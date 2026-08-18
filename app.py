import os
import tempfile
import requests
from flask import Flask, request, jsonify
import yt_dlp
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get('BOT_TOKEN')

def send_telegram_file(chat_id, file_path, file_type, caption=''):
    if file_type == "video":
        method = 'sendVideo'
    elif file_type == "photo":
        method = 'sendPhoto'
    else:
        method = 'sendDocument'
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {'chat_id': chat_id, 'caption': caption}
        response = requests.post(url, data=data, files=files)
    return response.json()

def get_media_info(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'outtmpl': os.path.join(tempfile.gettempdir(), '%(id)s.%(ext)s'),
        'noplaylist': True,
        'format': 'best[height<=1080]',
        'max_filesize': 49 * 1024 * 1024,
        'merge_output_format': 'mp4',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)
        if not os.path.exists(filepath):
            filepath = os.path.splitext(filepath)[0] + '.mp4'
        media_type = 'video' if info.get('vcodec') and info['vcodec'] != 'none' else 'document'
        if info.get('ext') in ['jpg', 'jpeg', 'png', 'webp']:
            media_type = 'photo'
        return {
            'filepath': filepath,
            'media_type': media_type,
            'caption': info.get('title', '')[:200],
            'ext': info.get('ext')
        }

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.json
        url = data.get('url')
        chat_id = data.get('chat_id')
        if not url or not chat_id:
            return jsonify({'error': 'Missing url or chat_id'}), 400
        media = get_media_info(url)
        result = send_telegram_file(chat_id, media['filepath'], media['media_type'], media['caption'])
        os.unlink(media['filepath'])
        if result.get('ok'):
            return jsonify({'success': True, 'result': result})
        else:
            return jsonify({'error': result.get('description', 'Telegram send failed')}), 500
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
