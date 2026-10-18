#!/usr/bin/env python3
"""
AI Video Clipper v2 — MASSIVE Edition
=======================================
100% Free  |  Zero Re-Setup  |  Resume-Safe

WHAT'S NEW vs v1:
  ✅ Styled DIALOGUE CAPTIONS burned into every clip
  ✅ SPEED RAMP — 1.07x (punchy pacing + audio frequency shift)
  ✅ LOGO OVERLAY — top-right corner (logo.png or @Channel text)
  ✅ HUE SHIFT — subtle +5° hue + saturation boost (unique fingerprint,
                 defeats YouTube/TikTok automated content-ID matching)
  ✅ Still 100% local FFmpeg, no paid APIs

USAGE:
  python local_clipper_v2.py "YOUTUBE_URL" [number_of_clips]

OUTPUT:
  clips/vertical_clip_1.mp4  (9:16, captions, watermark, speed-ramped)
  clips/vertical_clip_2.mp4
  clips/metadata.json         (title, caption, hashtags, timestamps)
"""

# ── 0. Auto-install missing libraries ─────────────────────────────────────────
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

# ── 1. Imports ─────────────────────────────────────────────────────────────────
import re, json, time, pathlib, textwrap, shutil
import google.generativeai as genai

# ── 2. Load .env ───────────────────────────────────────────────────────────────
SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()

def _find_env_file():
    """Walk up from the script directory to find the nearest .env file."""
    search = SCRIPT_DIR
    for _ in range(10):
        candidate = search / ".env"
        if candidate.exists():
            return candidate
        parent = search.parent
        if parent == search:
            break
        search = parent
    return None

ENV_FILE = _find_env_file()

def load_env():
    if ENV_FILE is None:
        print(f"[ERROR] .env not found in any parent directory of {SCRIPT_DIR}")
        print("Create a .env file in the project root with:  GEMINI_API_KEY=your_key_here")
        sys.exit(1)
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key  = key.strip()
            val  = val.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = val

load_env()

GEMINI_KEY    = os.environ.get("GEMINI_API_KEY", "")
OPENAI_KEY    = os.environ.get("OPENAI_API_KEY", "")  # optional fallback
CHANNEL_NAME  = os.environ.get("CHANNEL_WATERMARK", "@AI_Shorts")

if not GEMINI_KEY or GEMINI_KEY in ("your_gemini_api_key_here", "YOUR_GEMINI_API_KEY"):
    print(f"[ERROR] GEMINI_API_KEY not set in {ENV_FILE}")
    sys.exit(1)

print(f"[ok] Credentials loaded. Channel watermark: {CHANNEL_NAME}")
genai.configure(api_key=GEMINI_KEY)
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
MODEL = genai.GenerativeModel(MODEL_NAME)

# ── 3. WebVTT → clean transcript ───────────────────────────────────────────────
def parse_vtt(vtt_path: str) -> list:
    """
    Parse .vtt file.
    Returns list of dicts: {start_sec, end_sec, text}
    """
    path = pathlib.Path(vtt_path)
    if not path.exists():
        return []

    # e.g.  00:01:23.456 --> 00:01:27.890
    time_re = re.compile(
        r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s-->\s(\d{2}):(\d{2}):(\d{2})\.(\d{3})"
    )
    tag_re  = re.compile(r"<[^>]+>")
    lines   = path.read_text(encoding="utf-8").splitlines()
    entries = []
    cur_start = cur_end = None

    def to_sec(h, m, s, ms):
        return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000.0

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = time_re.match(line)
        if m:
            cur_start = to_sec(m.group(1), m.group(2), m.group(3), m.group(4))
            cur_end   = to_sec(m.group(5), m.group(6), m.group(7), m.group(8))
            i += 1
            text_parts = []
            while i < len(lines) and lines[i].strip():
                clean = tag_re.sub("", lines[i]).strip()
                if clean:
                    text_parts.append(clean)
                i += 1
            if text_parts and cur_start is not None:
                text = " ".join(dict.fromkeys(text_parts))  # deduplicate
                entries.append({"start_sec": cur_start, "end_sec": cur_end, "text": text})
        else:
            i += 1
    return entries

