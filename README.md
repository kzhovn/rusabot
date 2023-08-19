# Discord todo bot

## Usage
To add a todo, send "--" and then the text of the todo, e.g. "-- Send email".

To remove a todo, react to the initial todo message, with ✅ or ❌. ❌ will also delete a bot message.

## Commands
* `.list [name]`: lists all todos from the given list with a link to the original message; if no name is given uses the default list
    * `.list all`: lists all todos from all lists
* `.rand [name]`: gives you a random todo from the given list; if no name is given uses the default list
* `.newlist [name]`: creates a new list with the given name. Names must be one word, no spaces, and 'todo' and 'all' are reserved.
* `.removelist [name]`: deletes the list will the given name. *Will* delete your data.

