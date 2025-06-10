from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os
import re

app = Flask(__name__)
CORS(app) 

API_KEY = os.environ.get('API_SECRET_KEY')

# A helper function to create a safe filename
def sanitize_filename(name):
    # Remove invalid characters
    return re.sub(r'[\/:*?"<>|]', "", name)

@app.route('/convert', methods=['POST'])
def convert_video():
    request_api_key = request.headers.get('X-API-Key')
    if not API_KEY or request_api_key != API_KEY:
        return jsonify({"error": "Unauthorized Access"}), 401

    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "URL is required"}), 400

    temp_filename_base = ""
    full_mp3_path = ""
    
    try:
        # --- yt-dlp OPTIONS ---
        # 1. First, just get the video info without downloading
        info_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'download')
            temp_filename_base = sanitize_filename(video_title)
            full_mp3_path = f"{temp_filename_base}.mp3"

        # 2. Now, configure for MP3 download
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            # ADD THIS LINE:
            'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'},
            'outtmpl': temp_filename_base, 
            'quiet': True,
        }

        # 3. Download and convert the file
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # 4. Check if the file was created
        if not os.path.exists(full_mp3_path):
            raise FileNotFoundError("Conversion failed, MP3 file not found.")

        # 5. Send the file back to the user
        return send_file(
            full_mp3_path,
            as_attachment=True,
            download_name=full_mp3_path,
            mimetype='audio/mpeg'
        )

    except Exception as e:
        print(f"yt-dlp error for URL {url}: {str(e)}")
        # Send a generic but helpful error
        return jsonify({"error": "Failed to convert video. It may be unavailable or protected."}), 500
    
    finally:
        # 6. VERY IMPORTANT: Clean up the server by deleting the file
        if os.path.exists(full_mp3_path):
            os.remove(full_mp3_path)
