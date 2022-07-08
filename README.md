# Jucebot
Third-party bot for https://twitch.tv.
## Contact
Github: https://github.com/justin-witt/Jucebot/discussions/categories/general
## Getting Started
Create a new file in the same dir as jucebot called "main.py" (or whatever you like) and replace the following code with the required information.
``` py
import jucebot #import juecbot and call ChatBot

#THIS IS OPTIONAL: If you want the bot to moderate chat you can pass in a list of words/regex that will trigger the bot to BAN a user.
#Note: THIS DOES NOT TIMEOUT A USER BUT PERMANETLY BANS THEM
banphrase_list=["wordtoban","anotherwordtoban",r"some\Sregex\d$"]

# Pass in your username, the target channel, your oauth token. Color is optional. (cadet blue by default)
bot = jucebot.ChatBot(username="USERNAME",target="CHANNEL TO JOIN",oauth="TWITCH OAUTH", banphrases=banphrase_list) 

@bot.command("!helloworld") # Add the command and pass in an "acivation" phrase.
def helloworld(msg): # Include a variable to access the message object data. (msg.user; msg.message)
    # Return a string with the message and @ of the user you would like to target.
    return f"@{msg.user} hello!"

@bot.timer(30) # Create a timer and set how many mins(INTEGER) you want between the message to be sent
def github(): # Return the message that you want sent at the specified interval.
    return "Check out my github! https://github.com/justin-witt"

#Timers are set to 15 minutes by default if no time is passed in.
@bot.timer
def example():
    return "This timer will run every 15 minutes"

#Run the bot
bot.run()
```
## Stop the Bot
To stop the bot use `Ctrl+C`.
