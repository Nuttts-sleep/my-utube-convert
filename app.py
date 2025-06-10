from flask import Flask, request, jsonify
from flask_cors import CORS
import requests # The library for talking to other servers

app = Flask(__name__)
# This allows your GitHub website to talk to THIS server
CORS(app) 

COBALT_API_URL = "https://cobalt.tools/api/json"

@app.route('/convert-proxy', methods=['POST'])
def convert_proxy():
    # 1. Get the YouTube URL from your website's request
    data = request.get_json()
    youtube_url = data.get('url')

    if not youtube_url:
        return jsonify({"error": "URL is required"}), 400

    # 2. Prepare the request to send to the real Cobalt API
    cobalt_payload = {
        "url": youtube_url,
        "isAudioOnly": True
    }
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    try:
        # 3. Your server talks to the Cobalt API (server-to-server, no CORS error)
        response = requests.post(COBALT_API_URL, headers=headers, json=cobalt_payload)
        response.raise_for_status() # Raise an exception for bad status codes (like 404 or 500)
        
        # 4. Get the response from Cobalt and send it straight back to your website
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error talking to Cobalt API: {e}")
        return jsonify({"error": "The conversion service is currently unavailable."}), 502
