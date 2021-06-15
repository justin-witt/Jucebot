import socket, logging, os

class ChatBot:
    def __init__(self, username, target, oauth, color="CadetBlue"):
        self.__host='irc.chat.twitch.tv'
        self.__port=6667
        self.__username=username # Bot username
        self.__target_channel=target # Channel to join
        self.__token=oauth # Get Oauth for Twitch
        self.__color = color
        self.__encode="utf-8"
        self.__twitch_socket=self.__connect()
        self.__commands={}
        self.__send_message("/me Connected.") # Notify chat that the bot has connected
        self.__send_message(f"/color {self.__color}") # Set bot color
    
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
    def new_command(self, activation):
        def outter_wrapper(func):
            self.__commands[activation]=func
            def inner_wrapper(*args, **kwargs):
                func(*args, *kwargs)
            return inner_wrapper
        return outter_wrapper

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
        while 1:
            data=self.__recv_messages()
            for i in data:
                logging.info(f"{i.user}:{i.message}")
                try:
                    self.__send_message(self.__commands[i.message.split(" ")[0]](i))
                except Exception:
                    pass                
    
    class __Message:
        def __init__(self, user, message):
            self.user=user
            self.message=message
