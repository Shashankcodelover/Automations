# 📤 Module 04 — YouTube Auto-Publishing

Google Drive trigger watches folders → Gemini generates SEO tags + description → Pollinations.ai generates thumbnail → Telegram approval gate → YouTube upload.

Supports **two channels**:
- **Channel A** — Personal recorded videos
- **Channel B** — AI-generated VEO 3 content

## Workflows

| File | Description |
|---|---|
| `workflows/publish-channel-a.json` | Publish to Channel A (Personal) |
| `workflows/publish-channel-b.json` | Publish to Channel B (AI Content) |
| `workflows/autopublish.json` | Auto-publish workflow (Channel A) |
| `workflows/autopublish-channel-b.json` | Auto-publish workflow (Channel B) |
| `workflows/queue-mover-channel-b.json` | Queue mover utility for Channel B |
| `workflows/base-workflow.json` | Base/original publish workflow template |

## Scripts

| File | Description |
|---|---|
| `scripts/cloud_publisher.py` | GitHub Actions cloud publisher (24/7 free hosting) |
| `scripts/get_google_token.py` | One-time Google OAuth token generator |
| `scripts/setup_workflows.py` | Automated n8n workflow setup/configuration script |

## Guides

| File | Description |
|---|---|
| `guides/publish-guide.txt` | How-to: Telegram gate, metadata details |
| `guides/youtube-upload-config.txt` | YouTube upload node configuration checklist |

## Pipeline Flow

```
Google Drive Trigger (new file in Folder A or B)
    → Gemini generates engaging tags, title, description
    → Pollinations.ai generates shock/dramatic thumbnail
    → Telegram preview (title + tags + thumbnail)
    → Approved → YouTube Upload → Published!
```
