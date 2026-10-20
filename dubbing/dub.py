"""Dub a short video segment line by line, timed to the original speech.

usage: python dub.py SOURCE plan.json VOICE.onnx OUTDIR

plan.json: {"start": s, "end": s, "lang": "es", "glossary": [...],
            "lines": [{"start": s, "end": s, "en": "...", "<lang>": ["full", "shorter", ...]}]}
Set "lang" to pick which translation key to dub (this sample has "es" and "de").
Line times are absolute source times. Each line's candidates are tried in order:
the first one that fits its slot (with at most MAX_TEMPO speed-up) is used.
"""
import json, os, subprocess, sys, wave
import numpy as np

SR = 48000
MAX_TEMPO = 1.15      # most we speed up a voice line before rephrasing
GAP = 0.15            # silence kept before the next speaker line
PAD = 0.08            # pad around original speech when muting it
MAX_OVERRUN = 0.6     # most a line may run past the original line end (stays close to the picture)
DUCK = 0.3            # original sound level under dubbed speech that runs into a pause


def sh(*a):
    subprocess.run(a, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def read_pcm(path, channels):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", str(channels),
                          "-ar", str(SR), "-"], check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, channels).copy()


def tts(text, voice, out, tempo=1.0):
    tmp = out + ".raw.wav"
    subprocess.run([os.path.join(os.path.dirname(sys.executable), "piper"), "-m", voice, "-f", tmp],
                   input=text.encode(), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # trim leading/trailing silence so the line starts on its first word
    flt = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
           "silenceremove=start_periods=1:start_threshold=-45dB,areverse")
    if tempo != 1.0:
        flt += f",atempo={tempo:.4f}"
    sh("ffmpeg", "-y", "-i", tmp, "-af", flt, "-ar", str(SR), "-ac", "1", out)
    os.remove(tmp)
    with wave.open(out) as w:
        return w.getnframes() / w.getframerate()


def srt_time(t):
    ms = round(t * 1000)
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def main(src, plan_path, voice, outdir):
    plan = json.load(open(plan_path))
    os.makedirs(outdir, exist_ok=True)
    work = os.path.join(outdir, "work")
    os.makedirs(work, exist_ok=True)
    t0, t1 = plan["start"], plan["end"]
    seg = os.path.join(work, "segment.mp4")
    sh("ffmpeg", "-y", "-ss", str(t0), "-i", src, "-t", str(t1 - t0), "-c:v", "libx264", "-crf", "20",
       "-preset", "fast", "-c:a", "pcm_s16le", "-ar", str(SR), seg.replace(".mp4", ".mkv"))
    seg = seg.replace(".mp4", ".mkv")
    orig = read_pcm(seg, 2)
    n = len(orig)
    dub = np.zeros(n, dtype=np.float32)
    gain = np.ones(n, dtype=np.float32)
    lines = plan["lines"]
    report = []
    for i, ln in enumerate(lines):
        start = ln["start"] - t0
        limit = (lines[i + 1]["start"] - t0 - GAP) if i + 1 < len(lines) else (t1 - t0)
        limit = min(limit, ln["end"] - t0 + MAX_OVERRUN)
        slot = ln["end"] - ln["start"]
        room = limit - start
        chosen = None
        tried = []
        for k, text in enumerate(ln[plan["lang"]]):
            path = os.path.join(work, f"line{i + 1}.wav")
            d = tts(text, voice, path)
            tried.append(dict(text=text, natural=round(d, 2), needed_tempo=round(max(1.0, d / room), 3)))
            tempo = 1.0
            if d > room:
                tempo = d / room
                if tempo > MAX_TEMPO:
                    continue
                d = tts(text, voice, path, tempo)
            chosen = dict(text=text, candidate=k, natural=round(d * tempo, 2), tempo=round(tempo, 3),
                          dur=round(d, 2), path=path)
            break
        if chosen is None:
            # nothing fits: use the shortest candidate at max tempo and flag it for a human
            text = ln[plan["lang"]][-1]
            path = os.path.join(work, f"line{i + 1}.wav")
            nat = tts(text, voice, path)
            d = tts(text, voice, path, MAX_TEMPO)
            chosen = dict(text=text, candidate=len(ln[plan["lang"]]) - 1, natural=round(nat, 2), tempo=MAX_TEMPO,
                          dur=round(d, 2), path=path, flag="does not fit its slot; needs a human rephrase")
        v = read_pcm(chosen["path"], 1)[:, 0]
        a = int(start * SR)
        b = min(n, a + len(v))
        dub[a:b] += v[: b - a]
        # mute the original speech for this line; duck the original under any overrun into the pause
        ma, mb = int(max(0, start - PAD) * SR), int(min(t1 - t0, ln["end"] - t0 + PAD) * SR)
        gain[ma:mb] = 0.0
        over = gain[mb:b]
        gain[mb:b] = np.minimum(over, DUCK)
        end = start + chosen["dur"]
        if end > limit + 1e-3:
            chosen.setdefault("flag", "overlaps the next line")
        report.append(dict(line=i + 1, en=ln["en"], text=chosen["text"], candidate=chosen["candidate"],
                           orig_start=round(start, 2), orig_end=round(ln["end"] - t0, 2),
                           orig_slot=round(slot, 2), room=round(room, 2), dub_start=round(start, 2),
                           dub_end=round(end, 2), natural=chosen["natural"], tempo=chosen["tempo"],
                           flag=chosen.get("flag", ""), tried=tried))
    # smooth gain changes (30 ms) so cuts do not click
    k = int(0.03 * SR)
    gain = np.convolve(gain, np.ones(k) / k, mode="same").astype(np.float32)
    mix = orig * gain[:, None] + dub[:, None] * 0.9
    peak = float(np.abs(mix).max())
    if peak > 0.98:
        mix *= 0.98 / peak
    wav = os.path.join(work, "mix.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
    lang = plan["lang"]
    srt = os.path.join(outdir, f"dub.{lang}.srt")
    with open(srt, "w") as f:
        for r in report:
            f.write(f"{r['line']}\n{srt_time(r['dub_start'])} --> {srt_time(r['dub_end'])}\n{r["text"]}\n\n")
    out = os.path.join(outdir, f"dub.{lang}.mp4")
    sh("ffmpeg", "-y", "-i", seg, "-i", wav, "-i", srt, "-map", "0:v", "-map", "1:a", "-map", "2:s",
       "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-c:s", "mov_text",
       "-metadata:s:a:0", f"language={'spa' if lang == 'es' else lang}",
       "-metadata:s:s:0", f"language={'spa' if lang == 'es' else lang}", "-movflags", "+faststart", out)
    json.dump(report, open(os.path.join(outdir, "lines.json"), "w"), indent=1, ensure_ascii=False)
    for r in report:
        print(r)


if __name__ == "__main__":
    main(*sys.argv[1:5])
