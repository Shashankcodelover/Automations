# ============================================================
#   SOCIAL MEDIA AUTOMATION HUB  —  n8n Workspace
#   Channel A (Personal)  &  Channel B (AI Generated)
# ============================================================

## 📁 PROJECT STRUCTURE

```
n8n-automation/
│
├── 01-video-editing/          ← 🎬 Video stitching, cropping, music, captions
│   ├── workflows/             (2 n8n workflow JSONs: cloud + local)
│   ├── scripts/               (add_music.py, replace_audio.py)
│   └── guides/                (FFmpeg commands, editing how-tos)
│
├── 02-ai-video-generation/    ← 🤖 VEO 3 + Vertex AI cinematic video gen
│   ├── workflows/             (1 n8n workflow JSON)
│   └── guides/                (VEO 3 prompt guide)
│
├── 03-ai-clipping/            ← 🎞️ YouTube → AI-detected viral Shorts
│   ├── workflows/             (2 n8n workflow JSONs: full + free)
│   ├── scripts/               (local_clipper.py, local_clipper_v2.py)
│   └── output/                (generated clips output directory)
│
├── 04-youtube-publishing/     ← 📤 Auto-publish to YouTube (Channel A + B)
│   ├── workflows/             (6 n8n workflow JSONs)
│   ├── scripts/               (cloud_publisher.py, token gen, setup)
│   └── guides/                (publish guide, upload config)
│
├── infra/                     ← 🐳 Docker, deployment, credentials
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── guides/                (cloud deployment, credentials, config)
│   └── tokens/                (OAuth tokens — gitignored)
│
├── docs/                      ← 📚 Project-wide documentation
│   └── explainer.md           (tech stack & architecture explainer)
│
└── archive/                   ← 🗄️ Deprecated / old experiments (gitignored)
```

---

## THE FULL CONNECTED PIPELINE

  ╔════════════════════════════════════════════════════════════╗
  ║  CHANNEL A — Your Own Recorded Videos                      ║
  ║  (01-video-editing → Folder A → 04-youtube-publishing)     ║
  ╚═══════════════════════════╦════════════════════════════════╝
                              ║
  ╔═══════════════════════════╩════════════════════════════════╗
  ║  MODULE 01  —  Video Editing                               ║
  ║  1. Grab Video Clips from Airtable                         ║
  ║  2. Stitches clips + transitions + background music        ║
  ║  3. Submagic adds big bold captions (or local FFmpeg)      ║
  ║                                                            ║
  ║  🚦 GATE 1: Telegram preview of output video               ║
  ║            (Approve → Uploads to Drive Folder A)           ║
  ╚═══════════════════════════╦════════════════════════════════╝
                              ║
  ╔═══════════════════════════╩════════════════════════════════╗
  ║  MODULE 04  —  Publish Channel A                           ║
  ║  1. Google Drive Trigger watches Folder A                  ║
  ║  2. Gemini generates highly engaging visual tags           ║
  ║  3. Pollinations.ai generates emotional shock thumbnail    ║
  ║                                                            ║
  ║  🚦 GATE 2: Telegram metadata preview (Title, Tags, Thumb) ║
  ║            (Approve → Posts immediately to Channel A)      ║
  ╚════════════════════════════════════════════════════════════╝

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ╔════════════════════════════════════════════════════════════╗
  ║  CHANNEL B — AI Generated VEO 3 Videos                     ║
  ║  (02-ai-video-generation → Folder B → 04-youtube-publishing)║
  ╚═══════════════════════════╦════════════════════════════════╝
                              ║
  ╔═══════════════════════════╩════════════════════════════════╗
  ║  MODULE 02  —  AI Video Generation (VEO 3)                 ║
  ║  1. Gemini generates idea + VEO 3 prompt                   ║
  ║  2. Vertex AI generates 8-second cinematic video           ║
  ║                                                            ║
  ║  🚦 GATE 1: Telegram preview of generated AI video         ║
  ║            (Approve → Saves to Sheet + uploads Folder B)   ║
  ╚═══════════════════════════╦════════════════════════════════╝
                              ▼
  ╔═══════════════════════════╩════════════════════════════════╗
  ║  MODULE 04  —  Publish Channel B                           ║
  ║  1. Google Drive Trigger watches Folder B                  ║
  ║  2. Gemini generates cinematic tags + VEO 3 credit text    ║
  ║  3. Pollinations.ai generates dramatic movie-style thumb   ║
  ║                                                            ║
  ║  🚦 GATE 2: Telegram metadata preview (Title, Tags, Thumb) ║
  ║            (Approve → Posts immediately to Channel B)      ║
  ╚════════════════════════════════════════════════════════════╝

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ╔════════════════════════════════════════════════════════════╗
  ║  STANDALONE — AI Clipping (YouTube → Viral Shorts)         ║
  ║  (03-ai-clipping module)                                   ║
  ╚═══════════════════════════╦════════════════════════════════╝
                              ║
  ╔═══════════════════════════╩════════════════════════════════╗
  ║  MODULE 03  —  AI Clipping Automation                      ║
  ║  1. Input: Long YouTube video URL                          ║
  ║  2. AI detects most viral 30-60s segments                  ║
  ║  3. Clips + crops to 9:16 vertical                         ║
  ║  4. Auto-publishes to TikTok, Instagram, YouTube Shorts    ║
  ╚════════════════════════════════════════════════════════════╝

---

## 🔑 CONFIGURATION
For credential setup and copy-paste values:
👉 **[config-checklist.txt](infra/guides/config-checklist.txt)**
👉 **[credentials-setup.txt](infra/guides/credentials-setup.txt)**

---

## 🚨 ERROR HANDLING
All workflows are protected by an ELI5 error handling engine:
- If *any* error happens, n8n catches it.
- Gemini translates the dry code error stack trace into simple, human words.
- Telegram notifies your phone: "⚠️ VEO 3 workflow failed because your credentials expired. Please generate a new Bearer token."
