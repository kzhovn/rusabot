#Docs: https://discordpy.readthedocs.io/en/latest/intro.html
from bot_token import BOT_TOKEN

import os
import pickle
import discord
import random
from discord.ext.commands import Bot
import re
import parsedatetime
import time

NO_TODOS = "🎉 No todos 🎉"
DEFAULT_LIST = "todo"


async def get_message(message_id: int, channel_id: int):
    return await rusabot.get_channel(channel_id).fetch_message(message_id)

class Todo:
    def __init__(self, message: discord.Message):
        self.text: str = get_todo_text(message.content)
        self.url: str = message.jump_url
        self.display_date: time.struct_time = None

        # find all contents of square brackets
        metadata = []
        for string in re.findall('\[(.+?)\]', message.content):
            metadata += string.split(";")

        for item in metadata:
            item = item.strip()

            if item.startswith("start:"):
                datestr = item.removeprefix('start:')
                cal = parsedatetime.Calendar()
                parsed_date, is_date = cal.parse(datestr)
                if is_date == 1:
                    self.display_date = parsed_date


    def __repr__(self) -> str:
        return f"<Message: {self.text}, URL: {self.url}>"

    def compose_line(self):
        return f"- {self.text} ({self.url})\n"

    def update(self, message: discord.Message):
        self.text = get_todo_text(message.content)
        print("Updated " + self.text)
        #TODO: update date

    def current(self) -> bool:
        return not self.display_date or self.display_date < time.localtime()


class TodoList:
    def __init__(self, name: str = None):
        self.name: str = name
        self.todos: dict = {} # id int -> Todo
        self.last_list_id: int = None
        self.last_list_channel: int = None

        self.pkl()

    def get_file_name(self) -> str:
        return f'data/{self.name}.pkl'

    def add_todo(self, message: discord.Message):
        self.todos[message.id] = Todo(message)
        self.pkl()
        print("Adding " + self.todos[message.id].text)

    async def remove_todo(self, message: discord.Message):
        if not await self.remove_todo_by_id(message.id):
            print(f"{message} was not a todo")

    # Returns False if a todo with this id does not exist in the list and True if sucessfully removed
    async def remove_todo_by_id(self, id: int) -> bool:
        todo = self.todos[id]
        if not self.todos.pop(id, None):
            return False

        print("Removing " + todo.text)
        self.pkl()

        if self.last_list_id:
            last_list = await get_message(self.last_list_id, self.last_list_channel)
            new_message_content = ""
            for line in last_list.content.splitlines(keepends = True):
                if line.strip() == todo.compose_line().strip():
                    new_message_content += ("- ~~" + line[1:].strip() + "~~\n")
                else:
                    new_message_content += (line)

            await last_list.edit(content=new_message_content, suppress=True)

        return True

    def pretty_print(self) -> str:
        todo_str_list = ""
        for todo in self.todos.values():
            if todo.current():
                todo_str_list = todo_str_list + todo.compose_line()

        return todo_str_list

    def pkl(self):
        pickle.dump(self, open(self.get_file_name(), 'wb'))

    async def print_list_to_channel(self, context):
        if len(self.todos) == 0:
            await context.message.channel.send(NO_TODOS)
            return

        try:
            new_list = await context.message.channel.send(self.pretty_print())
        except:
            embedVar = discord.Embed(title = self.name, description=self.pretty_print())
            new_list = await context.message.channel.send(embed=embedVar)


        self.last_list_id = new_list.id
        self.last_list_channel = context.message.channel.id

    def update_todo(self, message: discord.Message):
        # TODO: update line in print?
        self.todos[message.id].update(message)
        self.pkl()

    def has_message(self, message: discord.Message) -> bool:
        return message.id in self.todos.keys()

    def __repr__(self) -> str:
        return f'Todos for list {self.name}: {self.todos}\n'


rusabot = Bot(command_prefix = ".", intents=discord.Intents.all())
user_todolists = {} # {name: TodoList}
todolist_names_file = 'data/todolist_names.pkl'

@rusabot.event
async def on_ready():
    if os.path.isfile(todolist_names_file):
        todolist_names = get_list_of_lists()
    else: # if we're new, just use the default list
        todolist_names = [DEFAULT_LIST]
        if not os.path.isdir('data'):
            os.mkdir('data')
        pickle.dump(todolist_names, open(todolist_names_file, 'wb'))

    for name in todolist_names:
        if os.path.isfile(f'data/{name}.pkl'):
            user_todolists[name] = (pickle.load(open(f'data/{name}.pkl', 'rb')))
        else:
            print(f'List {name} not found, creating.')
            user_todolists[name] = (TodoList(name))

    print("rusabot online")

