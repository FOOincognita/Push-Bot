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

## Setup
#* Intents
intents          = discord.Intents.default()
intents.guilds   = True   
intents.messages = True
bot = cmd.Bot(command_prefix='!', intents=intents)

#* Flask
app = Flask(__name__)

def runFlask() -> None: 
    """ Run Flask app in a separate thread """
    app.run(
        host = "0.0.0.0", 
        port = int(os.getenv("PORT", 5000))
    )

#* Environment vars & consts
TOKEN         = getenv('DISCORD_BOT_TOKEN')
PUSH_CHANNEL  = 1296513687611244546
GITHUB_SECRET = getenv("GITHUB_SECRET")


#* Notify when bot ready
@bot.event
async def on_ready():
    print(f'Bot has connected to Discord as {bot.user}')

## GitHub Goodness
#* Webhook & msg send
@app.route('/github-webhook', methods=['POST'])
def githubWebhook() -> tuple[str, int]:
    if request.method == 'POST':
        #> Verify signature
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

        #* Send msg to Discord
        print(f"Attempting to send message to channel ID: {PUSH_CHANNEL}", file=__stderr__)
        chan = bot.get_channel(PUSH_CHANNEL)
        
        if chan: coroutine(chan.send(embed=embed), bot.loop)
        else:    print("[ERROR]: Channel not found", file=__stderr__)

        return '', 200
    
    else: abort(400)

## Main
if __name__ == "__main__": 
    flaskThread = Thread(target=runFlask)
    flaskThread.start()

    bot.run(TOKEN)