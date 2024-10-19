import os
import discord
from discord.ext import commands
from flask import Flask, request, abort
import threading
import asyncio
import hmac
import hashlib

# Discord bot setup
intents = discord.Intents.default()
bot     = commands.Bot(command_prefix='!', intents=intents)

# Flask app setup
app = Flask(__name__)

#! Replace this with the ID of your #push-announcements channel
TOKEN         = os.getenv('DISCORD_BOT_TOKEN')
PUSH_CHANNEL  = os.getenv("PUSH_CHANNEL")
GITHUB_SECRET = os.getenv("GITHUB_SECRET")

# Route for GitHub webhook
@app.route('/github-webhook', methods=['POST'])
def githubWebhook() -> tuple[str, int]:
    if request.method == 'POST':
        # Verify the request signature
        signature = request.headers.get('X-Hub-Signature-256')
        
        if signature is None: abort(403)
            
        _, signature = signature.split('=')
        
        mac = hmac.new(
            bytes(GITHUB_SECRET, 'utf-8'), 
            digestmod = hashlib.sha256,
            msg       = request.data
        )
            
        if not hmac.compare_digest(mac.hexdigest(), signature):
            abort(403)

        payload   = request.json
        repoName  = payload['repository']['name']
        username  = payload['pusher']['name']
        commitMsg = payload['head_commit']['message']

        # Create an embed message
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
        channel = bot.get_channel(PUSH_CHANNEL)
        
        if channel:
            asyncio.run_coroutine_threadsafe(channel.send(embed=embed), bot.loop)
        else:
            print("Channel not found")

        return '', 200
    else:
        abort(400)
        

# Run Flask app in a separate thread
def run_flask(): app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__": 
    # Start the Flask app
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Run bot
    bot.run(TOKEN)