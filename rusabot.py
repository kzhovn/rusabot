#Docs: https://discordpy.readthedocs.io/en/latest/intro.html
from bot_token import BOT_TOKEN

import os
import pickle
import discord
import random
from discord.ext.commands import Bot


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
    def __init__(self, name : str = None):
        self.todos = {} # id int -> Todo
        self.last_list_id = None
        self.last_list_channel = None

        if name is None:
            self.todo_file = 'todo.pkl'
        else:
            self.todo_file = name + ".pkl"


    def add_todo(self, message: discord.Message):
        self.todos[message.id] = Todo(message)
        pickle.dump(self.todos, open(self.todo_file, 'wb'))
        print("Adding " + self.todos[message.id].text)

    async def remove_todo(self, message: discord.Message):
        todo = self.todos[message.id]
        if self.todos.pop(message.id, None):
            print("Removing " + todo.text)
            pickle.dump(self.todos, open(self.todo_file, 'wb'))

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

    def __repr__(self) -> str:
        return str(self.todos)

# class DailyTodoList(TodoList):
#     def __init__(self):
#         super().__init__("daily")

#     def add_todo(self, message : discord.Message):
#         self.todos[message.id] = DailyTodo(message)
#         pickle.dump(self.todos, open(self.todo_file, 'wb'))
#         print("Adding daily todo" + self.todos[message.id].text)


# class DailyTodo(Todo):
#     def __init__(self, message):
#         super().__init__(message)
#         self.complete = False
#         self.last_complete = None

#         self.text = message.content[10:].strip()



rusabot = Bot(command_prefix = ".", intents=discord.Intents.all())
user_todos = TodoList()
# user_dailies = DailyTodoList()
user_lists = [user_todos]


@rusabot.event
async def on_ready():
    # load todos
    for user_list in user_lists:
        if os.path.isfile(user_list.todo_file):
            user_list.todos = pickle.load(open(user_list.todo_file, 'rb'))

    print("rusabot online")
    await rusabot.change_presence(activity = discord.Game("Testing")) #set status


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




# print current todos in channel
@rusabot.command()
async def list(context, *args):
    if len(args) == 0:
        await print_list_to_channel(context, user_todos)
    else:
        pass # TODO: print list with that name

# give a random todo item
@rusabot.command()
async def rand(context):
    random_todo = random.choice(__builtins__.list(user_todos.todos.values()))
    await context.message.channel.send(random_todo.compose_line())

# # display a daily list that refreshes complete status every day
# @rusabot.command()
# async def daily(context):
#     await print_list_to_channel(context, user_dailies)

# # add text after command to the daily list
# @rusabot.command()
# async def add_daily(context):
#     user_dailies.add_todo(context.message)

async def print_list_to_channel(context, user_list: TodoList) -> None:
    if len(user_list.todos) == 0:
        await context.message.channel.send("🎉 No todos 🎉")
        return

    new_list = await context.message.channel.send(user_list.pretty_print())
    user_list.last_list_id = new_list.id
    user_list.last_list_channel = context.message.channel.id

def is_todo(message) -> bool:
    if (message.content.startswith("--") or message.content.startswith(".add_daily")) and not message.author.bot:
        return True
    else:
        return False

rusabot.run(BOT_TOKEN)
