#Docs: https://discordpy.readthedocs.io/en/latest/intro.html
from bot_token import BOT_TOKEN

import os
import pickle
import discord
from discord.ext.commands import Bot

todo_file = 'todo.pkl'
completed_todo_file = 'completed_todos.pkl'

class Todo:
    def __init__(self, message):
        self.text = message.content[2:].strip()
        self.id = message.id
        self.url = message.jump_url

    def __repr__(self) -> str:
        return f"<Message: {self.text}, ID: {self.id}>"

class TodoList:
    def __init__(self):
        self.todos = {} # id int -> Todo

    def add_todo(self, message: discord.Message):
        self.todos[message.id] = Todo(message)
        pickle.dump(self.todos, open(todo_file, 'wb'))
        print("Adding " + self.todos[message.id].text)

    def remove_todo(self, message: discord.Message):
        if user_todos.todos.pop(message.id, None):
            print("Removing " + message.content)
            pickle.dump(self.todos, open(todo_file, 'wb'))
            # completed_user_todos.add_todo(message)
            # pickle.dump(completed_user_todos.todos, open(completed_todo_file, 'wb'))
        else:
            print(f"{message} was not a todo")

    def pretty_print(self) -> str:
        todo_str_list = ""
        for todo in self.todos.values():
            todo_str_list = todo_str_list + f"- {todo.text} ({todo.url})\n"

        return todo_str_list

    def __repr__(self) -> str:
        return str(self.todos)

rusabot = Bot(command_prefix = ".", intents=discord.Intents.default())
user_todos = TodoList()
completed_user_todos = TodoList()

#when starting bot
@rusabot.event
async def on_ready():
    print("rusabot online")
    await rusabot.change_presence(activity = discord.Game("Testing")) #set status
    if os.path.isfile(todo_file):
        user_todos.todos = pickle.load(open(todo_file, 'rb'))
    if os.path.isfile(completed_todo_file):
        completed_user_todos.todos = pickle.load(open(completed_todo_file, 'rb'))


#https://stackoverflow.com/questions/49331096/why-does-on-message-stop-commands-from-working
@rusabot.event
async def on_message(message):
    if is_todo(message):
        user_todos.add_todo(message)

    await rusabot.process_commands(message)

@rusabot.event #check every new reaction (on_reaction_add only looks into cache)
async def on_raw_reaction_add(payload):
    message = await rusabot.get_channel(payload.channel_id).fetch_message(payload.message_id)
    if (payload.emoji.name == "✅" or payload.emoji.name == "❌") and is_todo(message):
        user_todos.remove_todo(message)

#on >todos, print current todos in channel
@rusabot.command()
async def list(context):
    await context.message.channel.send(user_todos.pretty_print())

def is_todo(message) -> bool:
    if message.content.startswith("--") and not message.author.bot:
        return True
    else:
        return False

# @rusabot.command()
# async def add_user(context):
#     user_list.append(context.message.author.id)
#     print(user_list)

rusabot.run(BOT_TOKEN)
