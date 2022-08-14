#Docs:
#https://discordpy.readthedocs.io/en/latest/intro.html
from bot_token import BOT_TOKEN

#import os
import discord
from discord.ext.commands import Bot

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

#on /ping, respond
@testbot.command()
async def ping(context):
    await context.send("pong!")
    await context.message.add_reaction("🏓")

# add user id to list
user_list = []
@testbot.command()
async def add_user(context):
    user_list.append(context.message.author.id)
    print(user_list)

testbot.run(BOT_TOKEN)
