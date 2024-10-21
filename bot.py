from os import getenv
import discord
from discord.ext import commands as cmd
from flask import Flask, request, abort
from threading import Thread
from asyncio import run_coroutine_threadsafe as coroutine
import hmac
import hashlib
from sys import __stderr__
import os


#* Setup
intents = discord.Intents.default()
intents.guilds = True   # Allow the bot to access guild (server) data
intents.messages = True  # Allow the bot to send messages
bot = cmd.Bot(command_prefix='!', intents=intents)

app = Flask(__name__)

#* Environment variables
TOKEN         = getenv('DISCORD_BOT_TOKEN')
PUSH_CHANNEL  = int(getenv("PUSH_CHANNEL"))  # Ensure this is an int (Discord channel ID)
GITHUB_SECRET = getenv("GITHUB_SECRET")


# Ensure bot is ready before processing any tasks
@bot.event
async def on_ready():
    print(f'Bot has connected to Discord as {bot.user}')


# Route for GitHub webhook
@app.route('/github-webhook', methods=['POST'])
def githubWebhook() -> tuple[str, int]:
    if request.method == 'POST':
        # Verify the request signature
        if (signature := request.headers.get('X-Hub-Signature-256')) is None: 
            abort(403)
            
        _, signature = signature.split('=')
        
        mac = hmac.new(
            bytes(GITHUB_SECRET, 'utf-8'), 
            digestmod = hashlib.sha256,
            msg       = request.data
        )
            
        if not hmac.compare_digest(mac.hexdigest(), signature):
            abort(403)
            
        #* Parse Payload
        payload   = request.json
        username  = payload['pusher']['name']
        repoName  = payload['repository']['name']
        commitMsg = payload['head_commit']['message']

        #* Create embed msg
        embed = discord.Embed(
            title = f"New Commit in {repoName}", 
            color = 0x00ff00
        )
        embed.add_field(
            name   = "User", 
            value  = username, 
            inline = True
        )
        embed.add_field(
            name   = "Message", 
            value  = commitMsg, 
            inline = False
        )

        # Send the message to Discord
        print(f"Attempting to send message to channel ID: {PUSH_CHANNEL}", file=__stderr__)
        chan = bot.get_channel(PUSH_CHANNEL)
        
        if chan:
            coroutine(chan.send(embed=embed), bot.loop)
        else:    
            print("[ERROR]: Channel not found", file=__stderr__)

        return '', 200
    
    else: 
        abort(400)


def runFlask() -> None: 
    """ Run Flask app in a separate thread """
    port = int(os.getenv("PORT", 5000))  # Use the port Heroku assigns
    app.run(host='0.0.0.0', port=port)


if __name__ == "__main__": 
    flaskThread = Thread(target=runFlask)
    flaskThread.start()

    bot.run(TOKEN)