#https://stackoverflow.com/questions/49331096/why-does-on-message-stop-commands-from-working
@rusabot.event
async def on_message(message: discord.Message):
    if is_todo(message):
        user_todolists[get_list_name(message)].add_todo(message)

    await rusabot.process_commands(message)

@rusabot.event
async def on_raw_message_edit(payload: discord.RawMessageUpdateEvent):
    after = await get_message(payload.message_id, payload.channel_id)
    if not is_todo(after):
        # TODO: clean up somehow
        return
    
    if user_todolists[get_list_name(after)].has_message(after):
        print("In list")
        user_todolists[get_list_name(after)].update_todo(after)
    else: # update list
        print("Changing message list")
        if payload.cached_message:
            before = payload.cached_message
            await user_todolists[get_list_name(before)].remove_todo(before)
        else: # handle case where old message isn't available
            for lst in user_todolists.values():
                if await lst.remove_todo_by_id(payload.message_id):
                    break

        user_todolists[get_list_name(after)].add_todo(after)


@rusabot.event #check every new reaction (on_reaction_add only looks into cache)
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    message = await get_message(payload.message_id, payload.channel_id)
    if (payload.emoji.name == "✅" or payload.emoji.name == "❌") and is_todo(message):
        await user_todolists[get_list_name(message)].remove_todo(message)

    if message.author == rusabot.user and payload.emoji.name == "❌":
        await message.delete()

# print current todos in channel
@rusabot.command()
async def list(context, *args): # yes this name is a crime but I do in fact want 'list' and don't know how to do it differently in the code
    if len(args) == 0:
        await user_todolists[DEFAULT_LIST].print_list_to_channel(context)
    elif args[0] == 'all':
        for todolist in user_todolists.values():
            await todolist.print_list_to_channel(context)
    else:
        await user_todolists[args[0]].print_list_to_channel(context)

# give a random todo item
@rusabot.command()
async def rand(context, *args):
    if len(args) == 0:
        list_name = DEFAULT_LIST
    else: #TODO: take multiple lists
        list_name = args[0]

    curr_list = user_todolists[list_name]

    if len(curr_list.todos) != 0 or not curr_list.pretty_print() == "": # yes this is a dumb way to check if we have any current todos, why do you ask?
        random_todo = random.choice(__builtins__.list(curr_list.todos.values()))
        while not random_todo.current():
            random_todo = random.choice(__builtins__.list(curr_list.todos.values()))

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

    todolist_names = get_list_of_lists()
    name = args[0]

    if name in todolist_names:
        await context.message.channel.send("List name already in use, try another one.")
    elif name == 'all':
        await context.message.channel.send("List name 'all' is reserved.")
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

    todolist_names = get_list_of_lists()
    for name in args:
        if name == DEFAULT_LIST:
            await context.message.channel.send(f"Cannot delete default list '{DEFAULT_LIST}'.")
        elif name in todolist_names:
            todolist_names.remove(name)
            print(f'Removing list {name}')
        else:
            await context.message.channel.send(f"List {name} doesn't exist.")

    pickle.dump(todolist_names, open(todolist_names_file, 'wb'))


def is_todo(message: discord.Message) -> bool:
    if message.content.startswith("--") and not message.author.bot:
        return True
    else:
        return False

def get_list_name(message: discord.Message) -> str:
    if not is_todo(message):
        raise Exception(f"{message.content} is not a todo.")

    colon_split_msg = message.content.split(':', 1)
    if len(colon_split_msg) == 1:
        return DEFAULT_LIST

    first_word = colon_split_msg[0][2:].strip()
    if first_word in get_list_of_lists():
        return first_word

    return DEFAULT_LIST # if does not exist, assume we are just writing a colon

# assumes format "-- list_name: todo text [metadata to remove]"
def get_todo_text(todo: str) -> str:
    todo = re.sub('(\[.+?\])', "", todo) # note: removes *all* content of square brackets, even non-accepted metadata formats
    return todo[2:].strip()

def get_list_of_lists():
    return pickle.load(open(todolist_names_file, 'rb'))



rusabot.run(BOT_TOKEN)
