from flask import Flask, request, abort
import os
import hmac
import hashlib
import requests

# Set the public URL for the worker dyno
WORKER_URL = "https://repo-bot-0cc1404b0c26.herokuapp.com/send_commit"  # Replace with your actual Heroku URL

# Set up Flask
app = Flask(__name__)

#* Environment variables
GITHUB_SECRET = os.getenv("GITHUB_SECRET")

# Route for GitHub webhook
@app.route('/github-webhook', methods=['POST'])
def githubWebhook():
    if request.method == 'POST':
        # Verify the request signature
        if (signature := request.headers.get('X-Hub-Signature-256')) is None: 
            abort(403)

        _, signature = signature.split('=')

        mac = hmac.new(
            bytes(GITHUB_SECRET, 'utf-8'), 
            digestmod=hashlib.sha256,
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
        print(f"Commit received: {username} committed '{commit_msg}' to {repo_name}")

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
    port = int(os.getenv("PORT", 5000))  # Use the port Heroku assigns
    app.run(host='0.0.0.0', port=port)


if __name__ == "__main__":
    runFlask()