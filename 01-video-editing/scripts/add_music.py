#!/usr/bin/env python3
"""
add_music.py — Background Music Overlay
========================================
Module: 01-video-editing

Downloads a trending royalty-free background track (via yt-dlp search or
direct URL fallback) and mixes it underneath the original video audio at
10% volume using FFmpeg.

Usage:
    python add_music.py <video_path>

The video file is modified IN-PLACE — the original is overwritten with the
music-blended version.

Dependencies:
    - ffmpeg / ffprobe (must be on PATH)
    - yt-dlp (pip install yt-dlp)
"""

import sys
import subprocess
import os
import tempfile
import urllib.request


def check_has_audio(video_path):
    """Probe a video file to check whether it contains an audio stream."""
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


def add_background_music(video_path):
    """
    Download a trending background track and mix it with the video.

    Returns True on success (or if music was skipped gracefully),
    False on hard failure.
    """
    print(f"Processing video: {video_path}")

    # Define temp paths (cross-platform)
    tmp_dir = tempfile.gettempdir()
    temp_audio = os.path.join(tmp_dir, "trending_temp_audio.mp3")
    temp_output = os.path.join(tmp_dir, "processed_video_temp.mp4")

    # 1. Download trending background song using yt-dlp
    search_query = "ytsearch1:trending tiktok background music instrumental copyright free"
    print(f"Downloading background audio using query: {search_query}")

    # Delete temp audio if it exists
    if os.path.exists(temp_audio):
        os.remove(temp_audio)

    download_cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--no-playlist",
        "--max-filesize", "15M",
        "--js-runtimes", "node",
        "-o", temp_audio,
        search_query
    ]

    try:
        subprocess.run(download_cmd, check=True)
        if not os.path.exists(temp_audio):
            raise FileNotFoundError("yt-dlp finished but the output audio file was not found.")
        print("Successfully downloaded background audio.")
    except Exception as e:
        print(f"Warning: Failed to download audio via yt-dlp: {e}")
        # Try a direct fallback URL using stdlib (no external dependency)
        fallback_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
        print(f"Trying fallback direct URL download: {fallback_url}")
        try:
            urllib.request.urlretrieve(fallback_url, temp_audio)
            if not os.path.exists(temp_audio) or os.path.getsize(temp_audio) < 1000:
                raise Exception("Downloaded file is empty or too small")
            print("Successfully downloaded fallback audio.")
        except Exception as fe:
            print(f"Warning: Fallback download also failed: {fe}. Proceeding with original video (no music).")
            if os.path.exists(temp_audio):
                os.remove(temp_audio)
            return True

    # 2. Check if background audio was successfully obtained
    if not os.path.exists(temp_audio):
        print("Warning: Background audio file was not downloaded. Skipping music mixing.")
        return True

    # 3. Check if original video has audio
    has_audio = check_has_audio(video_path)
    print(f"Original video has audio: {has_audio}")

    # 4. Mix audio using ffmpeg
    # We loop the background audio in case it is shorter than the video using stream_loop -1
    # We set background music volume to 10% (0.1)
    if has_audio:
        # Mix original audio (100% volume) and background music (10% volume)
        filter_str = "[0:a]volume=1.0[a0];[1:a]volume=0.1[a1];[a0][a1]amix=inputs=2:duration=first[a]"
        ffmpeg_cmd = [
            "ffmpeg", "-i", video_path, "-stream_loop", "-1", "-i", temp_audio,
            "-filter_complex", filter_str,
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-shortest", "-y", temp_output
        ]
    else:
        # Just add background music at 10% volume
        ffmpeg_cmd = [
            "ffmpeg", "-i", video_path, "-stream_loop", "-1", "-i", temp_audio,
            "-filter_complex", "[1:a]volume=0.1[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-shortest", "-y", temp_output
        ]

    print(f"Running ffmpeg command: {' '.join(ffmpeg_cmd)}")
    try:
        subprocess.run(ffmpeg_cmd, check=True)
        print("ffmpeg processing completed successfully.")
        # Replace the original file with the processed file
        os.replace(temp_output, video_path)
        print(f"Successfully updated video with background music: {video_path}")
        return True
    except Exception as e:
        print(f"Error mixing audio with ffmpeg: {e}")
        if os.path.exists(temp_output):
            os.remove(temp_output)
        return False
    finally:
        # Clean up temp audio
        if os.path.exists(temp_audio):
            os.remove(temp_audio)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 add_music.py <video_path>")
        sys.exit(1)
    video_path = sys.argv[1]
    success = add_background_music(video_path)
    if not success:
        sys.exit(1)
