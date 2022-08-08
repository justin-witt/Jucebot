__license__ = "https://unlicense.org/"
__version__ = "2.0.1"
__author__="https://github.com/justin-witt"

import logging, re, asyncio

class ChatBot():
    def __init__(self, username, target, oauth, color="CadetBlue", banphrases:list=None) -> None:
        self.__HOST='irc.chat.twitch.tv'
        self.__PORT=6667
        self.__USERNAME=username
        self.__TARGET=target
        self.__TOKEN=oauth
        self.__ENCODE="utf-8"
        self.__color=color
        self.__commands={}
        self.__timers=[]
        self.__banphrases=[] if banphrases == None else banphrases
        self.__twitchSocket=None

    async def __connect(self):
        """
        initalize connection to twitch
        """
        logging.info("opening socket...")
        logging.info("connecting...")
        tSocket=await asyncio.open_connection(self.__HOST,self.__PORT)
        logging.info("sending token...")
        tSocket[1].write(f"PASS {self.__TOKEN}\r\n".encode(self.__ENCODE))
        logging.info("sending username...")
        tSocket[1].write(f"NICK {self.__USERNAME}\r\n".encode(self.__ENCODE))
        logging.info("joining room...")
        tSocket[1].write(f"JOIN #{self.__TARGET}\r\n".encode(self.__ENCODE))
        joining=True
        while joining:
            buffer=await tSocket[0].read(1024)
            buffer=buffer.decode()
            data=buffer.splitlines()
            for i in data:
                logging.info(i)
                if "End of /NAMES list" in i:
                    joining=False
        logging.info(f"connected to {self.__TARGET}'s chat room...")
        return tSocket

    async def __sendMessage(self,msg):
        """
        Send twitch message
        """
        self.__twitchSocket[1].write(f"PRIVMSG #{self.__TARGET} :{msg}\r\n".encode(self.__ENCODE))
        logging.info(f"outgoing message:{msg}")

    async def __pingPong(self,msg):
        if 'PING :tmi.twitch.tv' in msg:
            logging.info("sending pong...")
            self.__twitchSocket[1].write(f"{msg.replace('PING', 'PONG')}\n".encode(self.__ENCODE))
            return True
        return False

    async def __recvMessages(self):
        buffer = await self.__twitchSocket[0].read(1024)
        buffer=buffer.decode()
        data=buffer.splitlines()
        for message in data:
            pingPong=await asyncio.create_task(self.__pingPong(message))
            if pingPong==False:
                message=message[1:].split("!",1)
                message[1]=message[1].split(":",1)[1]
                yield self.__Message(message[0], message[1])

    async def __chatModeration(self,msg):
        if any(re.match(i, msg.message) != None for i in self.__banphrases):
            asyncio.create_task(self.__sendMessage(f"/ban {msg.user}"))

    async def __createTimer(self, timer):
        """
        create timer loop
        """
        while True:
            await asyncio.sleep(timer[1]*60)
            asyncio.create_task(self.__sendMessage(await asyncio.create_task(timer[0]())))

    async def __main(self):
        """
        main loop for bot
        """
        self.__twitchSocket= await self.__connect()
        asyncio.create_task(self.__sendMessage(f"/color {self.__color}"))
        asyncio.create_task(self.__sendMessage("/me Connected."))
        for timer in self.__timers:
            asyncio.create_task(self.__createTimer(timer))
        while True:
            try:
                data=self.__recvMessages()
                async for i in data:
                    logging.info(f"{i.user}:{i.message}")
                    asyncio.create_task(self.__chatModeration(i))
                    try:
                        asyncio.create_task(self.__sendMessage(await asyncio.create_task(self.__commands[i.message.split(" ")[0]](i))))
                    except KeyError:
                        pass
            except ConnectionResetError:
                logging.warning("connection reset attemption to reconnect...")
                self.__twitchSocket= await self.__connect()
                logging.info("socket reset...")

    class __Message:
        def __init__(self, user, message) -> None:
            self.user=user
            self.message=message

    def run(self):
        """
        starts main loop for chatbot
        """
        asyncio.run(self.__main())

    def command(self,activation):
        """
        add command with activation for use
        """
        def outter(func):
            self.__commands[activation]=func
            async def inner(*args, **kwargs):
                func(*args,**kwargs)
            return inner
        return outter

    def timer(self,timer=15):
        """
        add message to be sent after X mins
        """
        def outter(func):
            self.__timers.append([func, timer])
            async def inner(*args,**kwargs):
                func(*args, **kwargs)
            return inner
        return outter
