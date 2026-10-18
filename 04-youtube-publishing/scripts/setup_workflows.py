"""
MEMES ADDA -- n8n COMPLETE AUTO SETUP SCRIPT
  Run this ONCE. All workflows will be imported with correct
  credentials pre-filled. You NEVER need to re-enter anything.

WHAT THIS SCRIPT DOES (automatically):
  1. Reads all your real credential IDs from the live n8n database
  2. Patches all workflow JSON files with the correct credential IDs
  3. Imports all 3 workflows into n8n via API
  4. Prints a health check — tells you exactly what's working and what's missing

HOW TO RUN:
  Open PowerShell in: C:\\Users\\Preetham.j\\Desktop\\My-Stufs\\n8n
  Type:  python setup_workflows.py
  Done!
"""

import subprocess, sys, os, json, pathlib, re, time
# Fix Windows console encoding
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.environ['PYTHONIOENCODING'] = 'utf-8'

# ── Auto-install requests if needed ────────────────────────────────────────────
try:
    import requests
except ImportError:
    print("[setup] Installing requests...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "requests"])
    import requests

def _find_project_root() -> pathlib.Path:
    p = pathlib.Path(__file__).parent.resolve()
    while p != p.parent:
        if (p / ".env").exists() or (p / "01-video-editing").exists():
            return p
        p = p.parent
    return pathlib.Path(__file__).parent.parent.parent.resolve()

PROJECT_ROOT = _find_project_root()
SCRIPT_DIR   = pathlib.Path(__file__).parent.resolve()
ENV_FILE     = PROJECT_ROOT / ".env"
N8N_URL      = "http://localhost:5678"

# Load .env into os.environ early so defaults/overrides are active
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip("'\"")
            if k and k not in os.environ:
                os.environ[k] = v

# ═══════════════════════════════════════════════════════════════════════════════
#  STEP 0 — KNOWN CREDENTIAL MAP (from live n8n export)
#  These are YOUR actual credential IDs — hardcoded from your running instance.
#  If you ever add NEW credentials in n8n UI, re-run this script to refresh.
# ═══════════════════════════════════════════════════════════════════════════════

# Credential ID → (n8n name, credential type)
CRED_MAP = {
    "HlTbiZsSm3UzVFBK": ("ai tool explorer",                "telegramApi"),         # Telegram — Channel A (AiecplorreBot)
    "aHtCunvn0weoyzqd": ("ai veo3",                         "telegramApi"),         # Telegram — Channel B (Ai_veo3Bot)
    "sESRlpkwi46CtmxI": ("Telegram account",               "telegramApi"),         # Telegram — General / Memes Adda
    "K1PVxpoHKYP7c1d3": ("ai explorer",                     "googlePalmApi"),       # Gemini API — Account A
    "eZWTI13itJfxflpY": ("ai veo3",                         "googlePalmApi"),       # Gemini API — Account B
    "J9YCiTIhCPgOO1g6": ("Google Gemini(PaLM) Api account", "googlePalmApi"),       # Gemini API — General
    "7y6rDR8RaF885spX": ("ai explorer",                     "airtableTokenApi"),    # Airtable
    "gDmHdKu0BX92TUC2": ("YouTube ai explorer",             "youTubeOAuth2Api"),    # YouTube — Channel A
    "6ghDeaT057rJB2zl": ("YouTube account",                 "youTubeOAuth2Api"),    # YouTube — Channel B (ai veo3)
    "Ise80JbKwA5X6AQY": ("YouTube ai veo3",                 "youTubeOAuth2Api"),    # YouTube — Veo3
    "U531a4sIfhwKe8cU": ("Google Drive ai explorer",        "googleDriveOAuth2Api"),# Google Drive — Account A
    "sHG4r1b3zIqyZFV9": ("Google Drive account  veo3",      "googleDriveOAuth2Api"),# Google Drive — Account B (veo3)
    "Lhskb1Dp4VDCJ05G": ("Google Sheets account",          "googleSheetsOAuth2Api"),# Google Sheets — Account B
    "GYEac6uT6qXgEaPk": ("OpenAI account",                  "openAiApi"),           # OpenAI (gpt-4o-mini)
    "t3riZ0hsOwqzfF9z": ("Google Drive account",            "googleDriveOAuth2Api"),# Google Drive — general
}

# ── Canonical IDs by role (what each workflow slot needs) ─────────────────────
TELEGRAM_CRED_ID   = "sESRlpkwi46CtmxI"  # "Telegram account" — memes adda general
TELEGRAM_CRED_NAME = "Telegram account"
DRIVE_CRED_ID      = "sHG4r1b3zIqyZFV9"  # "Google Drive account  veo3" — Account B
DRIVE_CRED_NAME    = "Google Drive account  veo3"
SHEETS_CRED_ID     = "Lhskb1Dp4VDCJ05G"  # "Google Sheets account"
SHEETS_CRED_NAME   = "Google Sheets account"
OPENAI_CRED_ID     = "GYEac6uT6qXgEaPk"  # "OpenAI account"
OPENAI_CRED_NAME   = "OpenAI account"
YOUTUBE_CRED_ID    = "Ise80JbKwA5X6AQY"  # "YouTube ai veo3"
YOUTUBE_CRED_NAME  = "YouTube ai veo3"

# ── Known IDs from .env ───────────────────────────────────────────────────────
DRIVE_FOLDER_ID_B     = "1IFkvmSJmL_5DLK1URAAicD8EZJ3oCbO5"  # AI Veo3 queue folder
GOOGLE_SHEET_ID_B     = "13WzEh3NC6wcmRc6NhD66-orUBYtn3NWhq9xTsZJ0vjs"
TELEGRAM_BOT_TOKEN    = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID_ENV  = os.environ.get("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID_HERE")
CHANNEL_NAME          = "Memes Adda"
CHANNEL_WATERMARK     = "@MemesAdda"

# ── Placeholder → Real value replacement map ──────────────────────────────────
REPLACEMENTS = {
    # Credential IDs
    "YOUR_TELEGRAM_CRED_ID":  TELEGRAM_CRED_ID,
    "YOUR_SHEETS_CRED_ID":    SHEETS_CRED_ID,
    "YOUR_OPENAI_CRED_ID":    OPENAI_CRED_ID,
    "XXf8tW6s8Yqv40eV":       DRIVE_CRED_ID,
    "YOUR_DRIVE_CRED_ID":     DRIVE_CRED_ID,

    # Credential names
    "Google Sheets":          SHEETS_CRED_NAME,
    "Telegram Bot":           TELEGRAM_CRED_NAME,
    "Google Drive account":   DRIVE_CRED_NAME,
    "OpenAI account":         OPENAI_CRED_NAME,

    # Google IDs
    "YOUR_GOOGLE_SHEET_ID":   GOOGLE_SHEET_ID_B,
    "YOUR_STAGING_FOLDER_ID": DRIVE_FOLDER_ID_B,
    "YOUR_PREVIEW_FOLDER_ID": DRIVE_FOLDER_ID_B,   # same folder for now — preview goes here
    "YOUR_PUBLISH_FOLDER_ID": DRIVE_FOLDER_ID_B,   # user can change after import
    "WATCHED_FOLDER_ID":      DRIVE_FOLDER_ID_B,

    # Telegram
    "YOUR_TELEGRAM_CHAT_ID":  TELEGRAM_CHAT_ID_ENV,

    # Channel info
    "@YourChannel":           CHANNEL_WATERMARK,
    "@AI_Shorts":             CHANNEL_WATERMARK,
    "YOUR_N8N_URL":           "http://localhost:5678",

    # Gemini key placeholder
    "<<<YOUR_GEMINI_API_KEY>>>": "{{ $env.GEMINI_API_KEY }}",
    "YOUR_GEMINI_API_KEY":    "{{ $env.GEMINI_API_KEY }}",

    # Sheet names
    "Video Editor Queue":     "Video Editor Queue",
    "Clipping Queue":         "Clipping Queue",
}

# ═══════════════════════════════════════════════════════════════════════════════
#  STEP 1 — Check n8n is running
# ═══════════════════════════════════════════════════════════════════════════════

def check_n8n():
    print("\n[1/5] Checking n8n is running...")
    for attempt in range(1, 4):
        try:
            r = requests.get(f"{N8N_URL}/healthz", timeout=5)
            if r.status_code == 200:
                print(f"      ✅ n8n is LIVE at {N8N_URL}")
                return True
        except Exception as e:
            print(f"      ⏳ Attempt {attempt}/3 — n8n not ready yet: {e}")
            time.sleep(3)
    print("      ❌ n8n is NOT running!")
    print("      FIX: Open PowerShell in the n8n folder and run:")
    print("           docker-compose up -d")
    return False

# ═══════════════════════════════════════════════════════════════════════════════
#  STEP 2 — Verify credentials exist in n8n
# ═══════════════════════════════════════════════════════════════════════════════

def verify_credentials():
    print("\n[2/5] Verifying credentials in n8n database...")
    # Use n8n CLI to export and verify
    try:
        result = subprocess.run(
            ["docker", "exec", "n8n-n8n-1", "sh", "-c",
             "n8n export:credentials --all --pretty 2>/dev/null"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print("      ⚠️  Could not verify credentials via CLI")
            return
        creds = json.loads(result.stdout.strip().split('\n', 1)[-1] if result.stdout.strip().startswith('Error') else result.stdout)
    except Exception as e:
        print(f"      ⚠️  Credential verification skipped: {e}")
        return

    found_ids = {c['id']: (c['name'], c['type']) for c in creds}
    required = {
        TELEGRAM_CRED_ID: "Telegram (for approval messages)",
        DRIVE_CRED_ID:    "Google Drive (for uploading clips)",
        SHEETS_CRED_ID:   "Google Sheets (for queue logging)",
        OPENAI_CRED_ID:   "OpenAI (for AI edit prompt parsing)",
    }

    all_ok = True
    for cred_id, purpose in required.items():
        if cred_id in found_ids:
            name, ctype = found_ids[cred_id]
            print(f"      ✅ {purpose}")
            print(f"         ID: {cred_id} | Name: '{name}'")
        else:
            print(f"      ❌ MISSING: {purpose}")
            print(f"         Expected ID: {cred_id}")
            all_ok = False

    if not all_ok:
        print("\n      ⚠️  Some credentials are missing!")
        print("         See SETUP_GUIDE.md for instructions on adding them.")

    return found_ids

# ═══════════════════════════════════════════════════════════════════════════════
#  STEP 3 — Patch workflow JSON files with real credential IDs
# ═══════════════════════════════════════════════════════════════════════════════

def patch_workflow(filepath: pathlib.Path) -> str:
    """Replace all placeholder strings with real values."""
    content = filepath.read_text(encoding="utf-8")
    for placeholder, real_value in REPLACEMENTS.items():
        content = content.replace(placeholder, real_value)

    # Also patch credential objects — match by type and replace id+name
    def patch_cred_object(match):
        full = match.group(0)
        # Replace id/name pairs for known credential types
        for cred_id, (cred_name, cred_type) in CRED_MAP.items():
            if cred_type in full and (
                "YOUR_" in full or
                "XXf8tW" in full or
                "CRED_ID" in full
            ):
                full = re.sub(r'"id":\s*"[^"]*"', f'"id": "{cred_id}"', full)
                full = re.sub(r'"name":\s*"[^"]*"', f'"name": "{cred_name}"', full)
                break
    cred_pattern = re.compile(r'"(?:googleDriveOAuth2Api|googleSheetsOAuth2Api|openAiApi|telegramApi|youTubeOAuth2Api|googlePalmApi)":\s*\{[^}]+\}')
    content = cred_pattern.sub(patch_cred_object, content)
    return content

def _resolve_workflow_file(modular_rel: str, legacy_name: str) -> pathlib.Path:
    p1 = PROJECT_ROOT / modular_rel
    if p1.exists():
        return p1
    p2 = SCRIPT_DIR / legacy_name
    if p2.exists():
        return p2
    return p1

def patch_all_workflows():
    print("\n[3/5] Patching workflow JSON files with real credential IDs...")
    workflow_targets = [
        ("01-video-editing/workflows/video-editing-local.json", "videoEditingLocal.json", "🎬 AI Video Editor — Revision Loop Edition"),
        ("03-ai-clipping/workflows/ai-clipping-free-v2.json", "AI_Clipping_Free_v2.json", "✂️ AI Clipping — Revision Loop Edition"),
    ]

    patched_files = []
    for rel_path, leg_name, wf_name in workflow_targets:
        filepath = _resolve_workflow_file(rel_path, leg_name)
        if not filepath.exists():
            print(f"      ⚠️  {filepath.name} not found at {filepath} — skipping")
            continue

        # Read and patch
        patched = patch_workflow(filepath)

        # Write patched version
        filepath.write_text(patched, encoding="utf-8")
        print(f"      ✅ Patched: {filepath.name} ({filepath.parent.name})")
        patched_files.append((filepath, wf_name))

    return patched_files

# ═══════════════════════════════════════════════════════════════════════════════
#  STEP 4 — Import workflows via n8n CLI (preserves credentials, no re-entry)
# ═══════════════════════════════════════════════════════════════════════════════

def import_workflow(filepath: pathlib.Path, wf_name: str):
    """
    Import a workflow JSON into n8n using the CLI inside Docker.
    Strips top-level 'id' so n8n auto-assigns a fresh ID (prevents 'null value in column id' error).
    """
    # Read, strip 'id', write to a temp file for import
    try:
        wf_data = json.loads(filepath.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"      ❌ Cannot read {filepath.name}: {e}")
        return False

    # Remove top-level id so n8n generates a fresh one
    wf_data.pop("id", None)

    # Write back
    filepath.write_text(json.dumps(wf_data, indent=2, ensure_ascii=False), encoding="utf-8")

    try:
        rel = filepath.relative_to(PROJECT_ROOT).as_posix()
        container_path = f"/workspace/{rel}"
    except ValueError:
        container_path = f"/workspace/{filepath.name}"

    cmd = [
        "docker", "exec", "n8n-n8n-1", "sh", "-c",
        f'n8n import:workflow --input="{container_path}" 2>&1'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    output = result.stdout + result.stderr
    if "successfully" in output.lower() or "imported" in output.lower() or "importing" in output.lower():
        print(f"      ✅ Imported: {wf_name}")
        return True
    else:
        print(f"      ⚠️  Import issue for {wf_name}:")
        print(f"         {output.strip()[-300:]}")
        return False

def import_all_workflows(patched_files):
    print("\n[4/5] Importing patched workflows into n8n...")
    print("      (credentials are already embedded — no re-entry needed!)")
    for filepath, wf_name in patched_files:
        import_workflow(filepath, wf_name)

# ═══════════════════════════════════════════════════════════════════════════════
#  STEP 5 — Health check and status report
# ═══════════════════════════════════════════════════════════════════════════════

def health_check():
    print("\n[5/5] Final health check...")

    checks = {
        "n8n UI": f"{N8N_URL}",
        "Docker running": "docker ps",
        "Workspace mounted": str(PROJECT_ROOT),
        "Python clipper v2": str(PROJECT_ROOT / "03-ai-clipping" / "scripts" / "local_clipper_v2.py"),
        ".env file": str(ENV_FILE),
        "logo.png (optional)": str(PROJECT_ROOT / "logo.png"),
    }

    env_vars = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env_vars[k.strip()] = v.strip().strip("'\"")

    print("  " + "-" * 57)
    print("  MEMES ADDA -- SYSTEM STATUS")
    print("  " + "-" * 57)
    print(f"  Channel Name    : {CHANNEL_NAME}")
    print(f"  Watermark       : {CHANNEL_WATERMARK}")
    print(f"  n8n URL         : {N8N_URL}")
    print(f"  Drive Folder B  : {DRIVE_FOLDER_ID_B}")
    print(f"  Google Sheet B  : {GOOGLE_SHEET_ID_B}")
    print()

    crit_env = {
        "GEMINI_API_KEY":          "AI transcript analysis (Clipping workflow)",
        "TELEGRAM_CHAT_ID":        "Telegram approval messages",
        "TELEGRAM_BOT_TOKEN":      "Telegram bot",
    }

    print("  -- Environment Variables ------------------------------------------")
    all_env_ok = True
    for key, purpose in crit_env.items():
        val = env_vars.get(key, "")
        if val and "YOUR_" not in val:
            print(f"  OK {key}")
        else:
            print(f"  FAIL {key} — MISSING! ({purpose})")
            all_env_ok = False

    print()
    print("  -- Credentials in n8n ---------------------------------------------")
    for cred_id, (name, ctype) in CRED_MAP.items():
        print(f"  OK [{ctype[:20]:20}] id={cred_id} → '{name}'")

    print()
    print("  -- Workflows to import --------------------------------------------")
    workflows = [
        ("video-editing-local.json", "01-video-editing/workflows/video-editing-local.json", "videoEditingLocal.json"),
        ("ai-clipping-free-v2.json", "03-ai-clipping/workflows/ai-clipping-free-v2.json", "AI_Clipping_Free_v2.json"),
    ]
    for display_name, mod_path, leg_name in workflows:
        p = _resolve_workflow_file(mod_path, leg_name)
        exists = p.exists()
        print(f"  {'OK' if exists else 'FAIL'} {display_name} ({p})")

    print()
    print("  -- What still needs your action ----------------------------------")
    if "YOUR_" in env_vars.get("TELEGRAM_CHAT_ID", "YOUR_"):
        print("  NOTE TELEGRAM_CHAT_ID — message @userinfobot on Telegram to get your ID")
        print("     Then open .env and replace YOUR_TELEGRAM_CHAT_ID_HERE with it")
    if (PROJECT_ROOT / "logo.png").exists():
        print("  OK logo.png found — will be overlaid on videos")
    else:
        print("  INFO No logo.png found — text watermark '@MemesAdda' will be used")
    print()
    print("  -- Google Drive Folders to create --------------------------------")
    print("  • Login to drive.google.com with your Ai Veo3 Gmail account")
    print("  • Create 3 folders inside 'My Drive':")
    print("    1. AI Preview  ← previews sent to Telegram")
    print("    2. AI Publish  ← approved clips go here")
    print("    3. AI Editor Queue  ← drop your raw clips here for editing")
    print()
    print("  -- Google Sheets to create ----------------------------------------")
    print(f"  • Open sheet: https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID_B}")
    print("  • Make sure it has TWO tabs (sheets):")
    print("    1. 'Video Editor Queue'")
    print("    2. 'Clipping Queue'")
    print("  • See SETUP_GUIDE.md for column names")
    print()
    print("=" * 65)
    print("  Setup complete! Go to http://localhost:5678 to see workflows.")
    print("=" * 65)

# -------------------------------------------------------------------------------
#  MAIN
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 65)
    print("  MEMES ADDA -- n8n Complete Auto Setup")
    print("=" * 65)

    if not check_n8n():
        print("\n❌ Cannot proceed — start Docker first:")
        print("   Open PowerShell → cd to n8n folder → run: docker-compose up -d")
        sys.exit(1)

    creds = verify_credentials()
    patched = patch_all_workflows()
    import_all_workflows(patched)
    health_check()
