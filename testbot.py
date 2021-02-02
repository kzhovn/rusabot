#Tutorials:
#https://realpython.com/how-to-make-a-discord-bot-python/
#https://codeburst.io/discord-py-the-quickstart-guide-2587abc136ab

#Docs:
#https://discordpy.readthedocs.io/en/latest/intro.html

#Background:
#https://stackoverflow.com/questions/50757497/simplest-async-await-example-possible-in-python


#import os

import discord
from discord.ext.commands import Bot
#from dotenv import load_dotenv

#load_dotenv()
#TOKEN = os.getenv('DISCORD_TOKEN')
TOKEN = "Nzg2NDI0NDcyOTc4MTk0NDM0.X9GM3Q.iZX0kWksHQPOWBYBtc8KMzy3OFo"
testbot = Bot(command_prefix = "/")

#when starting bot
@testbot.event
async def on_ready():
    print("Testbot online")
    await testbot.change_presence(activity = discord.Game("Testing")) #set status

#https://stackoverflow.com/questions/49331096/why-does-on-message-stop-commands-from-working
@testbot.event
async def on_message(message): #check every message
    if message.content == "testbot, ping":
        await message.channel.send(message.author.name + ", pong") #respond to message

    if message.author.bot: #check if bot
        await message.add_reaction("🤖") #add reaction

    await testbot.process_commands(message)

@testbot.event #check every new reaction
async def on_reaction_add(reaction, user):
    if reaction.emoji == "🌳":
        await reaction.message.channel.send("🌳🌳🌳")
    elif reaction.emoji == "🔁":

    
#on /ping (or other prefix)
@testbot.command()
async def ping(context):
    await context.send("pong!")
    await context.message.add_reaction("🏓")

user_list = []
@testbot.command()
async def add_user(context):
    user_list.append(context.message.author.id)
    print(user_list)
testbot.run(TOKEN)
