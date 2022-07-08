__license__ = "https://unlicense.org/"
__version__ = "1.2.0"

import socket, logging, re
from time import sleep
from threading import Thread

class ChatBot:
    def __init__(self, username, target, oauth, color="CadetBlue", banphrases:list=None):
        self.__host='irc.chat.twitch.tv'
        self.__port=6667
        self.__username=username # Bot username
        self.__target_channel=target # Channel to join
        self.__token=oauth # Get Oauth for Twitch
        self.__color = color
        self.__encode="utf-8"
        self.__commands={}
        self.__timers=[]
        self.__banphrases=[] if banphrases == None else banphrases
        self.__twitch_socket=self.__connect()
        self.__send_message(f"/color {self.__color}") # Set bot color
        self.__send_message("/me Connected.") # Notify chat that the bot has connected
    
    def __connect(self):
        logging.info("opening socket...")
        t_socket=socket.socket()
        logging.info("connecting...")
        t_socket.connect((self.__host,self.__port))
        logging.info("sending token...")
        t_socket.sendall(f"PASS {self.__token}\r\n".encode(self.__encode))
        logging.info("sending username...")
        t_socket.sendall(f"NICK {self.__username}\r\n".encode(self.__encode))
        logging.info("joining room...")
        t_socket.sendall(f"JOIN #{self.__target_channel}\r\n".encode(self.__encode))
        joining=True
        while joining:
            buffer=t_socket.recv(1024).decode()
            data=buffer.splitlines()
            for i in data:
                logging.info(i)
                if "End of /NAMES list" in i:
                    joining=False
        logging.info(f"connected to {self.__target_channel}'s chat room...")
        return t_socket

    #Add new commands
    def command(self, activation):
        def outter_wrapper(func):
            self.__commands[activation]=func
            def inner_wrapper(*args, **kwargs):
                func(*args, **kwargs)
            return inner_wrapper
        return outter_wrapper

    #Add new timer
    def timer(self, mins=15):
        def outter_wrapper(func):
            self.__timers.append(Thread(target=self.__create_timer, args=(func, mins)))
            def inner_wrapper():
                func()
            return inner_wrapper
        return outter_wrapper

    def __create_timer(self, func, mins):
        while True:
            sleep(mins*60)
            self.__send_message(func())

    def __send_message(self, msg):
        self.__twitch_socket.sendall(f"PRIVMSG #{self.__target_channel} :{msg}\r\n".encode(self.__encode))
        logging.info(f"outgoing message:{msg}")

    # Respond to ping request from twitch.
    def __ping_pong(self, msg):
        if 'PING :tmi.twitch.tv' in msg:
            logging.info("sending pong...")
            self.__twitch_socket.sendall(f"{msg.replace('PING', 'PONG')}\n".encode(self.__encode))
            return True
        return False

    # Generator for messages.
    def __recv_messages(self):
        buffer=self.__twitch_socket.recv(1024).decode()
        data=buffer.splitlines()
        for message in data:
            if self.__ping_pong(message)==False:
                message=message[1:].split("!",1)
                message[1]=message[1].split(":",1)[1]
                yield self.__Message(message[0], message[1])

    # Starts the bot
    def run(self):
        for thread in self.__timers:
            thread.start()
        while 1:
            data=self.__recv_messages()
            for i in data:
                logging.info(f"{i.user}:{i.message}")
                self.__chat_moderation(i)
                try:
                    self.__send_message(self.__commands[i.message.split(" ")[0]](i))
                except Exception:
                    pass
    
    def __chat_moderation(self, msg):
        if any(re.match(i, msg.message) != None for i in self.__banphrases):
            self.__send_message(f"/ban {msg.user}")            

    class __Message:
        def __init__(self, user, message):
            self.user=user
            self.message=message
    