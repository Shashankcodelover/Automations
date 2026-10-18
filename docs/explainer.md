# EXPLAINER: AI Video Clipping & YouTube Auto-Publishing Automation (n8n)

## 1. Project Overview & "In and Out" (ELI15/20)
This project is an **automated social media factory**. It automates the process of taking long videos, finding the most engaging parts, clipping them, adding background music, editing the audio/video to look high-quality, and scheduling them for publication on YouTube.
- **In**: A long video file or link is input.
- **Processing**: 
  1. The **n8n engine** coordinates the tasks.
  2. **Python scripts** run locally using `ffmpeg` to clip segments, adjust volume levels, add background tracks, and stitch the outputs together.
  3. JSON metadata caches the state of what has been edited and published.
- **Out**: High-quality clipped videos (Shorts or Reels) uploaded and published to social media channels via the Google/YouTube APIs.

---

## 2. Tech Stack & Decision Analysis (Why this, not that?)

| Component | Technology | Why we chose it | Why NOT the alternatives? |
| :--- | :--- | :--- | :--- |
| **Workflow Manager** | **n8n** (Dockerized) | Node-based visual automation engine. Handles webhooks, scheduled triggers, database connections, and Google OAuth flow out of the box with auto-retries on API failures. | **Pure Node.js/Cron**: Writing code to manage YouTube auth refresh tokens, API retry headers, and visual flowcharts requires thousands of lines of boilerplate. |
| **Video Engine** | **FFmpeg & Moviepy** (Python) | Industry-standard command-line tool for video compression, slicing, and stitching. Python's wrappers make it easy to programmatically edit media. | **JS Media libraries**: Node video libraries are mostly wrapper stubs around FFmpeg anyways, but Python offers native scientific support for array operations on video frames. |
| **Deployment** | **Docker Compose** | Bundles n8n, local executors, and python dependencies into isolation, ensuring the setup runs identical locally and on cloud servers. | **Manual setup**: Installing specific FFmpeg codec libraries, python dependencies, and node binaries globally leads to version collision errors. |

---

## 3. 10x Upgrade Blueprint (Developing to Version 8.0 - 10.0)

To take this local clipping setup into a high-scale SaaS automation pipeline:

### A. Core Upgrades
1. **AI Viral Detection (Whisper + GPT)**: Run long video audio through OpenAI's `Whisper` to get transcripts. Feed transcripts to GPT to locate high-impact quotes or highlights based on sentiment.
2. **Auto-Subtitles Overlay**: Use Python's `moviepy` combined with subtitle configurations to render animated word-by-word captions on screen dynamically.
3. **Queue Scalability (Celery + Redis)**: Queue heavy rendering jobs on distributed compute nodes so multiple videos can compile in parallel without locking the database thread.

### B. Upgraded Code structure & Backend Logic
Here is the upgraded Python script block showing automated Whisper transcript-based highlight clipping:

```python
# n8n-automation/advanced_clipper.py
import subprocess
import json
import os

class AIClipperEngine:
    def __init__(self, input_video: str, output_dir: str):
        self.input_video = input_video
        self.output_dir = output_dir

    def extract_audio(self, audio_output: str):
        # Extract audio stream fast for transcription using FFmpeg
        cmd = f'ffmpeg -y -i "{self.input_video}" -ab 160k -ac 2 -ar 44100 -vn "{audio_output}"'
        subprocess.run(cmd, shell=True, check=True)

    def parse_transcripts_for_highlights(self, transcript_json: str) -> list:
        # Scan transcript timestamps for viral markers or high-impact sentences
        with open(transcript_json, 'r') as f:
            data = json.load(f)
        
        highlights = []
        for segment in data.get("segments", []):
            text = segment.get("text", "").lower()
            # Simple viral phrase keyword detection
            if any(kw in text for kw in ["shocking", "secret", "never", "insane", "how to"]):
                highlights.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"]
                })
        return highlights

    def render_clip(self, start: float, duration: float, clip_index: int):
        # Slice video segment using fast copy seek flags
        output_file = os.path.join(self.output_dir, f"highlight_{clip_index}.mp4")
        cmd = f'ffmpeg -y -ss {start} -i "{self.input_video}" -t {duration} -c:v libx264 -crf 23 -c:a aac "{output_file}"'
        subprocess.run(cmd, shell=True, check=True)
        print(f"Rendered clip: {output_file}")
```
