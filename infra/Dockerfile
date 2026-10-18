# ============================================================
#  STAGE 1: Builder
#  Installs FFmpeg, Python, pip, yt-dlp, and AI libraries.
#  Gathers all binary dependencies and library paths.
# ============================================================
FROM alpine:3.19 AS builder

RUN apk add --no-cache \
    ffmpeg \
    python3 \
    py3-pip \
    fontconfig \
    ttf-dejavu \
    font-noto \
    font-noto-emoji \
    bash

RUN pip3 install --no-cache-dir --break-system-packages \
    yt-dlp \
    google-generativeai \
    requests

# Create target directories
RUN mkdir -p /dist/usr/bin /dist/usr/lib /dist/lib /dist/usr/share /dist/etc

# Copy main binaries/scripts
RUN cp -P /usr/bin/ffmpeg /dist/usr/bin/ && \
    cp -P /usr/bin/ffprobe /dist/usr/bin/ && \
    cp -P /usr/bin/python3* /dist/usr/bin/ && \
    cp -P /usr/bin/yt-dlp* /dist/usr/bin/

# Copy python library directories
RUN cp -r /usr/lib/python3.11 /dist/usr/lib/

# Copy fonts configuration
RUN cp -r /usr/share/fonts /dist/usr/share/ && \
    cp -r /etc/fonts /dist/etc/

# Copy all shared libraries they depend on dynamically
RUN for bin in /usr/bin/ffmpeg /usr/bin/ffprobe /usr/bin/python3; do \
      for lib in $(ldd $bin | tr -s ' \t' '\n' | grep '^/'); do \
        if [ -f "$lib" ]; then \
          real_lib=$(realpath "$lib"); \
          mkdir -p "/dist$(dirname "$real_lib")"; \
          cp -P "$real_lib" "/dist$real_lib" 2>/dev/null || true; \
          if [ "$lib" != "$real_lib" ]; then \
            mkdir -p "/dist$(dirname "$lib")"; \
            cp -P "$lib" "/dist$lib" 2>/dev/null || true; \
          fi; \
        fi; \
      done; \
    done

# ============================================================
#  STAGE 2: n8n final image (Hardened Alpine, no apk)
#  Copies the entire gathered root structure.
# ============================================================
FROM docker.n8n.io/n8nio/n8n:latest

USER root

# Copy everything gathered in Stage 1 directly to root
COPY --from=builder /dist/ /

# ── Create workspace + clips output directories ─────────────
RUN mkdir -p /workspace/clips && \
    chown -R node:node /workspace

# ── Verify everything is installed correctly ────────────────
RUN ffmpeg -version 2>&1 | head -3 && \
    ffprobe -version 2>&1 | head -1 && \
    python3 --version && \
    python3 -c "import yt_dlp; print('yt-dlp is working!')" && \
    echo "✅ All tools verified — image is ready"

USER node

# n8n listens on 5678 by default
EXPOSE 5678
