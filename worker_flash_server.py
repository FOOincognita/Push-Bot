from os import getenv
from flask import Flask, request
import discord
from discord.ext import commands as cmd
import threading
import asyncio

#* Setup Discord Bot
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
bot = cmd.Bot(command_prefix='!', intents=intents)

#* Setup Flask
app = Flask(__name__)

#* Environment variables
TOKEN = getenv('DISCORD_BOT_TOKEN')
PUSH_CHANNEL = int(getenv("PUSH_CHANNEL"))  # Ensure this is an int (Discord channel ID)

@bot.event
async def on_ready():
    print(f'Bot has connected to Discord as {bot.user}')

# Endpoint for receiving commit data
@app.route('/send_commit', methods=['POST'])
def send_commit():
    data = request.json
    repo_name = data.get('repo_name')
    username = data.get('username')
    commit_msg = data.get('commit_msg')

    # Run the bot task to send the commit message
    asyncio.run(send_commit_message(repo_name, username, commit_msg))
    return "Message sent", 200

# Send commit message to the Discord channel
async def send_commit_message(repo_name, username, commit_msg):
    channel = bot.get_channel(PUSH_CHANNEL)
    if channel:
        embed = discord.Embed(
            title=f"New Commit in {repo_name}",
            color=0x00ff00
        )
        embed.add_field(name="User", value=username, inline=True)
        embed.add_field(name="Message", value=commit_msg, inline=False)
        await channel.send(embed=embed)
    else:
        print("[ERROR]: Channel not found")

# Run Flask server in a separate thread
def run_flask():
    port = int(getenv("PORT", 5001))  # Use the port Heroku assigns
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Run Flask in a thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Run the Discord bot
    bot.run(TOKEN)