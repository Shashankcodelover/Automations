#!/usr/bin/env python3
"""
AI Video Clipper — 100% Free, Zero Re-Setup
============================================
Run once: python local_clipper.py "YOUTUBE_URL" [clip_count]

HOW CREDENTIALS WORK:
  All keys are read from the .env file sitting next to this script.
  You set them ONE TIME. After that, re-run the script as many times as
  you want — no re-entering, no re-initializing, no credential dialogs.

DEPENDENCIES (auto-installed on first run):
  yt-dlp, google-generativeai

WHAT IT DOES:
  1. Downloads only subtitles (2 secs, no full video)
  2. Sends transcript to Gemini (free) → finds 2-3 viral hooks
  3. Downloads only those exact sections
  4. Crops each to 9:16 vertical using FFmpeg
  5. Saves vertical_clip_1.mp4, vertical_clip_2.mp4 ...
  6. Saves metadata.json with captions + hashtags ready to paste

RESUME SAFETY:
  If it crashes mid-way, re-running picks up where it left off.
  Already-finished clips are not re-downloaded.
"""

# ── 0. Auto-install missing libraries ────────────────────────────────────────
import subprocess, sys, os

# Fix Windows console encoding for emojis
if hasattr(sys.stdout, 'reconfigure'): 
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.environ['PYTHONIOENCODING'] = 'utf-8'


