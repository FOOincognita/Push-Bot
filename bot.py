import os
import discord
from discord.ext import commands
import asyncio

# Set up Discord bot
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True  # Required to send messages
intents.message_content = True  # If message content access is needed
bot = commands.Bot(command_prefix='!', intents=intents)

# Environment variables
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
PUSH_CHANNEL_ID = int(os.getenv("PUSH_CHANNEL"))  # Discord channel ID

# Global variable to check if bot is ready
bot_ready = asyncio.Event()

@bot.event
async def on_ready():
    print(f'Bot has connected to Discord as {bot.user}')
    bot_ready.set()

# Async function to send commit messages (triggered by the Quart webhook)
async def send_commit_message(repo_name: str, username: str, commit_msg: str):
    await bot_ready.wait()  # Ensure bot is ready
    print(f"Attempting to send message to channel ID: {PUSH_CHANNEL_ID}")  # Debugging log
    channel = bot.get_channel(PUSH_CHANNEL_ID)
    
    if channel:
        print("Channel found, sending message...")  # Debugging log
        embed = discord.Embed(
            title=f"New Commit in {repo_name}",
            color=0x00ff00
        )
        embed.add_field(name="User", value=username, inline=True)
        embed.add_field(name="Message", value=commit_msg, inline=False)
        await channel.send(embed=embed)
    else:
        print("[ERROR]: Channel not found")  # Debugging log

if __name__ == "__main__":
    bot.run(TOKEN)