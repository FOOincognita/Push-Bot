from os import getenv
from flask import Flask, request, abort
import hmac
import hashlib
import os


#* Setup Flask
app = Flask(__name__)

#* Environment variables
GITHUB_SECRET = getenv("GITHUB_SECRET")

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

        # Log the payload for now (we'll have the worker send the message)
        print(f"Commit received: {username} committed '{commitMsg}' to {repoName}")

        return '', 200
    
    else: 
        abort(400)


def runFlask() -> None: 
    """ Run Flask app in the web dyno """
    port = int(os.getenv("PORT", 5000))  # Use the port Heroku assigns
    app.run(host='0.0.0.0', port=port)


if __name__ == "__main__": 
    runFlask()