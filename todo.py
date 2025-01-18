from discord.ext import commands
import discord
import pickle
import random
import os
import re
import time
import parsedatetime
from discord.ext.commands import Bot

import asyncio
import datetime
from typing import Optional


NO_TODOS = "🎉 No todos 🎉"
DEFAULT_LIST = "todo"

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
        self.todos: dict[int, Todo] = {} # id int -> Todo
        self.last_list_id: int = None
        self.last_list_channel: int = None

        self.pkl()

    def __repr__(self) -> str:
        return f'Todos for list {self.name}: {self.todos}\n'

    @property
    def file_name(self) -> str:
        return f"data/{self.name}.pkl"

    def add_todo(self, message: discord.Message):
        self.todos[message.id] = Todo(message)
        self.pkl()
        print("Adding " + self.todos[message.id].text)

    # don't like passing bot here but it doesn't pickle so I don't have a great solution
    async def remove_todo(self, bot: Bot, message: discord.Message, complete: bool = False):
        if not await self.remove_todo_by_id(bot, message.id):
            print(f"{message} was not a todo")
            return

    # Returns False if a todo with this id does not exist in the list and True if sucessfully removed
    async def remove_todo_by_id(self, bot: Bot, id: int) -> bool:
        todo = self.todos[id]
        if not self.todos.pop(id, None):
            return False

        print("Removing " + todo.text)
        self.pkl()

        if self.last_list_id:
            last_list = await self.get_last_list(bot)
            new_message_content = ""
            for line in last_list.content.splitlines(keepends = True):
                if line.strip() == todo.compose_line().strip():
                    new_message_content += ("- ~~" + line[1:].strip() + "~~\n")
                else:
                    new_message_content += (line)

            await last_list.edit(content=new_message_content, suppress=True)

        return True

    async def get_last_list(self, bot: Bot):
        return await bot.get_channel(self.last_list_channel).fetch_message(self.last_list_id)

    def pretty_print(self) -> str:
        todo_str_list = ""
        for todo in self.todos.values():
            if todo.current():
                new_line = todo.compose_line()

                for start in ["- daily:", "- d:"]: # for special lists, don't redundantly repeat list name
                    if new_line.startswith(start):
                        new_line = new_line.strip(" ").replace(start, "- ", 1) # remove first occurance

                todo_str_list = todo_str_list + new_line

        return todo_str_list

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

    def pkl(self):
        pickle.dump(self, open(self.file_name, 'wb'))

    def has_message(self, message: discord.Message) -> bool:
        return message.id in self.todos.keys()


