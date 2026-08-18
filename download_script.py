import os
import tempfile
import requests
import yt_dlp

BOT_TOKEN = os.environ['BOT_TOKEN']
VIDEO_URL = os.environ['VIDEO_URL']
CHAT_ID = os.environ['CHAT_ID']

ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'outtmpl': os.path.join(tempfile.gettempdir(), '%(id)s.%(ext)s'),
    'noplaylist': True,
    'format': 'best[height<=1080]',
    'max_filesize': 49 * 1024 * 1024,
    'merge_output_format': 'mp4',
}

def send_file(file_path, file_type, caption=''):
    if file_type == 'video':
        method = 'sendVideo'
    elif file_type == 'photo':
        method = 'sendPhoto'
    else:
        method = 'sendDocument'
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {'chat_id': CHAT_ID, 'caption': caption}
        r = requests.post(url, data=data, files=files)
    return r.json()

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(VIDEO_URL, download=True)
    filepath = ydl.prepare_filename(info)
    if not os.path.exists(filepath):
        filepath = os.path.splitext(filepath)[0] + '.mp4'

    media_type = 'video' if info.get('vcodec') and info['vcodec'] != 'none' else 'document'
    if info.get('ext') in ['jpg', 'jpeg', 'png', 'webp']:
        media_type = 'photo'
    caption = info.get('title', '')[:200]

    result = send_file(filepath, media_type, caption)
    os.unlink(filepath)
    if result.get('ok'):
        print("File sent successfully")
    else:
        print(f"Error: {result.get('description')}")
