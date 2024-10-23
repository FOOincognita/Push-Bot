
import os
import hmac
import hashlib
import discord
from os import getenv
from sys import __stderr__
from threading import Thread
from discord.ext import commands as cmd
from flask import Flask, request, abort
from asyncio import run_coroutine_threadsafe as coroutine
from datetime import datetime as dt, timezone as tz, timedelta as td

## Setup
#* Intents
intents          = discord.Intents.default()
intents.guilds   = True   
intents.messages = True
bot = cmd.Bot(command_prefix='!', intents=intents)

#* Flask
app = Flask(__name__)

#* Environment vars & consts
TOKEN         = getenv('DISCORD_BOT_TOKEN')
PUSH_CHANNEL  = 1296513687611244546
GITHUB_SECRET = getenv("GITHUB_SECRET")

#* Notify when bot ready
@bot.event
async def on_ready() -> None:
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
        repoURL   = payload['repository']['html_url']
        branch    = payload['ref'].split('/')[-1]
        commitMsg = "Oopsie Daisies: No commit msg :("
        commitURL = repoURL
        
        if commits := payload.get('commits', []):
            commitMsg = commits[-1]['message']
            commitURL = commits[-1]['url']

        #* Create embed
        embed = discord.Embed(
            title       = f"New Commit in {repoName}", 
            description = f"**Msg:** *{commitMsg}*\n",
            color       = 0x06ffdd, #? Aqua :3
            timestamp   = dt.now(tz(td(hours=-6)))
        )
        embed.add_field(
            name   = "\u200b", 
            value  = f"by **{username}** in branch **{branch}**", 
            inline = True
        )
        embed.add_field(
            name   = "Links", 
            value  = f"[View Changes]({commitURL}) | [View Repo]({repoURL})", 
            inline = False
        )
        embed.set_footer(
            text     = "GitHub", 
            icon_url = "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
        )

        #> Send msg to Discord
        print(f"Attempting to send message to channel ID: {PUSH_CHANNEL}", file=__stderr__)
        chan = bot.get_channel(PUSH_CHANNEL)
        
        if chan: coroutine(chan.send(embed=embed), bot.loop)
        else:    print("[ERROR]: Channel not found", file=__stderr__)

        return '', 200
    
    else: abort(400)
    
    
def runFlask() -> None: 
    """ Run Flask app in a separate thread """
    app.run(
        host = "0.0.0.0", 
        port = int(os.getenv("PORT", 5000))
    )

## Main
if __name__ == "__main__": 
    flaskThread = Thread(target=runFlask)
    flaskThread.start()

    bot.run(TOKEN)