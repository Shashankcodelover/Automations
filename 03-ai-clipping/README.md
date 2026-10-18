# AI Clipping Automation Setup Guide

This guide explains how to configure and run the full auto clipping automation workflow (`AI_Clipping_Automation_Full.json`) and the 100% free local alternative (`local_clipper.py`).

---

## 🚨 CRITICAL SECURITY ALERT: API KEY ROTATION
Your Google Doc exposed a live Blotato API key in plain text:
`blt_+2CW6mMdXpNWuKUuzr/Sw2Z2MjIx1zQlH+wqX6PK2l8=`

**Action Required**:
1. Log into your **Blotato Dashboard**.
2. Revoke/Delete this API key immediately.
3. Generate a new API key to use in your local environment setup.

---

## 🔑 SETUP STEP 1: CONFIGURE PERSISTENT CREDENTIALS (NO MORE RE-IMPORT BREAKS!)
Workflows usually lose credentials when you re-import or update them. To solve this, our new workflow (`AI_Clipping_Automation_Full.json`) reads credentials directly from **Environment Variables** (variables configured in your system or n8n settings). 

### How to set up variables:
If you are self-hosting n8n using Docker (as indicated by the `docker-compose.yml` in this workspace):
1. Open your `docker-compose.yml` file.
2. In the `environment:` section of your `n8n` service, append the following keys:
   ```yaml
   environment:
     - KLAP_API_KEY=your_new_klap_api_key
     - BLOTATO_API_KEY=your_new_blotato_api_key
     - TIKTOK_ACCOUNT_ID=your_tiktok_blotato_account_id
     - INSTAGRAM_ACCOUNT_ID=your_instagram_blotato_account_id
     - YOUTUBE_ACCOUNT_ID=your_youtube_blotato_account_id
   ```
3. Restart your containers to apply changes:
   ```bash
   docker compose down
   docker compose up -d
   ```

*Note: If you run n8n directly on Windows via command line (NPM), open PowerShell and set them before launching n8n:*
```powershell
$env:KLAP_API_KEY="your_key"
$env:BLOTATO_API_KEY="your_key"
$env:TIKTOK_ACCOUNT_ID="your_id"
$env:INSTAGRAM_ACCOUNT_ID="your_id"
$env:YOUTUBE_ACCOUNT_ID="your_id"
n8n
```
Once configured, the workflow nodes will automatically read these variables, and you will **never** have to re-enter them in n8n again.

---

## 📋 SETUP STEP 2: GOOGLE SHEETS QUEUE & DUPLICATE PREVENTION
The workflow can trigger automatically when you paste a YouTube link into a spreadsheet.

1. Create a Google Sheet.
2. Add these columns on the first row:
   `youtube_url`, `clip_count`, `status`, `timestamp`
3. Open `AI_Clipping_Automation_Full.json` in n8n:
   - Click on the `n1-sheet-trigger` (On Sheet Row Added) and select your Google Sheets credential.
   - Click on the `n19-log` (Save Shorts Log) node, select your Google Sheets credential, paste your spreadsheet URL or ID, and map the columns.
4. Whenever you add a new row with a YouTube URL, n8n will automatically run the clipping pipeline, create the shorts, schedule them, and log the output.

---

## 🤖 SETUP STEP 3: AUTO-PILOT RSS TRIGGER (TRENDING TECH NEWS)
We have added a schedule-based auto-trigger to the workflow:
- The **Daily Schedule** trigger fires once a day.
- It pulls the latest tech/coding video from Fireship's YouTube RSS feed.
- It validates the URL, verifies that it hasn't been clipped before, and runs the clipping and posting pipeline automatically.
- To use it: simply toggle the workflow to **Active** inside n8n.

---

## 💻 100% FREE LOCAL ALTERNATIVE (`local_clipper.py`)
If you run out of free trial credits on Klap or Blotato, you can clip and reframe long YouTube videos into vertical shorts **completely free of cost forever** directly on your computer.

### How it works:
1. It downloads only the video subtitles (.vtt file) via `yt-dlp` (takes 1–2 seconds, no video downloaded).
2. It sends the timestamped transcript to Google Gemini (`gemini-2.0-flash`, which has a very large free tier).
3. Gemini identifies the 3 most viral hooks/segments (30–60s) with precise timestamps.
4. The script uses `yt-dlp`'s partial-download feature to download **only** those specific segments (very fast).
5. It crops the video from 16:9 widescreen to 9:16 vertical using local FFmpeg and saves it.

### Setup and execution:
1. Install Python dependencies:
   ```bash
   pip install yt-dlp google-generativeai
   ```
2. Obtain a free Gemini API key from [Google AI Studio](https://aistudio.google.com).
3. Set your environment variable:
   - On Windows (PowerShell):
     ```powershell
     $env:GEMINI_API_KEY="AIzaSy..."
     ```
   - On Linux/Mac:
     ```bash
     export GEMINI_API_KEY="AIzaSy..."
     ```
4. Run the script:
   ```bash
   python local_clipper.py "https://www.youtube.com/watch?v=VIDEO_ID" 3
   ```
   * Replace `VIDEO_ID` with your target YouTube URL.
   * `3` is the number of shorts you want to generate.
5. The script outputs:
   - `vertical_clip_1.mp4`
   - `vertical_clip_2.mp4`
   - `vertical_clip_3.mp4`
   - A JSON output printout containing AI-generated social captions, titles, and hashtags for each clip.
