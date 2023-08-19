#Docs: https://discordpy.readthedocs.io/en/latest/intro.html
from bot_token import BOT_TOKEN

import os
import pickle
import discord
import random
from discord.ext.commands import Bot

NO_TODOS = "🎉 No todos 🎉"


async def get_message(message_id, channel_id):
    return await rusabot.get_channel(channel_id).fetch_message(message_id)

class Todo:
    def __init__(self, message):
        self.text: str = message.content[2:].strip()
        self.message_id: int = message.id
        self.url: str = message.jump_url

    def __repr__(self) -> str:
        return f"<Message: {self.text}, ID: {self.message_id}>"

    def compose_line(self):
        return f"- {self.text} ({self.url})\n"


class TodoList:
    def __init__(self, name : str = None):
        self.name: str = name
        self.todos: dict = {} # id int -> Todo
        self.last_list_id: int = None
        self.last_list_channel: int = None


    def get_file_name(self) -> str:
        return f'data/{self.name}.pkl'

    def add_todo(self, message: discord.Message):
        self.todos[message.id] = Todo(message)
        self.pkl()
        print("Adding " + self.todos[message.id].text)

    async def remove_todo(self, message: discord.Message):
        todo = self.todos[message.id]
        if self.todos.pop(message.id, None):
            print("Removing " + todo.text)
            self.pkl()

            if self.last_list_id:
                message = await get_message(self.last_list_id, self.last_list_channel)
                new_message_content = ""
                for line in message.content.splitlines(keepends = True):
                    if line.strip() == todo.compose_line().strip():
                        new_message_content += ("- ~~" + line[1:].strip() + "~~\n")
                    else:
                        new_message_content += (line)

                await message.edit(content=new_message_content, suppress=True)
        else:
            print(f"{message} was not a todo")

    def pretty_print(self) -> str:
        todo_str_list = ""
        for todo in self.todos.values():
            todo_str_list = todo_str_list + todo.compose_line()

        return todo_str_list

    def pkl(self):
        pickle.dump(self, open(self.get_file_name(), 'wb'))

    # @classmethod # https://stackoverflow.com/a/63442503
    # def unpkl(cls, filename: str):
    #     return pickle.load(open(filename, 'rb'))

    def __repr__(self) -> str:
        return f'Todos: {self.todos}\nPrev list: {self.last_list_channel}, {self.last_list_id}'


rusabot = Bot(command_prefix = ".", intents=discord.Intents.all())
user_todolist_names = ['todo']
user_todolists = []

@rusabot.event
async def on_ready():
    for name in user_todolist_names:
        if os.path.isfile(f'data/{name}.pkl'):
            user_todolists.append(pickle.load(open(f'data/{name}.pkl', 'rb')))
        else:
            user_todolists.append(TodoList(name))

    print(user_todolists)

    print("rusabot online")

#https://stackoverflow.com/questions/49331096/why-does-on-message-stop-commands-from-working
@rusabot.event
async def on_message(message):
    if is_todo(message):
        user_todolists[0].add_todo(message)

    await rusabot.process_commands(message)

@rusabot.event #check every new reaction (on_reaction_add only looks into cache)
async def on_raw_reaction_add(payload):
    message = await get_message(payload.message_id, payload.channel_id)
    if (payload.emoji.name == "✅" or payload.emoji.name == "❌") and is_todo(message):
        await user_todolists[0].remove_todo(message)


# print current todos in channel
@rusabot.command()
async def list(context, *args):
    if len(args) == 0:
        await print_list_to_channel(context, user_todolists[0])
    else:
        pass # TODO: print list with that name

# give a random todo item
@rusabot.command()
async def rand(context):
    if len(user_todolists[0].todos) != 0:
        random_todo = random.choice(__builtins__.list(user_todolists[0].todos.values()))
        await context.message.channel.send(random_todo.compose_line())
    else:
        await context.message.channel.send(NO_TODOS)



async def print_list_to_channel(context, user_list: TodoList) -> None:
    if len(user_list.todos) == 0:
        await context.message.channel.send(NO_TODOS)
        return

    new_list = await context.message.channel.send(user_list.pretty_print())
    user_list.last_list_id = new_list.id
    user_list.last_list_channel = context.message.channel.id

def is_todo(message) -> bool:
    if message.content.startswith("--") and not message.author.bot:
        return True
    else:
        return False

rusabot.run(BOT_TOKEN)
