from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pytube import YouTube
from pytube.exceptions import PytubeError
from moviepy.editor import AudioFileClip
import os
import io

app = Flask(__name__)
CORS(app) 

API_KEY = os.environ.get('API_SECRET_KEY')

@app.route('/convert', methods=['POST'])
def convert_video():
    request_api_key = request.headers.get('X-API-Key')
    if not API_KEY or request_api_key != API_KEY:
        return jsonify({"error": "Unauthorized Access"}), 401

    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        yt = YouTube(url)

        # --- IMPROVED STREAM SELECTION ---
        # First, try to get a specific audio-only stream which is often more reliable
        video_stream = yt.streams.get_audio_only()
        
        # If the preferred stream isn't found, fall back to the old method
        if video_stream is None:
            video_stream = yt.streams.filter(only_audio=True).first()

        # If there's still no stream, the video is likely unavailable
        if video_stream is None:
            raise PytubeError("No suitable audio stream found for this video.")

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
    
    # --- IMPROVED ERROR HANDLING ---
    except PytubeError as e:
        print(f"Pytube error for URL {url}: {str(e)}")
        return jsonify({"error": f"Video unavailable: It might be private, age-restricted, or removed."}), 500
    except Exception as e:
        print(f"Generic error for URL {url}: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred during conversion."}), 500