class TodoCog(commands.Cog):
    def __init__(self, bot: Bot, todolist_names_file: str):
        self.bot: Bot = bot
        self.todolist_names_file: str = todolist_names_file
        self.user_todolists: dict[str, TodoList] = {}

        # Load normal lists or create if not found
        if os.path.isfile(todolist_names_file):
            todolist_names = self.get_todolist_names()
        else: # if we're new, just use the default list
            todolist_names = [DEFAULT_LIST]
            if not os.path.isdir('data'):
                os.mkdir('data')
            pickle.dump(todolist_names, open(todolist_names_file, 'wb'))

        for name in todolist_names:
            if os.path.isfile(f'data/{name}.pkl'):
                self.user_todolists[name] = pickle.load(open(f'data/{name}.pkl', 'rb'))
            else:
                print(f'List {name} not found, creating.')
                self.user_todolists[name] = TodoList(name)

        # Load daily list or create if not found
        if os.path.isfile('data/daily.pkl'):
            self.daily_list = pickle.load(open(f'data/daily.pkl', 'rb'))
        else:
            print(f'Daily list not found, creating.')
            self.daily_list = DailyTodoList()

        self.user_todolists["daily"] = self.daily_list
        self._daily_task = None


    async def get_message(self, message_id: int, channel_id: int):
        return await self.bot.get_channel(channel_id).fetch_message(message_id)

    def get_todolist_names(self) -> list[str]:
        return pickle.load(open(self.todolist_names_file, 'rb'))

    def get_list_name(self, message: discord.Message) -> str:
        if not is_todo(message):
            raise Exception(f"{message.content} is not a todo.")

        colon_split_msg = message.content.split(':', 1)
        if len(colon_split_msg) == 1:
            return DEFAULT_LIST

        first_word = colon_split_msg[0][2:].strip()
        if first_word == "daily" or first_word == "d":  # We don't manually init dailt
            return "daily"
        if first_word in self.get_todolist_names():
            return first_word

        return DEFAULT_LIST # if does not exist, assume we are just writing a colon

    async def cog_load(self):
        # Start the background task when the cog is loaded
        self._daily_task = self.bot.loop.create_task(self.schedule_daily_reset())

    async def cog_unload(self):
        # Cleanup the task when the cog is unloaded
        if self._daily_task:
            self._daily_task.cancel()

    async def schedule_daily_reset(self):
        await self.bot.wait_until_ready()
        while True:
            try:
                now = datetime.datetime.now()
                # Calculate time until next 4 AM
                if now.hour >= 4:
                    next_run = now + datetime.timedelta(days=1)
                else:
                    next_run = now
                next_run = next_run.replace(hour=4, minute=0, second=0, microsecond=0)

                # Sleep until next run time
                delay = (next_run - now).total_seconds()
                await asyncio.sleep(delay)

                # Reset daily tasks
                await self.daily_list.reset_daily_tasks()

                # Log successful reset
                print(f"Daily tasks reset at {datetime.datetime.now()}")

            except asyncio.CancelledError:
                # Handle proper cancellation
                raise
            except Exception as e:
                # Log the error but don't let the loop die
                print(f"Error in daily reset task: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if is_todo(message):
            self.user_todolists[self.get_list_name(message)].add_todo(message)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        after = await self.get_message(payload.message_id, payload.channel_id)
        if not is_todo(after):
            # TODO: clean up somehow
            return

        if self.user_todolists[self.get_list_name(after)].has_message(after):
            print("In list")
            self.user_todolists[self.get_list_name(after)].update_todo(after)
        else: # update list
            print("Changing message list")
            if payload.cached_message:
                before = payload.cached_message
                await self.user_todolists[self.get_list_name(before)].remove_todo(self.bot, before)
            else: # handle case where old message isn't available
                for lst in self.user_todolists.values():
                    if await lst.remove_todo_by_id(self.bot, payload.message_id):
                        break

            self.user_todolists[self.get_list_name(after)].add_todo(after)

    @commands.Cog.listener() #check every new reaction (on_reaction_add only looks into cache)
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        message = await self.get_message(payload.message_id, payload.channel_id)
        if (payload.emoji.name == "✅" or payload.emoji.name == "❌") and is_todo(message):
            if payload.emoji.name == "✅":
                complete = True
            elif payload.emoji.name == "❌":
                complete = False
            await self.user_todolists[self.get_list_name(message)].remove_todo(self.bot, message, complete)

        if message.author == self.bot.user and payload.emoji.name == "❌":
            await message.delete()

    @commands.command(name="list")
    async def list_todos(self, context, lst: str = DEFAULT_LIST): # yes this name is a crime but I do in fact want 'list' and don't know how to do it differently in the code
        """Prints current todos to channel"""
        if lst == 'all':
            for todolist in self.user_todolists.values():
                await todolist.print_list_to_channel(context)
        else:
            await self.user_todolists[lst].print_list_to_channel(context)

    @commands.command()
    async def rand(self, context, lst: str = DEFAULT_LIST):
        """ Prints a random todo item to channel"""
        list_name = lst #TODO: take multiple lists
        curr_list = self.user_todolists[list_name]

        if len(curr_list.todos) != 0 or not curr_list.pretty_print() == "": # yes this is a dumb way to check if we have any current todos, why do you ask?
            random_todo = random.choice(list(curr_list.todos.values()))
            while not random_todo.current():
                random_todo = random.choice(list(curr_list.todos.values()))

            await context.message.channel.send(random_todo.compose_line())
        else:
            await context.message.channel.send(NO_TODOS)

    @commands.command()
    async def newlist(self, context, name: str):
        """Creates a new todolist named name. """

        todolist_names = self.get_todolist_names()

        for name in ['all', 'daily', 'd']:
            await context.message.channel.send(f"List name '{name}' is reserved.")
            return

        if name in todolist_names:
            await context.message.channel.send("List name already in use, try another one.")
        else:
            todolist_names.append(name)
            pickle.dump(todolist_names, open(self.todolist_names_file, 'wb'))

            new_list = TodoList(name)
            self.user_todolists[name] = new_list
            new_list.pkl()
            print(f'Created list {name}')

    @commands.command()
    async def removelist(self, context, *lsts: str):
        """Deletes the list(s) passed to the command. WARNING: deletes data. """
        if len(lsts) == 0:
            await context.message.channel.send("Must specify at least one name for the list(s) to be removed, e.g. `.removelist work`.")
            return

        todolist_names = self.get_todolist_names()
        for name in lsts:
            if name == DEFAULT_LIST:
                await context.message.channel.send(f"Cannot delete default list '{DEFAULT_LIST}'.")
            elif name in todolist_names:
                os.remove(self.user_todolists[name].file_name)
                todolist_names.remove(name)
                print(f'Removing list {name}')
            else:
                await context.message.channel.send(f"List {name} doesn't exist.")

        pickle.dump(todolist_names, open(self.todolist_names_file, 'wb'))

    @commands.command()
    async def daily(self, context):
        """Shows the daily todo list. Add items with --daily: task [repeat:daily/monday,wednesday/friday]"""
        await self.daily_list.print_list_to_channel(context)


### Daily ###

class DailyTodo(Todo):
    def __init__(self, message: discord.Message):
        super().__init__(message)
        self.repeat_schedule: Optional[str] = None

        # Parse metadata for repeat schedule
        metadata = []
        for string in re.findall('\[(.+?)\]', message.content):
            metadata += string.split(";")

        for item in metadata:
            item = item.strip()
            if item.startswith("repeat:"):
                self.repeat_schedule = item.removeprefix('repeat:').strip()

    def should_repeat(self) -> bool:
        if not self.repeat_schedule:
            return False

        today = datetime.datetime.now().strftime("%A").lower()
        if self.repeat_schedule == "daily":
            return True
        elif "," in self.repeat_schedule:
            days = [day.strip().lower() for day in self.repeat_schedule.split(",")]
            return today in days
        else:
            return today == self.repeat_schedule.lower()

class DailyTodoList(TodoList):
    def __init__(self, name: str = "daily"):
        super().__init__(name)
        self.repeating_todos: dict[int, DailyTodo] = {}

    def add_todo(self, message: discord.Message):
        todo = DailyTodo(message)
        if todo.repeat_schedule:
            self.repeating_todos[message.id] = todo
        self.todos[message.id] = todo
        self.pkl()
        print(f"Adding {'repeating ' if todo.repeat_schedule else ''}{todo.text}")

    async def reset_daily_tasks(self):
        # Clear non-repeating todos
        self.todos = {k: v for k, v in self.todos.items() if k in self.repeating_todos}

        # Filter out repeating todos that shouldn't show today
        self.todos = {k: v for k, v in self.todos.items()
                     if k not in self.repeating_todos or self.repeating_todos[k].should_repeat()}

        self.pkl()


### Utils ###

def is_todo(message: discord.Message) -> bool:
    if message.content.startswith("--") and not message.author.bot:
        return True
    else:
        return False

def get_todo_text(todo: str) -> str:
    """ Returns clean todo text with dashes and metadata stripped.
    Assumes format '-- list_name: todo text [metadata to remove]' """
    todo = re.sub('(\[.+?\])', "", todo) # note: removes *all* content of square brackets, even non-accepted metadata formats
    return todo[2:].strip()