def entries_to_transcript(entries: list) -> str:
    """Human-readable timestamped transcript for AI prompt."""
    def fmt(s):
        h = int(s // 3600)
        m = int((s % 3600) // 60)
        sec = int(s % 60)
        return f"{h:02d}:{m:02d}:{sec:02d}"
    parts = []
    for e in entries:
        parts.append(f"[{fmt(e['start_sec'])}] {e['text']}")
    return "\n".join(parts)

# ── 4. Gemini: find viral moments ──────────────────────────────────────────────
def find_viral_moments(transcript: str, num_clips: int) -> list:
    """
    Asks Gemini to find the best N self-contained viral moments.
    Avoids: intros, outros, "thank you for watching", generic greetings.
    Returns list of dicts with start_time, end_time, title, caption, hashtags.
    """
    prompt = textwrap.dedent(f"""
        You are the world's #1 viral short-form video editor and social media growth strategist.
        Analyze this TIMESTAMPED video transcript and select the {num_clips} BEST viral moments.

        ════════════════════════════════════
        STRICT SELECTION RULES:
        ════════════════════════════════════
        ✅ Each clip MUST be 30-90 seconds long
        ✅ Must start with a STRONG HOOK (surprising fact, question, or powerful statement)
        ✅ Must be 100% self-contained (makes sense without watching the rest)
        ✅ Must have high emotional intensity: shock, curiosity, inspiration, or humor

        ❌ NEVER pick:
           - "Thank you for watching", "don't forget to subscribe", "like and share"
           - Generic intros ("Hey everyone, today we'll...")
           - Outro scenes, sponsor plugs, or vague filler content
           - Clips that reference earlier/later parts ("as I showed before", "coming up next")

        ════════════════════════════════════
        OUTPUT FORMAT — RAW JSON ONLY:
        ════════════════════════════════════
        No markdown, no backticks, no explanation. Just a raw JSON array.
        Each item MUST have EXACTLY these keys:
          start_time  — "HH:MM:SS" (beginning of the hook)
          end_time    — "HH:MM:SS" (natural sentence end, 30-90s later)
          title       — max 60 chars, punchy, viral, use emoji if it helps
          caption     — social media caption, 2-3 emojis, 100-150 chars
          hashtags    — 5-7 relevant hashtags + #shorts #viral

        TRANSCRIPT:
        {transcript[:15000]}
    """)

    for attempt in range(1, 4):
        try:
            resp = MODEL.generate_content(prompt)
            raw  = resp.text.strip()
            # Strip code fences if model adds them
            raw  = re.sub(r"^```[a-z]*\s*", "", raw, flags=re.I)
            raw  = re.sub(r"\s*```$",        "", raw, flags=re.I)
            raw  = raw.strip()
            data = json.loads(raw)
            if isinstance(data, list) and len(data) > 0:
                return data[:num_clips]
            raise ValueError("Empty result list")
        except Exception as e:
            print(f"  [Gemini attempt {attempt}/3 failed] {e}")
            if attempt < 3:
                time.sleep(4)

    raise RuntimeError("Gemini failed to produce valid clip timestamps after 3 attempts.")

# ── 5. Build SRT subtitle file for a clip ─────────────────────────────────────
def build_srt_for_clip(entries: list, clip_start_sec: float, clip_end_sec: float,
                        srt_path: pathlib.Path):
    """
    Extract subtitle lines that fall within [clip_start_sec, clip_end_sec],
    shift timestamps to be relative to clip_start_sec, save as .srt.
    """
    def sec_to_srt(s):
        h = int(s // 3600)
        m = int((s % 3600) // 60)
        sec = s % 60
        ms  = int((sec - int(sec)) * 1000)
        return f"{h:02d}:{m:02d}:{int(sec):02d},{ms:03d}"

    relevant = [
        e for e in entries
        if e["end_sec"] > clip_start_sec and e["start_sec"] < clip_end_sec
    ]

    if not relevant:
        srt_path.write_text("", encoding="utf-8")
        return False

    lines = []
    for idx, e in enumerate(relevant, 1):
        s = max(0.0, e["start_sec"] - clip_start_sec)
        en = max(0.0, e["end_sec"]  - clip_start_sec)
        lines.append(str(idx))
        lines.append(f"{sec_to_srt(s)} --> {sec_to_srt(en)}")
        lines.append(e["text"])
        lines.append("")

    srt_path.write_text("\n".join(lines), encoding="utf-8")
    return True

# ── 6. Process one clip — download, crop, captions, effects ───────────────────
def process_clip(youtube_url: str, moment: dict, index: int,
                 out_dir: pathlib.Path, subtitle_entries: list,
                 logo_path: pathlib.Path) -> dict:
    """
    Full pipeline for one viral clip:
      A) Download exact time range with yt-dlp
      B) Build SRT subtitle file for this clip
      C) FFmpeg: 9:16 crop + speed ramp (1.07x) + caption burn-in +
                 logo/watermark overlay + hue/saturation shift
    """
    start  = moment["start_time"]
    end    = moment["end_time"]
    title  = moment.get("title", f"Clip {index}")
    temp   = out_dir / f"_raw_{index}.mp4"
    srt    = out_dir / f"_subs_{index}.srt"
    output = out_dir / f"vertical_clip_{index}.mp4"

    # ── Resume: skip if already done ────────────────────────────────────────
    if output.exists() and output.stat().st_size > 100_000:
        print(f"  [skip] Clip {index} already exists → {output.name}")
        return {"clip_path": str(output), **moment}

    print(f"\n  ▶ Clip {index}: '{title}'  ({start} → {end})")

    # ── A: Download section only ──────────────────────────────────────────────
    if temp.exists():
        temp.unlink()

    dl_cmd = [
        sys.executable, "-m", "yt_dlp",
        "--download-sections", f"*{start}-{end}",
        "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
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
            subprocess.run(dl_cmd, check=True, timeout=300)
            if temp.exists() and temp.stat().st_size > 10_000:
                break
            raise RuntimeError("Downloaded file too small")
        except Exception as e:
            print(f"    [download attempt {attempt}/3] {e}")
            if attempt == 3:
                raise RuntimeError(f"Could not download clip {index}.")
            time.sleep(6)

    # ── B: Build SRT subtitle file ────────────────────────────────────────────
    def ts_to_sec(ts: str) -> float:
        parts = ts.split(":")
        return int(parts[0])*3600 + int(parts[1])*60 + float(parts[2])

    clip_start_sec = ts_to_sec(start)
    clip_end_sec   = ts_to_sec(end)
    has_subs = build_srt_for_clip(subtitle_entries, clip_start_sec, clip_end_sec, srt)

    # ── C: Build FFmpeg filter graph ──────────────────────────────────────────
    # Layer 1 — Scale + pad to 1080×1920 (9:16 vertical)
    # Layer 2 — Speed ramp: 1.07× (punchy pace + audio freq shift bypasses content-ID)
    # Layer 3 — Hue shift: +5° hue, +10% saturation (unique visual fingerprint)
    # Layer 4 — Caption burn-in: styled yellow bold text, black outline
    # Layer 5 — Watermark: logo.png top-right, or drawtext fallback

    speed = 1.07

    # Base video filter chain
    vf_parts = [
        # Crop to 9:16 vertical
        "scale=iw*min(1080/iw\\,1920/ih):ih*min(1080/iw\\,1920/ih),"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,setsar=1",
        # Speed ramp
        f"setpts=PTS/{speed}",
        # Slight hue shift for uniqueness
        "hue=h=5:s=1.1",
    ]

    # Caption burn-in (if we have subtitles)
    if has_subs and srt.exists() and srt.stat().st_size > 10:
        # Use FFmpeg subtitles filter with styled ASS-style inline options
        srt_escaped = str(srt).replace("\\", "/").replace(":", "\\:")
        # Style: large bold yellow with black outline, center-bottom
        sub_style = (
            "FontName=Arial,FontSize=58,Bold=1,"
            "PrimaryColour=&H0000FFFF,"   # Yellow (ABGR format)
            "OutlineColour=&H00000000,"   # Black outline
            "BackColour=&H80000000,"      # Semi-transparent background box
            "Outline=3,Shadow=2,"
            "Alignment=2,"               # Center-bottom
            "MarginV=80"                  # 80px from bottom
        )
        vf_parts.append(f"subtitles='{srt_escaped}':force_style='{sub_style}'")

    vf_filter = ",".join(vf_parts)

    # Audio filter: match speed
    af_filter = f"atempo={speed}"

    # Watermark overlay
    if logo_path.exists():
        print(f"    [logo] Using {logo_path.name}")
        ff_cmd = [
            "ffmpeg", "-y",
            "-i", str(temp),
            "-i", str(logo_path),
            "-filter_complex",
            (
                f"[0:v]{vf_filter}[base];"
                f"[1:v]scale=160:-1[logo];"
                f"[base][logo]overlay=W-w-20:20[outv];"
                f"[0:a]{af_filter}[outa]"
            ),
            "-map", "[outv]",
            "-map", "[outa]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "128k",
            str(output),
        ]
    else:
        # Text watermark fallback
        watermark_text = CHANNEL_NAME.replace("'", "")
        wm_filter = (
            f"drawtext=text='{watermark_text}':"
            f"fontsize=36:fontcolor=white@0.75:"
            f"x=W-text_w-20:y=20:"
            f"box=1:boxcolor=0x00000066:boxborderw=8:"
            f"shadowcolor=black:shadowx=2:shadowy=2"
        )
        ff_cmd = [
            "ffmpeg", "-y",
            "-i", str(temp),
            "-vf", f"{vf_filter},{wm_filter}",
            "-af", af_filter,
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "128k",
            str(output),
        ]

    print(f"    [ffmpeg] Encoding with captions + watermark + speed ramp...")
    try:
        result = subprocess.run(ff_cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, ff_cmd, result.stdout, result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"    [FFmpeg error] Trying simplified fallback...")
        print(f"    stderr: {e.stderr[-500:] if e.stderr else 'none'}")
        # Simplified fallback — just vertical crop, speed, watermark
        simple_vf = (
            f"scale=iw*min(1080/iw\\,1920/ih):ih*min(1080/iw\\,1920/ih),"
            f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,setsar=1,"
            f"setpts=PTS/{speed},"
            f"hue=h=5:s=1.1,"
            f"drawtext=text='{CHANNEL_NAME.replace(chr(39), '')}':"
            f"fontsize=36:fontcolor=white@0.75:x=W-text_w-20:y=20:"
            f"box=1:boxcolor=0x00000066:boxborderw=8"
        )
        ff_fallback = [
            "ffmpeg", "-y",
            "-i", str(temp),
            "-vf", simple_vf,
            "-af", af_filter,
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "128k",
            str(output),
        ]
        subprocess.run(ff_fallback, check=True, timeout=600)

    # Cleanup temp files
    for f in [temp, srt]:
        if f.exists():
            f.unlink()

    size_mb = output.stat().st_size / 1_048_576
    print(f"  ✓ Saved → {output.name}  ({size_mb:.1f} MB)")
    return {"clip_path": str(output), **moment}

# ── 7. Main ────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: python local_clipper_v2.py <YOUTUBE_URL> [num_clips]")
        sys.exit(1)

    youtube_url = sys.argv[1].strip()
    num_clips   = max(1, min(5, int(sys.argv[2]) if len(sys.argv) > 2 else 3))
    out_dir     = SCRIPT_DIR / "clips"
    out_dir.mkdir(exist_ok=True)

    logo_path = SCRIPT_DIR / "logo.png"
    if logo_path.exists():
        print(f"[logo] Found logo.png — will overlay on clips")
    else:
        print(f"[logo] No logo.png found — using text watermark: {CHANNEL_NAME}")

    print(f"\n{'='*65}")
    print(f"  🎬 AI Clipper v2 — MASSIVE Edition")
    print(f"  URL:      {youtube_url}")
    print(f"  Clips:    {num_clips}")
    print(f"  Output:   {out_dir}")
    print(f"  Features: Captions ✅ | Speed 1.07x ✅ | Hue-shift ✅ | Logo ✅")
    print(f"{'='*65}\n")

    # ── STEP 1: Download subtitles only (fast, ~2s) ───────────────────────────
    print("[1/4] Downloading subtitles (no video download)...")
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
    try:
        subprocess.run(sub_cmd, check=True, timeout=60)
    except Exception as e:
        print(f"[WARN] Auto-subtitle download failed: {e}")
        print("       Will continue without subtitles...")

    vtt_file = next((str(p) for p in out_dir.glob("_subs*.vtt")), None)
    subtitle_entries = []
    if vtt_file:
        print("[2a] Parsing subtitle entries...")
        subtitle_entries = parse_vtt(vtt_file)
        pathlib.Path(vtt_file).unlink(missing_ok=True)
        print(f"     Found {len(subtitle_entries)} subtitle lines")
    else:
        print("[2a] No subtitles found — clips will have no captions")

    # ── STEP 2: Build transcript for Gemini ───────────────────────────────────
    print("[2/4] Building transcript for AI analysis...")
    transcript = entries_to_transcript(subtitle_entries)
    if len(transcript) < 100:
        print("[WARN] Very short or empty transcript. Gemini will have limited context.")

    print(f"      Transcript: {len(transcript):,} chars, {len(subtitle_entries)} lines")

    # ── STEP 3: Ask Gemini for viral moments ──────────────────────────────────
    print(f"\n[3/4] Asking Gemini to find the {num_clips} best viral moments...")
    try:
        moments = find_viral_moments(transcript, num_clips)
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    print(f"\n  🧠 Gemini selected {len(moments)} viral moments:")
    for i, m in enumerate(moments, 1):
        print(f"     {i}. {m['title']}")
        print(f"        {m['start_time']} → {m['end_time']}")

    # ── STEP 4: Download + process each clip ──────────────────────────────────
    print(f"\n[4/4] Downloading and processing {len(moments)} clips...")
    results = []
    failed  = 0

    for i, moment in enumerate(moments, 1):
        try:
            result = process_clip(
                youtube_url, moment, i, out_dir,
                subtitle_entries, logo_path
            )
            results.append(result)
        except Exception as e:
            failed += 1
            print(f"  [ERROR] Clip {i} failed: {e}")
            print("          Continuing with remaining clips...")

    # ── Save metadata.json ────────────────────────────────────────────────────
    meta_path = out_dir / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # ── Final summary ─────────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    if results:
        print(f"  ✅ Done! {len(results)} clip(s) ready in: {out_dir}")
        if failed:
            print(f"  ⚠️  {failed} clip(s) failed (see errors above)")
        for r in results:
            p = pathlib.Path(r["clip_path"])
            size_mb = p.stat().st_size / 1_048_576 if p.exists() else 0
            print(f"     📹 {p.name}  ({size_mb:.1f} MB)")
            print(f"        Title: {r.get('title','?')}")
            print(f"        Caption: {r.get('caption','?')[:80]}...")
        print(f"\n  📄 Full metadata → {meta_path}")
    else:
        print("  ❌ No clips were generated. Check errors above.")
    print(f"{'='*65}\n")

if __name__ == "__main__":
    main()
