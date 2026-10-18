# 🎬 Module 01 — Video Editing & Clipping

Takes raw video clips from Airtable → stitches, crops, adds background music & captions → produces finished YouTube Shorts.

## Workflows

| File | Description |
|---|---|
| `workflows/video-editing-cloud.json` | n8n workflow — cloud clip editor (fal.ai + Submagic captions) |
| `workflows/video-editing-local.json` | n8n workflow — 100% free local FFmpeg editor |

## Scripts

| File | Description |
|---|---|
| `scripts/add_music.py` | Overlay background music on clipped videos |
| `scripts/replace_audio.py` | Replace or adjust audio tracks in videos |

## Guides

| File | Description |
|---|---|
| `guides/video-editing-guide.txt` | How-to: timeline, cuts, music workflow |
| `guides/ffmpeg-commands.txt` | Copy-paste FFmpeg command reference |
| `guides/sample-timeline.txt` | Sample timeline overlay data for text overlays |

## Pipeline Flow

```
Airtable (raw clips) → n8n workflow → FFmpeg stitch + transitions + music
    → Submagic captions (cloud) or local FFmpeg → Telegram preview gate
    → Approved → Upload to Google Drive Folder A
```
