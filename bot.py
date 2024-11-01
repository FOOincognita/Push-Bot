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
import json

## Setup
#* Intents
intents          = discord.Intents.default()
intents.guilds   = True   
intents.messages = True
bot              = cmd.Bot(command_prefix='!', intents=intents)

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
            print("[LOG]: Missing 'X-Hub-Signature-256' header", file=__stderr__)
            abort(403)
        
        try:
            _, sig_hash = signature.split('=')
        except ValueError:
            print("[LOG]: Invalid signature format", file=__stderr__)
            abort(403)
        
        mac = hmac.new(
            bytes(GITHUB_SECRET, 'utf-8'), 
            digestmod = hashlib.sha256,
            msg       = request.data
        )
        
        if not hmac.compare_digest(mac.hexdigest(), sig_hash):
            print("[LOG]: Signature mismatch", file=__stderr__)
            abort(403)
        
        #> Check event type
        if (event := request.headers.get('X-GitHub-Event')) != 'push':
            print(f"[LOG]: Ignored event type: {event}", file=__stderr__)
            return '', 200 
        
        #> Parse Payload
        if not (payload := request.json):
            print("[LOG]: Empty payload received", file=__stderr__)
            abort(400)
        
        if not (pusher := payload.get('pusher')):
            print(f"[LOG]: No 'pusher' key in payload: {json.dumps(payload)}", file=__stderr__)
            abort(400)
        
        username = pusher.get('name', 'Unknown')
        repo     = payload.get('repository', {})
        repoName = repo.get('name', 'Unknown Repository')
        repoURL  = repo.get('html_url', 'https://github.com/')
        
        ref    = payload.get('ref', 'refs/heads/main')
        branch = ref.split('/')[-1]
        
        if (commits := payload.get('commits', [])):
            latestCommit = commits[-1]
            commitMsg     = latestCommit.get('message', 'No commit message')
            commitURL     = latestCommit.get('url', repoURL)
        else:
            commitMsg = "No commits found."
            commitURL = repoURL
        
        #> Create embed
        embed = discord.Embed(
            title       = f"New Commit in {repoName}", 
            description = f"*{commitMsg}*\n",
            color       = 0x06ffdd,  #? Aqua color :3
            timestamp   = dt.now(tz=tz(td(hours=-6))) 
        )
        embed.add_field(
            name   = "\u200b", 
            value  = f"by **{username}** in branch **{branch}**", 
            inline = True
        )
        embed.add_field(
            name   = "\u200b", 
            value  = f"[View Changes]({commitURL}) | [View Repo]({repoURL})", 
            inline = False
        )
        embed.set_footer(
            text     = "GitHub", 
            icon_url = "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
        )
        
        #> Send msg to Discord
        print(f"[LOG]: Attempting to send message to channel ID: {PUSH_CHANNEL}", file=__stderr__)
        chan = bot.get_channel(PUSH_CHANNEL)
        
        if chan:
            try:
                coroutine(chan.send(embed=embed), bot.loop)
            except Exception as e:
                print(f"[LOG]: Failed to send embed: {e}", file=__stderr__)
        else:
            print("[LOG]: Channel not found", file=__stderr__)
        
        return '', 200
    
    else:
        abort(400)
        

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
