
import os
import tempfile
import requests
import yt_dlp
import json

BOT_TOKEN = os.environ['BOT_TOKEN']
VIDEO_URL = os.environ['VIDEO_URL']
CHAT_ID = os.environ['CHAT_ID']

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

def send_text(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': text}
    requests.post(url, json=data)

def try_ytdlp(url):
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
        caption = info.get('title', '')[:200]
        return [{'path': filepath, 'type': media_type, 'caption': caption}]

def try_ddinstagram(url):
    endpoints = [
        f"https://api.ddinstagram.com/video?url={url}",
        f"https://api.ddinstagram.com/images?url={url}"
    ]
    for ep in endpoints:
        try:
            r = requests.get(ep, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if 'url' in data and data['url']:
                    media_type = 'video' if ep.startswith("https://api.ddinstagram.com/video") else 'photo'
                    return [{'url': data['url'], 'type': media_type, 'caption': ''}]
                if 'images' in data and isinstance(data['images'], list):
                    media_list = []
                    for img in data['images']:
                        if isinstance(img, str):
                            media_list.append({'url': img, 'type': 'photo', 'caption': ''})
                        elif isinstance(img, dict) and 'url' in img:
                            media_list.append({'url': img['url'], 'type': 'photo', 'caption': ''})
                    if media_list:
                        return media_list
        except:
            continue
    return None

def try_instaweb(url):
    # ممکنه بعضی سرویس‌ها مثل instaweb کار کنن
    api = f"https://api.instaweb.me/api/download?url={url}"
    try:
        r = requests.get(api, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if 'media' in data and isinstance(data['media'], list):
                media_list = []
                for item in data['media']:
                    media_list.append({'url': item['url'], 'type': 'video' if item.get('type') == 'video' else 'photo', 'caption': ''})
                if media_list:
                    return media_list
    except:
        pass
    return None

def download_and_send(url):
    # امتحان yt-dlp
    try:
        media_list = try_ytdlp(url)
        if media_list:
            for media in media_list:
                filepath = media['path']
                file_type = media['type']
                caption = media['caption']
                result = send_file(filepath, file_type, caption)
                os.unlink(filepath)
                if not result.get('ok'):
                    send_text(f"Error sending file: {result.get('description')}")
            return
    except Exception as e:
        print(f"yt-dlp failed: {e}")

    # امتحان ddinstagram
    media_list = try_ddinstagram(url)
    if media_list:
        for media in media_list:
            media_url = media['url']
            file_type = media['type']
            r = requests.get(media_url, timeout=30)
            if r.status_code == 200:
                ext = 'mp4' if file_type == 'video' else 'jpg'
                filepath = os.path.join(tempfile.gettempdir(), f"dd_media.{ext}")
                with open(filepath, 'wb') as f:
                    f.write(r.content)
                result = send_file(filepath, file_type, '')
                os.unlink(filepath)
                if not result.get('ok'):
                    send_text(f"Error sending file: {result.get('description')}")
        return

    # امتحان instaweb
    media_list = try_instaweb(url)
    if media_list:
        for media in media_list:
            media_url = media['url']
            file_type = media['type']
            r = requests.get(media_url, timeout=30)
            if r.status_code == 200:
                ext = 'mp4' if file_type == 'video' else 'jpg'
                filepath = os.path.join(tempfile.gettempdir(), f"insta_media.{ext}")
                with open(filepath, 'wb') as f:
                    f.write(r.content)
                result = send_file(filepath, file_type, '')
                os.unlink(filepath)
                if not result.get('ok'):
                    send_text(f"Error sending file: {result.get('description')}")
        return

    send_text("❌ دانلود ناموفق بود. لطفاً مطمئن شوید پست عمومی است و لینک صحیح است.")

if __name__ == "__main__":
    download_and_send(VIDEO_URL)
