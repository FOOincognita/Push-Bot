import os
import discord
from discord.ext import commands
import asyncio
from aiohttp import web
import hmac
import hashlib

# Environment variables
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
PUSH_CHANNEL_ID = 1293643953048125535  # Help channel
GITHUB_SECRET = os.getenv("GITHUB_SECRET")

# Set up Discord bot
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Global variable to check if bot is ready
bot_ready = asyncio.Event()

@bot.event
async def on_ready():
    print(f'Bot has connected to Discord as {bot.user}')
    print("Guilds the bot is connected to:")
    for guild in bot.guilds:
        print(f"- {guild.name} (ID: {guild.id})")
    bot_ready.set()

# Async function to send commit messages
async def send_commit_message(repo_name: str, username: str, commit_msg: str):
    await bot_ready.wait()
    try:
        print(f"Attempting to fetch channel ID: {PUSH_CHANNEL_ID}")  # Debugging log
        channel = await bot.fetch_channel(PUSH_CHANNEL_ID)
        print("Channel fetched successfully, sending message...")  # Debugging log
        embed = discord.Embed(
            title=f"New Commit in {repo_name}",
            color=0x00ff00
        )
        embed.add_field(name="User", value=username, inline=True)
        embed.add_field(name="Message", value=commit_msg, inline=False)
        await channel.send(embed=embed)
    except discord.NotFound:
        print("[ERROR]: Channel not found")
    except discord.Forbidden:
        print("[ERROR]: Bot does not have permissions to access the channel")
    except discord.HTTPException as e:
        print(f"[ERROR]: Failed to fetch channel due to HTTPException: {e}")

# Set up aiohttp web server
async def handle_webhook(request):
    # Verify the request signature
    signature = request.headers.get('X-Hub-Signature-256')
    if signature is None:
        return web.Response(status=403)
    sha_name, signature = signature.split('=')
    if sha_name != 'sha256':
        return web.Response(status=403)

    body = await request.read()
    mac = hmac.new(bytes(GITHUB_SECRET, 'utf-8'), msg=body, digestmod='sha256')
    if not hmac.compare_digest(mac.hexdigest(), signature):
        return web.Response(status=403)

    # Parse Payload
    payload = await request.json()
    username = payload['pusher']['name']
    repo_name = payload['repository']['name']
    commit_msg = payload['head_commit']['message']

    # Schedule the send_commit_message function
    asyncio.create_task(send_commit_message(repo_name, username, commit_msg))

    return web.Response(status=200)

app = web.Application()
app.router.add_post('/github-webhook', handle_webhook)

# Run both bot and web server
async def main():
    # Start the web server
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 5000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    # Start the Discord bot
    await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())