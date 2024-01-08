import logging
import re
import asyncio

class Bot:
    """
    A Twitch chat bot.

    Attributes:
    - __HOST (str): Twitch IRC host.
    - __PORT (int): Twitch IRC port.
    - __ENCODE (str): Encoding format.

    Methods:
    - __init__: Initialize the Bot instance.
    - run: Run the bot.
    - command: Decorator to add chat command handlers.
    - timer: Decorator to add timers for periodic tasks.
    """

    __HOST = 'irc.chat.twitch.tv'
    __PORT = 6667
    __ENCODE = "utf-8"

    class Message:
        """
        Represents a message in the Twitch chat.

        Attributes:
        - user (str): Username of the sender.
        - message (str): Content of the message.
        """

        def __init__(self, user: str, message: str) -> None:
            self.user = user
            self.message = message

    def __init__(self, username: str, target: str, oauth: str, color: str = "CadetBlue", banphrases: list = None) -> None:
        """
        Initialize the Bot instance.

        Args:
        - username (str): Twitch username.
        - target (str): Twitch channel name.
        - oauth (str): OAuth token for authentication.
        - color (str, optional): Color for chat messages.
        - banphrases (list, optional): List of phrases to trigger bans.
        """
        self.__USERNAME = username
        self.__TARGET = target
        self.__TOKEN = oauth
        self.__color = color
        self.__banphrases = [] if not banphrases else banphrases
        self.__commands = {}
        self.__timers = []

    async def __connect(self) -> None:
        """
        Connect to the Twitch IRC server.
        """
        logging.info("[CONNECTING] opening connection")
        self.__reader, self.__writer = await asyncio.open_connection(self.__HOST, self.__PORT)
        logging.info("[CONNECTING] sending token")
        self.__writer.write(f"PASS {self.__TOKEN}\r\n".encode(self.__ENCODE))
        await self.__writer.drain()
        logging.info("[CONNECTING] sending username")
        self.__writer.write(f"NICK {self.__USERNAME}\r\n".encode(self.__ENCODE))
        await self.__writer.drain()
        logging.info("[CONNECTING] joining room")
        self.__writer.write(f"JOIN #{self.__TARGET}\r\n".encode(self.__ENCODE))
        await self.__writer.drain()

        join = True

        while join:
            buff = await self.__reader.read(1024)
            buff = buff.decode()
            data = buff.splitlines()
            for msg in data:
                logging.info(f"[CONNECTING] {msg}")
                if "End of /NAMES list" in msg:
                    join = False

    async def __sendMessage(self, msg: str) -> None:
        """
        Send a message to the Twitch chat.

        Args:
        - msg (str): Message to send.
        """
        self.__writer.write(f"PRIVMSG #{self.__TARGET} :{msg}\r\n".encode(self.__ENCODE))
        await self.__writer.drain()
        logging.info(f"[CHAT] {self.__USERNAME}:{msg}")

    async def __pingPong(self, msg: str) -> bool:
        """
        Respond to server PING with PONG.

        Args:
        - msg (str): Received message.

        Returns:
        - bool: True if PING message was handled.
        """
        if "PING :tmi.twitch.tv" in msg:
            self.__writer.write(f"{msg.replace('PING','PONG')}\n".encode(self.__ENCODE))
            await self.__writer.drain()
            logging.info("[CONNECTION] ping pong")
            return True
        return False

    async def __recvMessages(self) -> Message:
        """
        Receive messages from the Twitch chat.

        Yields:
        - Message: A message received from chat.
        """
        buff = await self.__reader.read(2048)
        buff = buff.decode()
        buff = buff.splitlines()
        for msg in buff:
            pingPong = await self.__pingPong(msg)
            if not pingPong:
                msg = msg[1:].split("!", 1)
                msg[1] = msg[1].split(":", 1)[1]
                yield self.Message(msg[0], msg[1])

    async def __mod(self, msg: Message) -> None:
        """
        Moderate chat messages and perform actions if triggered.

        Args:
        - msg (Message): Received message object.
        """
        if any(re.search(i, msg.message) is not None for i in self.__banphrases):
            asyncio.create_task(self.__sendMessage(f"/ban {msg.user}"))
            logging.info(f"[BAN TRIGGER] USER: {msg.user} MSG: {msg.message}")

    async def __createTimer(self, timer: list):
        """
        Create a timer for periodic tasks.

        Args:
        - timer (list): Timer configuration.
        """
        while True:
            await asyncio.sleep(timer[1] * 60)
            msg = await timer[0]()
            asyncio.create_task(self.__sendMessage(msg))

    async def __main(self):
        """
        Main loop for the bot operations.
        """
        try:
            await self.__connect()
            asyncio.create_task(self.__sendMessage(f"/color {self.__color}"))
            asyncio.create_task(self.__sendMessage("/me Connected."))

            for timer in self.__timers:
                asyncio.create_task(self.__createTimer(timer))

            async for msg in self.__recvMessages():
                logging.info(f"[CHAT] {msg.user}:{msg.message}")
                asyncio.create_task(self.__mod(msg))

                try:
                    outgoing = await self.__commands[msg.message.split(" ")[0]](msg)
                    asyncio.create_task(self.__sendMessage(outgoing))
                except KeyError:
                    pass

        except ConnectionResetError:
            logging.warning("[CONNECTION] connection reset attempt to reconnect")
            await self.__connect()
            logging.info("[CONNECTION] socket reset")

    async def run_bot(self):
        """
        Run the Twitch bot asynchronously.
        """
        async with asyncio.open_connection(self.__HOST, self.__PORT) as (reader, writer):
            self.__reader = reader
            self.__writer = writer
            await self.__main()

    def run(self):
        """
        Run the Twitch bot synchronously.
        """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.run_bot())

    def command(self, activation: str):
        """
        Decorator to add chat command handlers.

        Args:
        - activation (str): Command activation phrase.

        Returns:
        - function: Decorated function.
        """
        def outer(func):
            self.__commands[activation] = func

            async def inner(*args, **kwargs):
                return await func(*args, **kwargs)

            return inner

        return outer

    def timer(self, timer: int = 15):
        """
        Decorator to add timers for periodic tasks.

        Args:
        - timer (int, optional): Timer duration in minutes.

        Returns:
        - function: Decorated function.
        """
        def outer(func):
            self.__timers.append([func, timer])

            async def inner(*args, **kwargs):
                return await func(*args, **kwargs)

            return inner

        return outer
