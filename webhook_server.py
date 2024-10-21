import os
from quart import Quart, request, abort
import hmac
import hashlib
import asyncio
from bot import send_commit_message  # Import the send_commit_message function from bot.py

# Set up Quart app
app = Quart(__name__)

# Environment variables
GITHUB_SECRET = os.getenv("GITHUB_SECRET")

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

    # Call the Discord bot function to send the commit message
    asyncio.create_task(send_commit_message(repo_name, username, commit_msg))

    return '', 200

if __name__ == "__main__":
    # Hypercorn will run this Quart app (via Procfile)
    pass