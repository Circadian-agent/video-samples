#!/bin/sh
# Rebuild lesson06-sample.mp4: narration (Piper TTS), screen recording (Playwright), subtitles and mux (ffmpeg).
# Needs: piper + zh_CN-huayan-medium voice, ffmpeg with libx264/libass, Node with playwright, a CJK font.
set -e
i=0
for line in $(node -e 'require("./segs.json").forEach(s=>console.log(encodeURIComponent(s.tts)))'); do
  node -e "process.stdout.write(decodeURIComponent('$line'))" | piper --model zh_CN-huayan-medium.onnx --length_scale 1.1 --sentence_silence 0.3 --output_file seg$i.wav
  i=$((i+1))
done
OUT=$(node rec.cjs)                # {"start": seconds of page load to trim, "file": recorded webm}
START=$(echo "$OUT" | node -pe 'JSON.parse(require("fs").readFileSync(0)).start')
WEBM=$(echo "$OUT" | node -pe 'JSON.parse(require("fs").readFileSync(0)).file')
ffmpeg -f lavfi -i anullsrc=r=22050:cl=mono -t 1.0 sil_lead.wav
ffmpeg -f lavfi -i anullsrc=r=22050:cl=mono -t 0.6 sil_gap.wav
printf 'file sil_lead.wav\n' > concat.txt
for n in 0 1 2 3 4; do printf 'file seg%s.wav\nfile sil_gap.wav\n' $n >> concat.txt; done
ffmpeg -f concat -safe 0 -i concat.txt -af "apad=pad_dur=1.2,loudnorm=I=-16" -ar 48000 voice.wav
ffmpeg -ss "$START" -i "$WEBM" -i voice.wav \
  -vf "subtitles=lesson06.zh-Hant.srt:force_style='FontName=WenQuanYi Zen Hei,FontSize=15,BorderStyle=3,Outline=6,BackColour=&H80000000,MarginV=28'" \
  -c:v libx264 -crf 20 -pix_fmt yuv420p -r 30 -c:a aac -b:a 160k -shortest -movflags +faststart lesson06-sample.mp4
