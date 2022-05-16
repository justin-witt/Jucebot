# Jucebot
Just a simple chat bot for twitch.
## Contact
Github: https://github.com/justin-wittenmeier/Jucebot/discussions/categories/general
## Getting Started
Create a new file in the same dir as jucebot called "main.py" (or whatever you like) and replace the following code with the required information.
``` py
import jucebot #import juecbot and call ChatBot
# Pass in your username, the target channel, your oauth token. Color is optional. (cadet blue by default)
bot = jucebot.ChatBot(username="USERNAME",target="CHANNEL TO JOIN",oauth="TWITCH OAUTH") 

@bot.new_command("!helloworld") # Add the command and pass in an "acivation" phrase.
def helloworld(msg): # Include a variable to access the message object data. (msg.user; msg.message)
    # Return a string with the message and @ of the user you would like to target.
    return f"@{msg.user} hello!"

#Run the bot
bot.run()
```
*run*
