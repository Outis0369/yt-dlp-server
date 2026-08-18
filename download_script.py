import os
import tempfile
import requests
import yt_dlp
import re
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

def download_file_to_temp(url, ext):
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            filepath = os.path.join(tempfile.gettempdir(), f"media_{os.urandom(4).hex()}.{ext}")
            with open(filepath, 'wb') as f:
                f.write(r.content)
            return filepath
    except:
        pass
    return None

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

def try_instagram_a1(url):
    """Try old JSON endpoint ?__a=1"""
    try:
        json_url = url.rstrip('/') + '/?__a=1&__d=dis'
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(json_url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            media_list = []
            if 'graphql' in data:
                shortcode = data['graphql']['shortcode_media']
                if shortcode.get('is_video'):
                    media_list.append({'url': shortcode['video_url'], 'type': 'video', 'caption': shortcode.get('title', '')})
                else:
                    media_list.append({'url': shortcode['display_url'], 'type': 'photo', 'caption': ''})
                if 'edge_sidecar_to_children' in shortcode:
                    for child in shortcode['edge_sidecar_to_children']['edges']:
                        node = child['node']
                        if node.get('is_video'):
                            media_list.append({'url': node['video_url'], 'type': 'video', 'caption': ''})
                        else:
                            media_list.append({'url': node['display_url'], 'type': 'photo', 'caption': ''})
            return media_list if media_list else None
    except:
        pass
    return None

def try_instagram_embed(url):
    """Try embed page"""
    try:
        embed_url = url.rstrip('/') + '/embed/captioned/'
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(embed_url, headers=headers, timeout=15)
        if r.status_code == 200:
            html = r.text
            match = re.search(r'window\.__additionalDataLoaded\s*=\s*({.*?});', html, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                media_list = []
                if 'graphql' in data and 'shortcode_media' in data['graphql']:
                    shortcode = data['graphql']['shortcode_media']
                    if shortcode.get('is_video'):
                        media_list.append({'url': shortcode['video_url'], 'type': 'video', 'caption': shortcode.get('title', '')})
                    else:
                        media_list.append({'url': shortcode['display_url'], 'type': 'photo', 'caption': ''})
                    if 'edge_sidecar_to_children' in shortcode:
                        for child in shortcode['edge_sidecar_to_children']['edges']:
                            node = child['node']
                            if node.get('is_video'):
                                media_list.append({'url': node['video_url'], 'type': 'video', 'caption': ''})
                            else:
                                media_list.append({'url': node['display_url'], 'type': 'photo', 'caption': ''})
                return media_list if media_list else None
    except:
        pass
    return None

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

def try_snapinsta(url):
    # ممکنه کار کنه
    api = f"https://api.snapinsta.app/api?url={url}"
    try:
        r = requests.get(api, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if 'media' in data and isinstance(data['media'], list):
                media_list = []
                for item in data['media']:
                    media_list.append({
                        'url': item['url'],
                        'type': 'video' if item.get('type') == 'video' else 'photo',
                        'caption': ''
                    })
                return media_list if media_list else None
    except:
        pass
    return None

def process_media_list(media_list):
    if not media_list:
        return False
    for media in media_list:
        if media.get('path'):  # from yt-dlp
            filepath = media['path']
            file_type = media['type']
            caption = media['caption']
            result = send_file(filepath, file_type, caption)
            os.unlink(filepath)
            if not result.get('ok'):
                send_text(f"Error sending file: {result.get('description')}")
        else:  # from URL
            media_url = media['url']
            file_type = media['type']
            ext = 'mp4' if file_type == 'video' else 'jpg'
            filepath = download_file_to_temp(media_url, ext)
            if filepath:
                result = send_file(filepath, file_type, media.get('caption', ''))
                os.unlink(filepath)
                if not result.get('ok'):
                    send_text(f"Error sending file: {result.get('description')}")
    return True

def main():
    # 1) yt-dlp
    try:
        media_list = try_ytdlp(VIDEO_URL)
        if media_list:
            if process_media_list(media_list):
                return
    except Exception as e:
        print(f"yt-dlp failed: {e}")

    # 2) Instagram ?__a=1
    media_list = try_instagram_a1(VIDEO_URL)
    if media_list:
        if process_media_list(media_list):
            return

    # 3) Instagram embed
    media_list = try_instagram_embed(VIDEO_URL)
    if media_list:
        if process_media_list(media_list):
            return

    # 4) ddinstagram
    media_list = try_ddinstagram(VIDEO_URL)
    if media_list:
        if process_media_list(media_list):
            return

    # 5) snapinsta
    media_list = try_snapinsta(VIDEO_URL)
    if media_list:
        if process_media_list(media_list):
            return

    send_text("❌ هیچ روشی جواب نداد. لطفاً مطمئن شوید پست عمومی است و لینک صحیح است.")

if __name__ == "__main__":
    main()
