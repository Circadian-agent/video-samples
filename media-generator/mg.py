#!/usr/bin/env python3
"""Media generator proof run: brief -> rules check -> generate -> check -> report."""
import json, os, re, subprocess, sys, time, urllib.parse, urllib.request, wave, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
VENV_BIN = os.path.join(os.path.dirname(HERE), "v", "bin")
VOICE = os.path.join(HERE, "voices", "en_US-kristin-medium.onnx")
os.makedirs(OUT, exist_ok=True)

# Proof-only stand-in for the production check (a vision/NER classifier plus a consent question).
KNOWN_PEOPLE = {"taylor swift", "elon musk", "beyonce", "lionel messi", "barack obama"}
PROTECTED = {"mickey mouse", "pikachu", "spider-man", "nike logo", "coca-cola logo"}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=width,height:format=duration", "-of", "json", p],
                       capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def rules(text, consent):
    t = text.lower()
    for name in KNOWN_PEOPLE:
        if name in t and not consent:
            return f"declined: names a real, identifiable person ({name.title()}) and the buyer has not confirmed they are that person or have their consent"
    for name in PROTECTED:
        if name in t:
            return f"declined: {name} is a copyrighted character or a brand the buyer has not shown they own"
    return None


def image_job(job):
    files, attempts = [], []
    w, h = job["width"], job["height"]
    seed = 101
    while len(files) < job["count"] and len(attempts) < job["count"] * 3:
        url = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(job["prompt"]) +
               f"?width={w}&height={h}&seed={seed}&nologo=true&model={job['model']}")
        path = os.path.join(OUT, f"{job['id']}-{len(files) + 1}.jpg")
        t0 = time.time()
        time.sleep(50)  # free tier allows one image per 45 s per IP
        try:
            with urllib.request.urlopen(url, timeout=300) as r:
                open(path, "wb").write(r.read())
        except Exception as e:
            attempts.append({"seed": seed, "error": str(e)[:120], "seconds": round(time.time() - t0, 1)})
            seed += 1
            continue
        st = probe(path)["streams"][0]
        ok = abs(st["width"] / st["height"] - w / h) < 0.01
        attempts.append({"seed": seed, "size": f"{st['width']}x{st['height']}", "format_ok": ok,
                         "seconds": round(time.time() - t0, 1)})
        seed += 1
        if ok:
            files.append({"file": os.path.basename(path), "size": f"{st['width']}x{st['height']}",
                          "sha256": sha(path), "provider": "pollinations.ai",
                          "model": "not reported by the free tier (provider default; GET /models listed only sana on 2026-10-20)", "seed": seed - 1})
        else:
            os.remove(path)
    return {"files": files, "attempts": attempts}


def words(s):
    return re.findall(r"[a-z0-9']+", s.lower().replace("-", " "))


def synth(txt, path, scale, silence):
    subprocess.run([os.path.join(VENV_BIN, "piper"), "-m", VOICE, "-f", path,
                    "--length-scale", f"{scale:.3f}", "--sentence-silence", f"{silence:.3f}", "-i", txt],
                   check=True, capture_output=True)
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def hear(asr, path):
    import numpy as np
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    segs, _ = asr.transcribe(np.frombuffer(pcm, np.float32), language="en", beam_size=5)
    return " ".join(s.text.strip() for s in segs)


def voice_job(job):
    """Hit the length with natural pauses first (speech is slowed at most 10%), then check every word."""
    from faster_whisper import WhisperModel
    asr = WhisperModel("base", device="cpu", compute_type="int8")
    target, attempts = job["seconds"], []
    txt = os.path.join(OUT, "script.txt")
    open(txt, "w").write(job["script"])
    path = os.path.join(OUT, f"{job['id']}.wav")
    gaps = max(1, len(re.findall(r"[.!?]", job["script"])) - 1)
    for scale in (1.0, 1.05, 1.10, 0.97):
        silence = 0.35
        dur = synth(txt, path, scale, silence)
        # natural speech is short: spread the missing time over the sentence breaks (max 1.6 s each)
        silence = min(1.2, max(0.2, silence + (target - dur) / gaps))
        dur = synth(txt, path, scale, silence)
        heard = hear(asr, path)
        a, b = words(job["script"]), words(heard)
        diff = [(i, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y]
        att = {"length_scale": scale, "sentence_pause_s": round(silence, 2), "seconds": round(dur, 2),
               "duration_ok": abs(dur - target) <= 1.0, "word_for_word": a == b,
               "mismatches": diff[:10] + ([("count", len(a), len(b))] if len(a) != len(b) else [])}
        attempts.append(att)
        if att["duration_ok"] and att["word_for_word"]:
            break
    return {"files": [{"file": os.path.basename(path), "seconds": round(dur, 2), "sha256": sha(path),
                       "provider": "local Piper TTS (self-hosted)", "model": "en_US-kristin-medium (public domain LibriVox voice)"}],
            "attempts": attempts, "duration_ok": att["duration_ok"],
            "script_check": {"asr": "faster-whisper base", "word_for_word": att["word_for_word"], "heard": heard},
            "flag_for_review": not (att["duration_ok"] and att["word_for_word"])}


def main():
    brief = json.load(open(sys.argv[1]))
    report = {"brief": brief["title"], "made_by": "Circadian, an AI agent working for Aron's business (Norway)",
              "items": []}
    only = sys.argv[2:] or None
    for job in brief["jobs"]:
        if only and job["id"] not in only:
            continue
        reason = rules(job.get("prompt", "") + " " + job.get("script", ""), job.get("consent", False))
        item = {"id": job["id"], "type": job["type"], "request": job.get("prompt") or job.get("script")[:80] + "..."}
        if reason:
            item.update(status="declined", reason=reason, files=[])
        elif job["type"] == "image":
            item.update(status="delivered", **image_job(job))
        elif job["type"] == "voiceover":
            item.update(status="delivered", **voice_job(job))
        report["items"].append(item)
        print(json.dumps({k: item[k] for k in ("id", "status")}), flush=True)
    json.dump(report, open(os.path.join(OUT, f"report.{'-'.join(only or ['all'])}.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
