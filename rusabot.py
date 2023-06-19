#Docs: https://discordpy.readthedocs.io/en/latest/intro.html
from bot_token import BOT_TOKEN

import os
import pickle
import discord
from discord.ext.commands import Bot

todo_file = 'todo.pkl'

async def get_message(message_id, channel_id):
    return await rusabot.get_channel(channel_id).fetch_message(message_id)

class Todo:
    def __init__(self, message):
        self.text = message.content[2:].strip()
        self.message_id = message.id
        self.url = message.jump_url

    def __repr__(self) -> str:
        return f"<Message: {self.text}, ID: {self.message_id}>"

    def compose_line(self):
        return f"- {self.text} ({self.url})\n"


class TodoList:
    def __init__(self):
        self.todos = {} # id int -> Todo
        self.last_list_id = None
        self.last_list_channel = None

    def add_todo(self, message: discord.Message):
        self.todos[message.id] = Todo(message)
        pickle.dump(self.todos, open(todo_file, 'wb'))
        print("Adding " + self.todos[message.id].text)

    async def remove_todo(self, message: discord.Message):
        todo = self.todos[message.id]
        if user_todos.todos.pop(message.id, None):
            print("Removing " + todo.text)
            pickle.dump(self.todos, open(todo_file, 'wb'))

            if self.last_list_id:
                message = await get_message(self.last_list_id, self.last_list_channel)
                new_message_content = ""
                for line in message.content.splitlines(keepends = True):
                    print(line)
                    print(todo.compose_line())
                    if line.strip() == todo.compose_line().strip():
                        new_message_content += ("✅" + line[1:])
                    else:
                        new_message_content += (line)

                await message.edit(content=new_message_content)
        else:
            print(f"{message} was not a todo")

    def pretty_print(self) -> str:
        todo_str_list = ""
        for todo in self.todos.values():
            todo_str_list = todo_str_list + todo.compose_line()

        return todo_str_list

    def __repr__(self) -> str:
        return str(self.todos)

rusabot = Bot(command_prefix = ".", intents=discord.Intents.all())
user_todos = TodoList()

@rusabot.event
async def on_ready():
    print("rusabot online")
    await rusabot.change_presence(activity = discord.Game("Testing")) #set status
    if os.path.isfile(todo_file):
        user_todos.todos = pickle.load(open(todo_file, 'rb'))

#https://stackoverflow.com/questions/49331096/why-does-on-message-stop-commands-from-working
@rusabot.event
async def on_message(message):
    if is_todo(message):
        user_todos.add_todo(message)

    await rusabot.process_commands(message)

@rusabot.event #check every new reaction (on_reaction_add only looks into cache)
async def on_raw_reaction_add(payload):
    message = await get_message(payload.message_id, payload.channel_id)
    if (payload.emoji.name == "✅" or payload.emoji.name == "❌") and is_todo(message):
        await user_todos.remove_todo(message)

#on .list, print current todos in channel
@rusabot.command()
async def list(context):
    new_list = await context.message.channel.send(user_todos.pretty_print())
    user_todos.last_list_id = new_list.id
    user_todos.last_list_channel = context.message.channel.id


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
