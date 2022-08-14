__license__ = "https://unlicense.org/"
__version__ = "2.0.4"
__author__="https://github.com/justin-witt"

import logging, re, asyncio

class Bot:


    __HOST='irc.chat.twitch.tv'
    __PORT=6667
    __ENCODE="utf-8"
    __reader=None
    __writer=None


    class __Message:
        def __init__(self, user, message) -> None:
            self.user = user
            self.message = message


    def __init__(self, username:str, target:str, oauth:str, color:str="CadetBlue", banphrases:list=None) -> None:
        self.__USERNAME=username
        self.__TARGET=target
        self.__TOKEN=oauth
        self.__color=color
        self.__banphrases=[] if not banphrases else banphrases
        self.__commands={}
        self.__timers=[]
    

    async def __connect(self) -> None:
        """Connect to twitch and set reader and writer.
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


    async def __sendMessage(self, msg:str) -> None:
        """Send chat message

            Args:
                msg:str - Message to send in chat
        """

        self.__writer.write(f"PRIVMSG #{self.__TARGET} :{msg}\r\n".encode(self.__ENCODE))
        await self.__writer.drain()
        logging.info(f"[CHAT] {self.__USERNAME}:{msg}")


    async def __pingPong(self, msg:str) -> bool:
        """Respond to ping request from twitch

            Args:
                msg:str - Message to check for ping request
        """

        if "PING :tmi.twitch.tv" in msg:
            self.__writer.write(f"{msg.replace('PING','PONG')}\n".encode(self.__ENCODE))
            await self.__writer.drain()
            logging.info("[CONNECTION] ping pong")
            return True
        return False


    async def __recvMessages(self) -> __Message:
        """Recieve messages from twitch

            Return: yields __Message objects
        """
        
        buff = await self.__reader.read(2048)
        buff = buff.decode()
        buff = buff.splitlines()
        for msg in buff:
            pingPong = await self.__pingPong(msg)
            if not pingPong:
                msg = msg[1:].split("!",1)
                msg[1] = msg[1].split(":",1)[1]
                yield self.__Message(msg[0], msg[1])


    async def __mod(self, msg:__Message) -> None:
        """Check message against ban phrase

            Args:
                msg:__Message - Mesage to check against banphrases
        """        
        if any(re.search(i, msg.message) != None for i in self.__banphrases):
            asyncio.create_task(self.__sendMessage(f"/ban {msg.user}"))
            logging.info(f"[BAN TRIGGER] USER: {msg.user} MSG: {msg.message}")


    async def __createTimer(self, timer:list):
        """Create timer to send messages

            Args:
                timer:list - timer[0]:function function that returns message to send | timer[1]:int minutes between messages 
        """

        await asyncio.sleep(timer[1]*60)
        msg = await timer[0]()
        asyncio.create_task(self.__sendMessage(msg))


    async def __main(self):
        """Main loop function
        """

        await self.__connect()
        asyncio.create_task(self.__sendMessage(f"/color {self.__color}"))
        asyncio.create_task(self.__sendMessage("/me Connected."))
        
        for timer in self.__timers:
            asyncio.create_task(self.__createTimer(timer))
        
        while True:
            try:

                data = self.__recvMessages()

                async for msg in data:
                    logging.info(f"[CHAT] {msg.user}:{msg.message}")
                    asyncio.create_task(self.__mod(msg))

                    try:
                        outgoing = await self.__commands[msg.message.split(" ")[0]](msg)
                        asyncio.create_task(self.__sendMessage(outgoing))
                    except KeyError:
                        pass

            except ConnectionResetError:
                logging.warning("[CONNECTION] connection reset attemption to reconnect")
                await self.__connect()
                logging.info("[CONNECTION] socket reset")

    def run(self):
        """Starts the main loop
        """

        asyncio.run(self.__main())


    def command(self, activation:str):
        """Add command to bot

            Args:
                activation:str = phrase that will trigger message response
        """

        def outter(func):
            self.__commands[activation]=func
            async def inner(*args, **kwargs):
                func(*args,**kwargs)
            return inner
        return outter


    def timer(self, timer:int=15):
        """Add timer to bot

            Args:
                timer:int = minutes between sending message
        """

        def outter(func):
            self.__timers.append([func, timer])
            async def inner(*args,**kwargs):
                func(*args, **kwargs)
            return inner
        return outter
