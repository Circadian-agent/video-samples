#!/bin/sh
# Rebuild the escrow sample: 36 s vertical 1080x1920 video + 4-card 1080x1350 image post.
# Needs: Node with playwright (Chromium), python3, ffmpeg with libx264. Fonts load from Google Fonts.
set -e
node grain.cjs                      # static paper grain texture (grain.png)
mkdir -p f
for k in 0 1 2 3; do W=4 K=$k node frames.cjs & done; wait   # 864 frames at 24 fps from render(t) in video.html
python3 music.py                    # original ambient bed, synthesized, no samples or licensed audio
ffmpeg -y -framerate 24 -i f/%05d.jpg -i music.wav -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p \
  -c:a aac -b:a 128k -shortest -movflags +faststart escrow-vertical-sample.mp4
node cards.cjs                      # post-1.png .. post-4.png
