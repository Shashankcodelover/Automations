#!/usr/bin/env python3
"""
cloud_publisher.py — GitHub Actions YouTube Auto-Publisher
===========================================================
Module: 04-youtube-publishing

Designed to run in GitHub Actions (24/7 free). Picks the next video from a
Google Drive queue folder, mixes background music, generates SEO metadata
via Gemini, uploads to YouTube as an unlisted Short, deletes from queue,
and sends a Telegram notification.

Environment Variables Required:
    GOOGLE_TOKEN_JSON         — JSON string of OAuth2 credentials
    GEMINI_API_KEY            — Gemini API key for SEO generation
    TELEGRAM_BOT_TOKEN        — Telegram bot token for notifications
    TELEGRAM_CHAT_ID          — Telegram chat ID for alerts
    GOOGLE_DRIVE_QUEUE_FOLDER_ID — Google Drive folder ID for the video queue

Dependencies:
    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib yt-dlp
"""

import os
import sys
import json
import random
import pathlib
import urllib.request
import subprocess
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# ── Auto-load .env if present (walks up parent directories) ────────────────────
def _load_env():
    p = pathlib.Path(__file__).parent.resolve()
    for _ in range(4):
        env_p = p / ".env"
        if env_p.exists():
            for line in env_p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
            break
        p = p.parent

_load_env()
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# Scopes
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/youtube.upload']

# List of stable, verified cute, happy, and lo-fi royalty-free tracks for cat videos
ROYALTY_FREE_TRACKS = [
    "https://assets.mixkit.co/music/preview/mixkit-lazy-day-27.mp3",        # Chill, relaxing lo-fi acoustic
    "https://assets.mixkit.co/music/preview/mixkit-serene-view-443.mp3",     # Warm, sweet lo-fi beat
    "https://assets.mixkit.co/music/preview/mixkit-valley-sunset-122.mp3",   # Sweet acoustic folk, happy
    "https://assets.mixkit.co/music/preview/mixkit-dreaming-big-31.mp3",     # Uplifting, cute piano
    "https://assets.mixkit.co/music/preview/mixkit-forest-treasure-138.mp3", # Whimsical, playful acoustic
    "https://assets.mixkit.co/music/preview/mixkit-sun-and-tide-150.mp3"     # Carefree, happy acoustic
]

def get_background_music():
    """Gets the path to the background music. Checks for custom music folder first, falls back to download."""
    music_folder = "music"
    temp_audio = "rf_music.mp3"
    
    # 1. Check for custom music folder in the repository
    if os.path.exists(music_folder) and os.path.isdir(music_folder):
        mp3_files = [f for f in os.listdir(music_folder) if f.endswith(".mp3")]
        if mp3_files:
            selected = os.path.join(music_folder, random.choice(mp3_files))
            print(f"Using custom background music from repository: {selected}")
            return selected, False # False means do not delete after mixing
            
    # 2. Fallback to downloading a cute track
    track_url = random.choice(ROYALTY_FREE_TRACKS)
    print(f"No custom music found in 'music/' folder. Downloading cute fallback track: {track_url}")
    try:
        urllib.request.urlretrieve(track_url, temp_audio)
        if not os.path.exists(temp_audio) or os.path.getsize(temp_audio) < 1000:
            raise Exception("Downloaded file is empty")
        return temp_audio, True # True means delete temp file after mixing
    except Exception as e:
        print(f"Error downloading music: {e}. Stripping audio instead...")
        return None, False


def send_telegram(text, token, chat_id):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
        print("Telegram alert sent successfully.")
    except Exception as e:
        print(f"Warning: Failed to send Telegram alert: {e}")

