from discord.ext import commands
from pyminder.pyminder import Pyminder
from bot_token import BEEMINDER_TOKEN, BEEMINDER_USER

class Beeminder(commands.Cog):

    @commands.command()
    async def beemind(self, context, *args):
        if len(args) == 0:
            await context.message.channel.send("Must specify a goal name, e.g. `.beemind teeth`.")
            return
        
        goal = str(args[0])
        val = 1
        comment = ""

        if len(args) >= 2:
            val = float(args[1]) # raise the exceptions sanely

        if len(args) >= 3:
            comment = str(args[2])

        if len(args) > 3:
            await context.message.channel.send('Too many arguments. You can specify goal name, value, and a comment, e.g. `.beemind teeth 1.5 "flossed today"`')
            return
        
        if create_beeminder_datapoint(goal, val, comment):
            await context.message.add_reaction("🐝")
        else:
            await context.message.add_reaction("❌")


# Sends a beeminder datapoint to `goal`; returns true on success and false on failure
def create_beeminder_datapoint(goal: str, val: float = 1, comment: str = "") -> bool:
    pyminder = Pyminder(user = BEEMINDER_USER, token = BEEMINDER_TOKEN)
    comment = comment + " via rusabot"
    try:
        pyminder._beeminder.create_datapoint(goal, val, comment = comment)
        print(f"Added {val} to beeminder goal '{goal}'.") 
        return True     
    except Exception as e:
        print(e)
        return False

