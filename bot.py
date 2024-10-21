from os import getenv
import discord
from discord.ext import commands as cmd
from flask import Flask, request
from threading import Thread

#* Setup Discord Bot
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
bot = cmd.Bot(command_prefix='!', intents=intents)

#* Flask app to handle communication between web dyno and worker
app = Flask(__name__)

#* Environment variables
TOKEN = getenv('DISCORD_BOT_TOKEN')
PUSH_CHANNEL = int(getenv("PUSH_CHANNEL"))  # Ensure this is an int (Discord channel ID)

# Ensure bot is ready before processing any tasks
@bot.event
async def on_ready():
    print(f'Bot has connected to Discord as {bot.user}')

# Endpoint to receive POST requests from the web dyno
@app.route('/send_commit', methods=['POST'])
def send_commit():
    data = request.json
    repo_name = data.get('repo_name')
    username = data.get('username')
    commit_msg = data.get('commit_msg')

    # Use run_coroutine_threadsafe to run async code within Flask
    channel = bot.get_channel(PUSH_CHANNEL)
    if channel:
        embed = discord.Embed(
            title=f"New Commit in {repo_name}",
            color=0x00ff00
        )
        embed.add_field(name="User", value=username, inline=True)
        embed.add_field(name="Message", value=commit_msg, inline=False)
        # Run async coroutine to send the message
        bot.loop.create_task(channel.send(embed=embed))
        return "Message sent", 200
    else:
        return "Channel not found", 404

# Run Flask server
def run_flask():
    app.run(host="0.0.0.0", port=5001)

if __name__ == "__main__":
    # Run Flask in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Run Discord bot
    bot.run(TOKEN)