#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <input.webm> [output.mp4]" >&2
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is required to transcode WebM to MP4." >&2
  echo "Install with Homebrew: brew install ffmpeg" >&2
  exit 1
fi

INPUT="$1"
OUTPUT="${2:-${INPUT%.*}.mp4}"

ffmpeg -y \
  -i "$INPUT" \
  -c:v libx264 \
  -pix_fmt yuv420p \
  -movflags +faststart \
  -an \
  "$OUTPUT"

echo "Wrote $OUTPUT"
