from os import getenv
import discord
from discord.ext import commands as cmd
import asyncio


#* Setup
intents = discord.Intents.default()
intents.guilds = True   # Allow the bot to access guild (server) data
intents.messages = True  # Allow the bot to send messages
bot = cmd.Bot(command_prefix='!', intents=intents)

#* Environment variables
TOKEN         = getenv('DISCORD_BOT_TOKEN')
PUSH_CHANNEL  = int(getenv("PUSH_CHANNEL"))  # Ensure this is an int (Discord channel ID)


# Ensure bot is ready before processing any tasks
@bot.event
async def on_ready():
    print(f'Bot has connected to Discord as {bot.user}')


# Async function to send the message to the channel (worker will listen to Flask payload)
async def send_commit_message(repo_name: str, username: str, commit_msg: str):
    channel = bot.get_channel(PUSH_CHANNEL)
    if channel:
        embed = discord.Embed(
            title = f"New Commit in {repo_name}",
            color = 0x00ff00
        )
        embed.add_field(name="User", value=username, inline=True)
        embed.add_field(name="Message", value=commit_msg, inline=False)
        await channel.send(embed=embed)
    else:
        print("[ERROR]: Channel not found")


if __name__ == "__main__":
    bot.run(TOKEN)