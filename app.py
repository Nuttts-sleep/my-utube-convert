from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pytube import YouTube
from moviepy.editor import AudioFileClip
import os
import io

app = Flask(__name__)
CORS(app) 

# Load the secret key from the environment variables set on Render
# This is safe because the key is NOT written in the code
API_KEY = os.environ.get('API_SECRET_KEY')

@app.route('/convert', methods=['POST'])
def convert_video():
    # --- SECURITY CHECK ---
    # Check if the request includes the correct API key in its headers
    request_api_key = request.headers.get('X-API-Key')
    if not API_KEY or request_api_key != API_KEY:
        # If the key is missing or wrong, deny access
        return jsonify({"error": "Unauthorized Access"}), 401

    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        yt = YouTube(url)
        video_stream = yt.streams.filter(only_audio=True).first()
        buffer = io.BytesIO()
        video_stream.stream_to_buffer(buffer)
        buffer.seek(0)
        temp_input_filename = "temp_audio_input"
        with open(temp_input_filename, "wb") as f:
            f.write(buffer.read())

        audio_clip = AudioFileClip(temp_input_filename)
        mp3_buffer = io.BytesIO()
        audio_clip.write_audiofile(mp3_buffer, codec='libmp3lame')
        mp3_buffer.seek(0)
        audio_clip.close()
        os.remove(temp_input_filename)

        safe_title = "".join([c for c in yt.title if c.isalpha() or c.isdigit() or c.isspace()]).rstrip()
        mp3_filename = f"{safe_title}.mp3"

        return send_file(
            mp3_buffer,
            as_attachment=True,
            download_name=mp3_filename,
            mimetype='audio/mpeg'
        )
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": f"An error occurred during conversion: {str(e)}"}), 500