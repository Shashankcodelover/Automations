# 🤖 Module 02 — AI Video Generation (VEO 3 / Vertex AI)

Gemini generates creative ideas + VEO 3 prompt → Vertex AI generates cinematic 8-second AI videos → Telegram approval gate → Google Drive upload.

## Workflows

| File | Description |
|---|---|
| `workflows/veo3-automation.json` | n8n workflow — full VEO 3 AI video generation pipeline |

## Guides

| File | Description |
|---|---|
| `guides/veo3-guide.txt` | How-to: prompts, GCP credit rotation, Vertex AI setup |

## Pipeline Flow

```
Gemini (idea + prompt) → Vertex AI VEO 3 (8-sec cinematic video)
    → Telegram preview gate → Approved → Google Sheets log + Drive Folder B
```

## Prerequisites

- Google Cloud Platform project with Vertex AI API enabled
- Service Account Key JSON for Vertex AI authentication
- GCP credits (free tier or billing enabled)
