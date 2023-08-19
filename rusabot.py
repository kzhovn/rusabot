#Docs: https://discordpy.readthedocs.io/en/latest/intro.html
from bot_token import BOT_TOKEN

import os
import pickle
import discord
import random
from discord.ext.commands import Bot

NO_TODOS = "🎉 No todos 🎉"


async def get_message(message_id: int, channel_id: int):
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

    async def print_list_to_channel(self, context) -> None:
        if len(self.todos) == 0:
            await context.message.channel.send(NO_TODOS)
            return

        new_list = await context.message.channel.send(self.pretty_print())
        self.last_list_id = new_list.id
        self.last_list_channel = context.message.channel.id


    def __repr__(self) -> str:
        return f'Todos for list {self.name}: {self.todos}\n'


rusabot = Bot(command_prefix = ".", intents=discord.Intents.all())
user_todolists = {}
todolist_names_file = 'data/todolist_names.pkl'

@rusabot.event
async def on_ready():
    if os.path.isfile(todolist_names_file):
        todolist_names = pickle.load(open(todolist_names_file, 'rb'))
    else: # if we're new, just use the default list
        todolist_names = ['todo']
        pickle.dump(todolist_names, open(todolist_names_file, 'wb'))

    for name in todolist_names:
        if os.path.isfile(f'data/{name}.pkl'):
            user_todolists[name] = (pickle.load(open(f'data/{name}.pkl', 'rb')))
        else:
            print(f'List {name} not found, creating.')
            user_todolists[name] = (TodoList(name))

    print(user_todolists)

    print("rusabot online")

#https://stackoverflow.com/questions/49331096/why-does-on-message-stop-commands-from-working
@rusabot.event
async def on_message(message):
    if is_todo(message):
        user_todolists['todo'].add_todo(message)

    await rusabot.process_commands(message)

@rusabot.event #check every new reaction (on_reaction_add only looks into cache)
async def on_raw_reaction_add(payload):
    message = await get_message(payload.message_id, payload.channel_id)
    if (payload.emoji.name == "✅" or payload.emoji.name == "❌") and is_todo(message):
        await user_todolists['todo'].remove_todo(message)


# print current todos in channel
@rusabot.command()
async def list(context, *args):
    if len(args) == 0:
        await user_todolists['todo'].print_list_to_channel(context)
    else:
        pass # TODO: print list with that name

# give a random todo item
@rusabot.command()
async def rand(context):
    if len(user_todolists['todo'].todos) != 0:
        random_todo = random.choice(__builtins__.list(user_todolists['todo'].todos.values()))
        await context.message.channel.send(random_todo.compose_line())
    else:
        await context.message.channel.send(NO_TODOS)

@rusabot.command()
async def newlist(context, *args):
    if len(args) == 0:
        await context.message.channel.send("Must specify a name for the list, e.g. `.newlist work`.")
        return
    if len(args) > 1:
        await context.message.channel.send("List name must be one word, no spaces permitted, e.g. `.newlist work`.")
        return

    todolist_names = pickle.load(open(todolist_names_file, 'rb'))
    name = args[0]

    if name in todolist_names:
        await context.message.channel.send("List name already in use, try another one.")
    else:
        todolist_names.append(name)
        pickle.dump(todolist_names, open(todolist_names_file, 'wb'))

        new_list = TodoList(name)
        user_todolists[name] = new_list
        new_list.pkl()
        print(f'Created list {name}')

@rusabot.command()
async def removelist(context, *args):
    if len(args) == 0:
        await context.message.channel.send("Must specify at least one name for the list(s) to be removed, e.g. `.removelist work`.")
        return

    todolist_names = pickle.load(open(todolist_names_file, 'rb'))
    for name in args:
        if name == 'todo':
            await context.message.channel.send("Cannot delete default list 'todo'.")
        elif name in todolist_names:
            todolist_names.remove(name)
            print(f'Removing list {name}')
        else:
            await context.message.channel.send(f"List {name} doesn't exist.")

    pickle.dump(todolist_names, open(todolist_names_file, 'wb'))


def is_todo(message) -> bool:
    if message.content.startswith("--") and not message.author.bot:
        return True
    else:
        return False

rusabot.run(BOT_TOKEN)