def get_google_creds():
    token_json = os.environ.get("GOOGLE_TOKEN_JSON")
    if not token_json:
        # Fallback to local token.json or infra/tokens/token.json
        candidate_paths = [
            pathlib.Path("token.json"),
            pathlib.Path(__file__).parent / "token.json",
            pathlib.Path(__file__).parent.parent.parent / "infra" / "tokens" / "token.json",
            pathlib.Path(__file__).parent.parent.parent / "token.json",
        ]
        found_path = None
        for cand in candidate_paths:
            if cand.exists():
                found_path = cand
                break

        if found_path:
            token_json = found_path.read_text(encoding="utf-8")
        else:
            raise FileNotFoundError(
                "GOOGLE_TOKEN_JSON env variable or token.json file not found.\n"
                "Run `python get_google_token.py` first to generate your token."
            )
            
    creds_dict = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(creds_dict, SCOPES)
    
    if creds and creds.expired and creds.refresh_token:
        print("Refreshing Google access credentials...")
        creds.refresh(Request())
        
    return creds

def get_gemini_seo(topic, api_key):
    # Call Gemini Flash API directly using HTTP POST to avoid complex SDK imports in simple runner
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    prompt = f"""You are the world's #1 YouTube Shorts growth hacker and viral SEO expert for AI-generated cinematic content. 
This is a YouTube SHORT (~1:20, vertical 9:16). Optimize for the Shorts feed algorithm.

Video Topic: {topic}

Return raw JSON only (no markdown, no backticks).
{{
 "youtubeTitle": "[Subject] Looks INSANE in AI 🔥 #Shorts",
 "youtubeDescription": "🔥 [Bold 1-line hook]\\n👀 [curiosity question]\\n\\n[Sensory description 1]\\n[Sensory description 2]\\n\\n✨ Created with Google VEO 3\\n🔔 Subscribe for daily AI Shorts\\n\\n#shorts #viralshorts #[exactSubject]",
 "youtubeTags": ["tag1", "tag2"],
 "youtubeCategory": "15",
 "defaultLanguage": "en"
}}"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            res = json.loads(response.read().decode('utf-8'))
            text_resp = res['candidates'][0]['content']['parts'][0]['text']
            return json.loads(text_resp.strip())
    except Exception as e:
        print(f"Gemini API error: {e}")
        # Return fallback SEO metadata to prevent execution failure
        return {
            "youtubeTitle": f"{topic} Looks INSANE in AI 🔥 #Shorts",
            "youtubeDescription": f"🔥 {topic} generated by AI VEO 3!\n👀 What do you think about this?\n\n✨ Created with Google VEO 3.\n🔔 Subscribe for daily AI Shorts!\n\n#shorts #viralshorts #ai",
            "youtubeTags": ["shorts", "viral", "ai"],
            "youtubeCategory": "15",
            "defaultLanguage": "en"
        }

def download_mix_audio(video_path, output_path):
    print("Replacing audio for:", video_path)
    
    # Get background music (checks music/ folder first, falls back to download)
    music_file, should_delete = get_background_music()
    
    if not music_file or not os.path.exists(music_file):
        print("No background music available. Stripping audio instead...")
        ffmpeg_cmd = ["ffmpeg", "-y", "-i", video_path, "-an", "-c:v", "copy", output_path]
        subprocess.run(ffmpeg_cmd, check=True)
        return

    # Check if original video has audio
    has_audio = False
    try:
        probe_cmd = [
            "ffprobe", "-v", "error", "-select_streams", "a",
            "-show_entries", "stream=codec_name", "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        res = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        has_audio = len(res.stdout.strip()) > 0
    except Exception:
        pass
        
    print(f"Original video has audio: {has_audio}")
    
    if has_audio:
        # Keep original audio 100% untouched (no pitch/speed shift, volume 1.0) and mix background music at 0.25 volume
        filter_complex = "[0:a]volume=1.0[a0];[1:a]volume=0.25[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2[a]"
        ffmpeg_cmd = [
            "ffmpeg", "-y", 
            "-i", video_path, 
            "-stream_loop", "-1", "-i", music_file, 
            "-filter_complex", filter_complex,
            "-map", "0:v", "-map", "[a]", 
            "-c:v", "copy", 
            "-c:a", "aac", 
            "-shortest", 
            output_path
        ]
    else:
        # Overlay royalty-free music at a normal volume (0.35)
        ffmpeg_cmd = [
            "ffmpeg", "-y", 
            "-i", video_path, 
            "-stream_loop", "-1", "-i", music_file, 
            "-filter_complex", "[1:a]volume=0.35[a]",
            "-map", "0:v", "-map", "[a]", 
            "-c:v", "copy", 
            "-c:a", "aac", 
            "-shortest", 
            output_path
        ]
        
    subprocess.run(ffmpeg_cmd, check=True)
    
    # Delete temporary downloaded file if needed
    if should_delete and os.path.exists(music_file):
        os.remove(music_file)

def main():
    # Load Environment Secrets
    folder_id = os.environ.get("GOOGLE_DRIVE_QUEUE_FOLDER_ID", "124xifvalyDFoyQSZUx6zNtyS7IqyaS15")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    
    if not gemini_key or not tg_token:
        print("ERROR: Missing environment variables (GEMINI_API_KEY or TELEGRAM_BOT_TOKEN)")
        sys.exit(1)
        
    try:
        # 1. Connect to Google APIs
        creds = get_google_creds()
        drive_service = build('drive', 'v3', credentials=creds)
        youtube_service = build('youtube', 'v3', credentials=creds)
        
        # 2. List queue folder files alphabetically
        query = f"'{folder_id}' in parents and trashed = false"
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        if not files:
            print("Queue folder is empty. Nothing to publish.")
            send_telegram("⚠️ *YouTube Auto-Publish Alert*:\nQueue folder is empty! No video to publish.", tg_token, tg_chat_id)
            sys.exit(0)
            
        # Sort alphabetically
        files.sort(key=lambda x: x['name'].lower())
        target_file = files[0]
        file_id = target_file['id']
        filename = target_file['name']
        print(f"Selected file to upload: {filename} (ID: {file_id})")
        
        # Extract clean video title from name
        topic_name = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').strip()
        
        # 3. Download the video
        local_input = "input_video.mp4"
        local_output = "clean_video.mp4"
        print(f"Downloading video from Google Drive...")
        
        request = drive_service.files().get_media(fileId=file_id)
        with open(local_input, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                
        print("Download complete.")
        
        # 4. Process video and replace audio
        print("Mixing background music and pitch-shifting video audio...")
        download_mix_audio(local_input, local_output)
        
        # 5. Generate SEO metadata via Gemini
        print("Generating viral title and descriptions via Gemini 2.5 Flash...")
        seo = get_gemini_seo(topic_name, gemini_key)
        title = seo.get("youtubeTitle", f"{topic_name} #Shorts")
        desc = seo.get("youtubeDescription", "")
        tags = seo.get("youtubeTags", [])
        cat_id = seo.get("youtubeCategory", "15")
        
        print(f"Title: {title}")
        print(f"Tags: {tags}")
        
        # 6. Upload to YouTube Shorts
        print("Uploading to YouTube...")
        body = {
            'snippet': {
                'title': title,
                'description': desc,
                'tags': tags,
                'categoryId': cat_id
            },
            'status': {
                'privacyStatus': 'unlisted',
                'selfDeclaredMadeForKids': False
            }
        }
        
        media = MediaFileUpload(local_output, chunksize=-1, resumable=True, mimetype='video/mp4')
        request_insert = youtube_service.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )
        
        response_yt = None
        while response_yt is None:
            status, response_yt = request_insert.next_chunk()
            if status:
                print(f"Upload progress: {int(status.progress() * 100)}%")
                
        video_id = response_yt.get("id")
        print(f"Successfully uploaded! Video ID: {video_id}")
        
        # 7. Delete file from Google Drive queue folder
        print("Deleting video from Google Drive queue...")
        drive_service.files().delete(fileId=file_id).execute()
        
        # Clean up local files
        for f in [local_input, local_output]:
            if os.path.exists(f):
                os.remove(f)
                
        # 8. Send Telegram Alert
        success_msg = f"✅ *Video Published on YouTube!*\n\n📹 *Title:* {title}\n🔗 *URL:* https://www.youtube.com/shorts/{video_id}"
        send_telegram(success_msg, tg_token, tg_chat_id)
        print("All done!")
        
    except Exception as e:
        error_msg = f"❌ *YouTube Auto-Publish Error*:\n{e}"
        print(error_msg)
        send_telegram(error_msg, tg_token, tg_chat_id)
        sys.exit(1)

if __name__ == '__main__':
    main()
