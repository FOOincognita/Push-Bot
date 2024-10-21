import os
import discord
from discord.ext import commands
from quart import Quart, request, abort
import hmac
import hashlib
import asyncio

# Set up Discord bot
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Set up Quart app
app = Quart(__name__)

# Environment variables
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
PUSH_CHANNEL_ID = int(os.getenv("PUSH_CHANNEL"))  # Discord channel ID
GITHUB_SECRET = os.getenv("GITHUB_SECRET")

# Global variable to check if bot is ready
bot_ready = asyncio.Event()

# Ensure bot is ready before processing any tasks
@bot.event
async def on_ready():
    print(f'Bot has connected to Discord as {bot.user}')
    bot_ready.set()

# Route for GitHub webhook
@app.route('/github-webhook', methods=['POST'])
async def github_webhook():
    # Verify the request signature
    signature = request.headers.get('X-Hub-Signature-256')
    if signature is None:
        abort(403)
    sha_name, signature = signature.split('=')
    if sha_name != 'sha256':
        abort(403)

    mac = hmac.new(bytes(GITHUB_SECRET, 'utf-8'), msg=await request.get_data(), digestmod='sha256')
    if not hmac.compare_digest(mac.hexdigest(), signature):
        abort(403)

    # Parse Payload
    payload = await request.get_json()
    username = payload['pusher']['name']
    repo_name = payload['repository']['name']
    commit_msg = payload['head_commit']['message']

    # Wait until the bot is ready
    await bot_ready.wait()

    # Create embed message
    embed = discord.Embed(
        title=f"New Commit in {repo_name}",
        color=0x00ff00
    )
    embed.add_field(name="User", value=username, inline=True)
    embed.add_field(name="Message", value=commit_msg, inline=False)

    # Send the message to Discord
    channel = bot.get_channel(PUSH_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)
    else:
        print("[ERROR]: Channel not found")

    return '', 200

# Run both bot and Quart app
async def main():
    # Start the bot
    asyncio.create_task(bot.start(TOKEN))

    # Run the Quart app
    port = int(os.getenv("PORT", 5000))
    await app.run_task(host='0.0.0.0', port=port)

if __name__ == "__main__":
    asyncio.run(main())