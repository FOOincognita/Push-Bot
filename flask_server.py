from os import getenv
from flask import Flask, request, abort
import hmac
import hashlib
import requests

#* Setup Flask
app = Flask(__name__)

#* Environment variables
GITHUB_SECRET = getenv("GITHUB_SECRET")
WORKER_URL = "http://localhost:5001/send_commit"  # Local request to worker

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
            msg=request.data
        )

        if not hmac.compare_digest(mac.hexdigest(), signature):
            abort(403)

        #* Parse Payload
        payload = request.json
        username = payload['pusher']['name']
        repo_name = payload['repository']['name']
        commit_msg = payload['head_commit']['message']

        # Log the payload for now
        print(f"**PUSH:**\nCommit to {repo_name} by {username}\nMessage:'{commit_msg}'")

        # Send the commit data to the worker (Discord bot)
        data = {
            'repo_name': repo_name,
            'username': username,
            'commit_msg': commit_msg
        }
        try:
            # Send a POST request to the worker dyno
            response = requests.post(WORKER_URL, json=data)
            print(f"Worker response: {response.status_code}")
        except Exception as e:
            print(f"Error sending to worker: {e}")

        return '', 200

    else:
        abort(400)


def runFlask() -> None:
    """ Run Flask app in the web dyno """
    port = int(getenv("PORT", 5000))  # Use the port Heroku assigns
    app.run(host='0.0.0.0', port=port)


if __name__ == "__main__":
    runFlask()