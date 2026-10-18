# ============================================================
#   AUTOMATION HUB & WORKSPACE
# ============================================================

An enterprise-grade repository of autonomous AI agents, media generation pipelines, and operations tooling.

---

## 📁 REPOSITORY STRUCTURE

```
Automations/
│
├── job-application-filler/    ← 🤖 Autopilot-X Autonomous Application Engine
│   ├── AUTOPILOT_X_GLOBAL_TEMPLATE.md  (Global parameterized agent directive)
│   ├── candidate_profile_sample.json   (Reference data schema)
│   └── README.md                       (Workflow architecture & usage)
│
├── 01-video-editing/          ← 🎬 Video stitching, cropping, music, captions
│   ├── workflows/             (n8n workflow JSONs: cloud + local)
│   ├── scripts/               (add_music.py, replace_audio.py)
│   └── guides/                (FFmpeg commands, editing how-tos)
│
├── 02-ai-video-generation/    ← 🤖 VEO 3 + Vertex AI cinematic video generation
│   ├── workflows/             (n8n workflow JSON)
│   └── guides/                (VEO 3 prompt guide)
│
├── 03-ai-clipping/            ← 🎞️ YouTube → AI-detected viral Shorts
│   ├── workflows/             (n8n workflow JSONs: full + free)
│   └── scripts/               (local_clipper.py, local_clipper_v2.py)
│
├── 04-youtube-publishing/     ← 📤 Auto-publish to YouTube (Channel A + B)
│   ├── workflows/             (n8n publishing & queue workflows)
│   ├── scripts/               (cloud_publisher.py, OAuth setup)
│   └── guides/                (Publish guides & configs)
│
├── infra/                     ← 🐳 Docker, deployment, credentials
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── guides/                (Cloud deployment & config checklists)
│
└── docs/                      ← 📚 Architecture and tech stack explainer
```

---

## 🚀 MODULE BREAKDOWN

### 1. 🤖 [Job Application Filler (Autopilot-X)](./job-application-filler/)
Autonomous career operations engine designed to execute high-precision, zero-defect job applications across modern ATS portals (AshbyHQ, Greenhouse, Lever, Workable, etc.).

**Key Capabilities:**
- **Zero-Blanks Policy:** 100% field occupancy (education, skills, URLs, experience, custom essays).
- **Dual-Source Tracker Hygiene:** Bi-directional sync with Notion API & Google Sheets.
- **Link Verification Protocol:** Validates live URLs via HTTP status check prior to submission.
- **Anti-Bot Human-in-the-Loop:** High-velocity automated pre-fill paired with manual submission confirmation.
- **"Pause & Go" Cadence:** Predictable, transparent status logging before and after each application.

---

### 2. 🎬 [Video Editing Pipeline (01-video-editing)](./01-video-editing/)
Automated video assembly and enhancement engine:
- Fetches source clips from Airtable/Drive.
- Stitches multi-clip sequences with automated transitions and background audio.
- Adds stylized captions via Submagic API or local FFmpeg pipelines.
- Implements human verification gates via Telegram bot before rendering to cloud storage.

---

### 3. 🤖 [AI Video Generation (02-ai-video-generation)](./02-ai-video-generation/)
Cinematic AI video production powered by Google Vertex AI & VEO 3:
- Automated prompt synthesis with Google Gemini.
- High-definition video generation via Vertex AI endpoints.
- Telegram-based preview and approval workflows.

---

### 4. 🎞️ [AI Video Clipping (03-ai-clipping)](./03-ai-clipping/)
Short-form content extraction engine:
- Downloads long-form YouTube source videos.
- Analyzes transcripts and audio dynamics to identify high-engagement segments.
- Crops to 9:16 vertical ratio and exports ready-to-publish Shorts/Reels/TikToks.

---

### 5. 📤 [YouTube Auto-Publisher (04-youtube-publishing)](./04-youtube-publishing/)
Multi-channel automated social distribution:
- Watches designated cloud storage folders for approved video files.
- Generates SEO-optimized titles, descriptions, and tag sets using Gemini.
- Synthesizes custom visual thumbnails via Pollinations.ai.
- Publishes directly to YouTube channels with full analytics tracking.

---

## 🛠️ INFRASTRUCTURE & ORCHESTRATION

- **Orchestrator:** n8n Workflow Automation (Dockerized)
- **Deployment:** Docker & docker-compose configurations in [`infra/`](./infra/)
- **AI Models:** Google Gemini, Vertex AI (VEO 3), Claude, LangGraph
- **Languages & Frameworks:** Python 3.11+, Node.js, Shell, FFmpeg
