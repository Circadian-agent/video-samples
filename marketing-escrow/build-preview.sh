#!/bin/sh
# Make a portfolio preview for AI Freelance Hub's 8:5 video cards.
# Preserve the entire 9:16 picture, timing and original audio with side margins.
# Run from this directory; requires ffmpeg with libx264.
set -eu
"${FFMPEG:-ffmpeg}" -y -i escrow-vertical-sample.mp4 \
  -map 0:v:0 -map 0:a:0 \
  -vf 'scale=540:960:flags=lanczos,pad=1536:960:(ow-iw)/2:0:color=0x25211d,setsar=1' \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -c:a copy -movflags +faststart escrow-portfolio-preview.mp4
