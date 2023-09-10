#Docs: https://discordpy.readthedocs.io/en/latest/intro.html
import discord
from discord.ext.commands import Bot
from todo import TodoCog, TodoList, Todo
from beeminder import Beeminder
from bot_token import BOT_TOKEN

rusabot = Bot(command_prefix = ".", intents=discord.Intents.all())

@rusabot.event
async def on_ready():
    print("rusabot online")

@rusabot.event
async def setup_hook():
    todolist_names_file = 'data/todolist_names.pkl'
    await rusabot.add_cog(TodoCog(rusabot, todolist_names_file))

    await rusabot.add_cog(Beeminder())

rusabot.run(BOT_TOKEN)