def _ensure(pkg, import_name=None):
    import_name = import_name or pkg
    try:
        __import__(import_name)
    except ImportError:
        print(f"[setup] Installing {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])

_ensure("yt-dlp", "yt_dlp")
_ensure("google-generativeai", "google.generativeai")

# ── 1. Imports after auto-install ─────────────────────────────────────────────
import re, json, time, pathlib, textwrap
import google.generativeai as genai

# ── 2. Load .env file (ONE-TIME SETUP, never ask again) ──────────────────────
SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()

def _find_env_file():
    """Walk up from the script directory to find the nearest .env file."""
    search = SCRIPT_DIR
    for _ in range(10):  # max 10 levels up
        candidate = search / ".env"
        if candidate.exists():
            return candidate
        parent = search.parent
        if parent == search:
            break  # reached filesystem root
        search = parent
    return None

ENV_FILE = _find_env_file()

def load_env():
    """
    Reads KEY=VALUE lines from .env found by walking up parent directories.
    Lines starting with # are comments. Blank lines are skipped.
    Values already in os.environ take priority (Docker / system env).
    """
    if ENV_FILE is None:
        print(f"""
[ERROR] .env file not found in any parent directory of:
  {SCRIPT_DIR}

Create a .env file in the project root with:

  GEMINI_API_KEY=your_gemini_api_key_here

Get a free Gemini key at: https://aistudio.google.com/apikey
""")
        sys.exit(1)

    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key  = key.strip()
            val  = val.strip().strip('"').strip("'")
            # System/Docker env takes priority; file fills everything else
            if key not in os.environ:
                os.environ[key] = val

load_env()
print(f"[ok] Credentials loaded from {ENV_FILE}")

# ── 3. Validate required keys right away ─────────────────────────────────────
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")

if not GEMINI_KEY or GEMINI_KEY in ("your_gemini_api_key_here", "YOUR_GEMINI_API_KEY"):
    print(f"""
[ERROR] GEMINI_API_KEY is not set or still has the placeholder value.

Open the .env file at:
  {ENV_FILE}

And replace the placeholder with your real key:
  GEMINI_API_KEY=AIzaSy...

Get a free key at: https://aistudio.google.com/apikey
""")
    sys.exit(1)

print(f"[ok] Credentials loaded from {ENV_FILE}")

# ── 4. Configure Gemini once ──────────────────────────────────────────────────
genai.configure(api_key=GEMINI_KEY)
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
MODEL = genai.GenerativeModel(MODEL_NAME)

# ── 5. Helper: parse WebVTT subtitles ─────────────────────────────────────────
def parse_vtt(vtt_path: str) -> str:
    """Returns a clean, timestamped transcript string from a .vtt file."""
    path = pathlib.Path(vtt_path)
    if not path.exists():
        return ""

    time_re = re.compile(r"(\d{2}:\d{2}:\d{2})\.\d{3}\s-->\s\d{2}:\d{2}:\d{2}\.\d{3}")
    tag_re   = re.compile(r"<[^>]+>")
    seen_text = set()
    parts = []
    cur_ts = ""

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.isdigit() or line.startswith("WEBVTT") or ":" not in line and len(line) < 4:
            continue
        m = time_re.match(line)
        if m:
            cur_ts = m.group(1)
            continue
        clean = tag_re.sub("", line).strip()
        if clean and clean not in seen_text:
            seen_text.add(clean)
            parts.append(f"[{cur_ts}] {clean}")

    return "\n".join(parts)

# ── 6. Gemini: find viral moments (with retry) ───────────────────────────────
def find_viral_moments(transcript: str, num_clips: int) -> list:
    """
    Asks Gemini to pick the best N viral segments.
    Retries up to 3 times if the response is not valid JSON.
    Returns a list of dicts: {start_time, end_time, title, caption, hashtags}
    """
    prompt = textwrap.dedent(f"""
        You are an expert viral video editor and social media growth strategist.
        Analyze this timestamped video transcript and pick the {num_clips} most
        engaging, self-contained viral moments (each 30-60 seconds long).
        Choose moments with a strong hook at the start.

        Reply ONLY with a raw JSON array — no markdown, no backticks, no explanation.
        Each item must have exactly these keys:
          start_time  (HH:MM:SS)
          end_time    (HH:MM:SS)
          title       (max 50 chars, punchy)
          caption     (social media caption with 2-3 emojis)
          hashtags    (#tag1 #tag2 #tag3 #shorts #viral)

        TRANSCRIPT:
        {transcript[:12000]}
    """)

    for attempt in range(1, 4):
        try:
            resp = MODEL.generate_content(prompt)
            raw  = resp.text.strip()
            # Strip any accidental code fences
            raw  = re.sub(r"^```[a-z]*\s*", "", raw, flags=re.I)
            raw  = re.sub(r"\s*```$",        "", raw, flags=re.I)
            data = json.loads(raw)
            if isinstance(data, list) and data:
                return data
            raise ValueError("Gemini returned an empty list")
        except Exception as e:
            print(f"  [Gemini attempt {attempt}/3 failed] {e}")
            if attempt < 3:
                time.sleep(3)

    raise RuntimeError("Gemini could not produce valid clip timestamps after 3 attempts.")

# ── 7. Download + crop one clip (resume-safe) ─────────────────────────────────
def process_clip(youtube_url: str, moment: dict, index: int, out_dir: pathlib.Path) -> dict:
    start  = moment["start_time"]
    end    = moment["end_time"]
    title  = moment.get("title", f"Clip {index}")
    temp   = out_dir / f"_temp_clip_{index}.mp4"
    output = out_dir / f"vertical_clip_{index}.mp4"

    # ── Resume: skip if already done ────────────────────────────────────────
    if output.exists() and output.stat().st_size > 50_000:
        print(f"  [skip] Clip {index} already exists → {output.name}")
        return {"clip_path": str(output), **moment}

    print(f"\n  ▶ Clip {index}: '{title}' ({start} → {end})")

    # ── Step A: download section ──────────────────────────────────────────────
    if temp.exists():
        temp.unlink()

    dl_cmd = [
        sys.executable, "-m", "yt_dlp",
        "--download-sections", f"*{start}-{end}",
        "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]",
        "--merge-output-format", "mp4",
        "--no-playlist",
        "--retries", "5",
        "--fragment-retries", "10",
        "--quiet",
        "-o", str(temp),
        youtube_url,
    ]

    for attempt in range(1, 4):
        try:
            subprocess.run(dl_cmd, check=True)
            if temp.exists() and temp.stat().st_size > 10_000:
                break
            raise RuntimeError("Downloaded file is too small or missing")
        except Exception as e:
            print(f"    [download attempt {attempt}/3] {e}")
            if attempt == 3:
                raise RuntimeError(f"Could not download clip {index} after 3 attempts.")
            time.sleep(5)

    # ── Step B: FFmpeg → vertical 9:16 center-crop ───────────────────────────
    ff_cmd = [
        "ffmpeg", "-y",
        "-i", str(temp),
        "-vf", (
            "scale=iw*min(1080/iw\\,1920/ih):ih*min(1080/iw\\,1920/ih),"
            "pad=1080:1920:(1080-iw)/2:(1920-ih)/2:black,"
            "crop=1080:1920"
        ),
        "-c:v", "libx264", "-crf", "22", "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
        str(output),
    ]

    try:
        subprocess.run(ff_cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"    [FFmpeg fallback] Primary filter failed, trying simple center crop...")
        # Simple fallback filter
        ff_fallback = [
            "ffmpeg", "-y",
            "-i", str(temp),
            "-vf", "crop=in_h*9/16:in_h",
            "-c:v", "libx264", "-crf", "22", "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k",
            str(output),
        ]
        subprocess.run(ff_fallback, check=True)

    # ── Cleanup temp ─────────────────────────────────────────────────────────
    if temp.exists():
        temp.unlink()

    print(f"  ✓ Saved → {output.name}")
    return {"clip_path": str(output), **moment}

# ── 8. Main entry point ───────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage:  python local_clipper.py <YOUTUBE_URL> [number_of_clips]")
        print("Example: python local_clipper.py https://youtu.be/abc123 3")
        sys.exit(1)

    youtube_url = sys.argv[1].strip()
    num_clips   = max(1, min(5, int(sys.argv[2]) if len(sys.argv) > 2 else 3))

    # Output folder: clips/ next to the script
    out_dir = SCRIPT_DIR / "clips"
    out_dir.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  AI Clipper — Starting")
    print(f"  URL:   {youtube_url}")
    print(f"  Clips: {num_clips}")
    print(f"  Out:   {out_dir}")
    print(f"{'='*60}\n")

    # ── STEP 1: Download subtitles only ──────────────────────────────────────
    print("[1/4] Downloading subtitles (no video)...")
    vtt_stem = str(out_dir / "_subs")
    sub_cmd = [
        sys.executable, "-m", "yt_dlp",
        "--write-auto-subs",
        "--skip-download",
        "--sub-lang", "en",
        "--sub-format", "vtt",
        "--quiet",
        "-o", vtt_stem,
        youtube_url,
    ]
    subprocess.run(sub_cmd, check=True)

    vtt_file = next((str(p) for p in out_dir.glob("_subs*.vtt")), None)
    if not vtt_file:
        print("[ERROR] No English subtitles found for this video.")
        print("        Try a video with auto-generated captions enabled.")
        sys.exit(1)

    # ── STEP 2: Parse transcript ──────────────────────────────────────────────
    print("[2/4] Parsing transcript...")
    transcript = parse_vtt(vtt_file)
    pathlib.Path(vtt_file).unlink(missing_ok=True)

    if len(transcript) < 200:
        print("[ERROR] Transcript is too short or empty. Cannot find viral moments.")
        sys.exit(1)

    print(f"      Transcript length: {len(transcript):,} characters")

    # ── STEP 3: Ask Gemini for viral moments ─────────────────────────────────
    print(f"[3/4] Asking Gemini to find the {num_clips} best viral moments...")
    try:
        moments = find_viral_moments(transcript, num_clips)
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    print(f"      Gemini found {len(moments)} moments:")
    for i, m in enumerate(moments, 1):
        print(f"        {i}. {m['title']}  ({m['start_time']} → {m['end_time']})")

    # ── STEP 4: Download + crop each clip ────────────────────────────────────
    print(f"\n[4/4] Downloading & cropping {len(moments)} clips to vertical 9:16...")
    results  = []
    failed   = 0

    for i, moment in enumerate(moments, 1):
        try:
            result = process_clip(youtube_url, moment, i, out_dir)
            results.append(result)
        except Exception as e:
            failed += 1
            print(f"  [ERROR] Clip {i} failed: {e}")
            print(f"          Continuing with remaining clips...")

    # ── Save metadata.json ────────────────────────────────────────────────────
    meta_path = out_dir / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    if results:
        print(f"  ✅ Done! {len(results)} clip(s) saved to: {out_dir}")
        print(f"  📄 Metadata + captions → {meta_path.name}")
        if failed:
            print(f"  ⚠️  {failed} clip(s) failed (see errors above)")
        for r in results:
            p = pathlib.Path(r["clip_path"])
            size_mb = p.stat().st_size / 1_048_576 if p.exists() else 0
            print(f"     • {p.name}  ({size_mb:.1f} MB)  ← {r['title']}")
    else:
        print("  ❌ No clips were generated. Check errors above.")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
