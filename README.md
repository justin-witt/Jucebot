# Jucebot
Just a simple chat bot for twitch.
## Getting Started
```
import jucebot #import juecbot and call ChatBot
# Pass in your username, the target channel, your oauth token, and you can select color as well (cadet blue by default)
bot = jucebot.ChatBot(username="USERNAME",target="CHANNEL TO JOIN",oauth="TWITCH OAUTH") 

@bot.new_command("!helloworld") # Add the command and pass in an "acivation" phrase.
def roll(msg): # Include a variable to access the message object data. (msg.user; msg.message)
    # Return a string with the message and @ of the user you would like to target.
    return f"@{msg.user} hello!"

#Run the bot
bot.run()
```
