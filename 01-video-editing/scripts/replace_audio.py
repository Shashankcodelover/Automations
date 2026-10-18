#!/usr/bin/env python3
"""
replace_audio.py — Royalty-Free Audio Replacement
==================================================
Module: 01-video-editing

Replaces or mixes the audio track of a video with a randomly selected
royalty-free track from Mixkit. If the original video has audio, it blends
the original (80% volume, pitch-shifted 4% for Content ID bypass) with the
new track (20% volume). If no original audio, overlays the music at 25%.

Usage:
    python replace_audio.py <input_video> [output_video]

If output_video is not specified, saves to <input>.new.mp4.

Dependencies:
    - ffmpeg / ffprobe (must be on PATH)
"""

import sys
import os
import random
import urllib.request
import subprocess
import tempfile

# List of stable, verified royalty-free Mixkit tracks
ROYALTY_FREE_TRACKS = [
    "https://assets.mixkit.co/music/preview/mixkit-tech-house-vibes-130.mp3",
    "https://assets.mixkit.co/music/preview/mixkit-hip-hop-02-738.mp3",
    "https://assets.mixkit.co/music/preview/mixkit-dreaming-big-31.mp3",
    "https://assets.mixkit.co/music/preview/mixkit-spirit-131.mp3",
    "https://assets.mixkit.co/music/preview/mixkit-deep-urban-623.mp3",
    "https://assets.mixkit.co/music/preview/mixkit-forest-treasure-138.mp3",
    "https://assets.mixkit.co/music/preview/mixkit-serene-view-443.mp3",
    "https://assets.mixkit.co/music/preview/mixkit-valley-sunset-122.mp3",
    "https://assets.mixkit.co/music/preview/mixkit-driving-ambition-32.mp3",
    "https://assets.mixkit.co/music/preview/mixkit-lazy-day-27.mp3"
]

def check_has_audio(video_path):
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "a",
        "-show_entries", "stream=codec_name", "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return len(res.stdout.strip()) > 0
    except Exception:
        return False

def replace_audio(video_path, output_path=None):
    if not output_path:
        output_path = video_path + ".new.mp4"
        
    print(f"Replacing audio for: {video_path}")
    temp_audio = os.path.join(tempfile.gettempdir(), "rf_music.mp3")
    
    # 1. Download random track
    track_url = random.choice(ROYALTY_FREE_TRACKS)
    print(f"Downloading royalty-free track: {track_url}")
    
    try:
        urllib.request.urlretrieve(track_url, temp_audio)
        if not os.path.exists(temp_audio) or os.path.getsize(temp_audio) < 1000:
            raise Exception("Downloaded file is empty or missing")
        print("Music downloaded successfully.")
    except Exception as e:
        print(f"Error downloading music: {e}")
        # Fallback to silent video if download fails, to ensure no copyright block
        print("Falling back to stripping audio completely (silent video)...")
        ffmpeg_cmd = ["ffmpeg", "-y", "-i", video_path, "-an", "-c:v", "copy", output_path]
        subprocess.run(ffmpeg_cmd, check=True)
        return True

    # Check if original video has audio
    has_audio = check_has_audio(video_path)
    print(f"Original video has audio: {has_audio}")

    # 2. Process audio with ffmpeg
    if has_audio:
        # MIX original audio and royalty-free music:
        # - [0:a]asetrate=45864,aresample=44100 speeds up + pitch-shifts original audio by 4% to bypass Content ID
        # - volume=0.8 keeps the original sound (animal meows) clear
        # - volume=0.2 blends in the royalty-free background beat
        filter_complex = "[0:a]asetrate=45864,aresample=44100,volume=0.8[a0];[1:a]volume=0.2[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2[a]"
        ffmpeg_cmd = [
            "ffmpeg", "-y", 
            "-i", video_path, 
            "-stream_loop", "-1", "-i", temp_audio, 
            "-filter_complex", filter_complex,
            "-map", "0:v", "-map", "[a]", 
            "-c:v", "copy", 
            "-c:a", "aac", 
            "-shortest", 
            output_path
        ]
    else:
        # Just overlay the royalty-free background music
        ffmpeg_cmd = [
            "ffmpeg", "-y", 
            "-i", video_path, 
            "-stream_loop", "-1", "-i", temp_audio, 
            "-filter_complex", "[1:a]volume=0.25[a]",
            "-map", "0:v", "-map", "[a]", 
            "-c:v", "copy", 
            "-c:a", "aac", 
            "-shortest", 
            output_path
        ]
    
    try:
        print(f"Running FFmpeg: {' '.join(ffmpeg_cmd)}")
        subprocess.run(ffmpeg_cmd, check=True)
        print("Audio blending/replacement complete.")
        
        # Clean up temp audio
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
            
        return True
    except Exception as e:
        print(f"FFmpeg error: {e}")
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 replace_audio.py <input_video_path> [output_video_path]")
        sys.exit(1)
        
    in_video = sys.argv[1]
    out_video = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = replace_audio(in_video, out_video)
    if not success:
        sys.exit(1)
