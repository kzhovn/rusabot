#Docs: https://discordpy.readthedocs.io/en/latest/intro.html
import discord
from discord.ext.commands import Bot
from discord.ext.commands import errors
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

@rusabot.event
async def on_command_error(ctx, error):
    if isinstance(error, errors.MissingRequiredArgument):
        await ctx.send("Missing an argument.")
    elif isinstance(error, errors.TooManyArguments):
        await ctx.send("Too many arguments")       
    elif isinstance(error, errors.CommandNotFound):
        return
    else:
        print(error)
    
    await ctx.message.add_reaction("❌")
    await ctx.send_help(ctx.command)
rusabot.run(BOT_TOKEN)