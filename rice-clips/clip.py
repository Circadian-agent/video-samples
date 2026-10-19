"""Render sentence-aligned clips with burned captions from a word-timestamped transcript.

usage: clip.py SOURCE TRANSCRIPT.json PLAN.json OUTDIR
PLAN: {"clips":[{"id":"c1","from":"<start phrase>","to":"<end phrase>","why":"..."}],
       "formats":["vertical","square"],"captions":true}
"""
import json, re, subprocess, sys, hashlib, os

src, tpath, ppath, out = sys.argv[1:5]
os.makedirs(out, exist_ok=True)
words = [w for s in json.load(open(tpath)) for w in s["words"]]
plan = json.load(open(ppath))
norm = lambda t: re.sub(r"[^a-z0-9 ]", "", t.lower()).split()
toks = [norm(w["w"]) for w in words]
flat = [(i, t) for i, ts in enumerate(toks) for t in ts]
ENDS = re.compile(r"[.?!][\"')\]]*$")

def find(phrase, after=0):
    p = norm(phrase)
    for k in range(len(flat) - len(p) + 1):
        if flat[k][0] >= after and [t for _, t in flat[k:k + len(p)]] == p:
            return flat[k][0], flat[k + len(p) - 1][0]
    raise SystemExit(f"phrase not found: {phrase!r}")

def snap(a, b):
    # Start on a sentence start, end on a sentence end, never mid-word.
    while a > 0 and not ENDS.search(words[a - 1]["w"].strip()):
        a -= 1
    while b < len(words) - 1 and not ENDS.search(words[b]["w"].strip()):
        b += 1
    return a, b

def ts(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"

SIZES = {"vertical": (1080, 1920, 78, 560), "square": (1080, 1080, 64, 150)}
manifest = {"source": os.path.basename(src), "selection": plan.get("selection"), "clips": [], "unsupported": []}
for c in plan["clips"]:
    a, _ = find(c["from"]); _, b = find(c["to"], a)
    a, b = snap(a, b)
    # Pad into the surrounding silence, but stay clear of the neighbouring words.
    start = max(words[a]["s"] - 0.25, (words[a - 1]["e"] + words[a]["s"]) / 2 if a else 0)
    end = min(words[b]["e"] + 0.35, (words[b]["e"] + words[b + 1]["s"]) / 2 if b + 1 < len(words) else 1e9)
    text = "".join(w["w"] for w in words[a:b + 1]).strip()
    entry = {"id": c["id"], "start": round(start, 2), "end": round(end, 2),
             "duration": round(end - start, 2), "first_words": " ".join(text.split()[:8]),
             "last_words": " ".join(text.split()[-8:]), "transcript": text, "why": c["why"], "files": {}}
    for fmt in plan["formats"]:
        if fmt not in SIZES:
            manifest["unsupported"].append({"clip": c["id"], "format": fmt, "reason": "format not supported"}); continue
        W, H, fs, mv = SIZES[fmt]
        ass = os.path.join(out, f"{c['id']}_{fmt}.ass")
        with open(ass, "w") as f:
            f.write(f"[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\n\n[V4+ Styles]\n"
                    "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV\n"
                    f"Style: Cap,Liberation Sans,{fs},&H00FFFFFF,&H00000000,&H80000000,1,1,5,1,2,60,60,{mv}\n\n"
                    "[Events]\nFormat: Layer, Start, End, Style, Text\n")
            seg = words[a:b + 1]; i = 0
            while plan.get("captions") and i < len(seg):
                chunk = [seg[i]]
                while i + len(chunk) < len(seg) and len(chunk) < 4 and not ENDS.search(chunk[-1]["w"].strip()) \
                        and not chunk[-1]["w"].strip().endswith(","):
                    chunk.append(seg[i + len(chunk)])
                s0 = chunk[0]["s"] - start
                e0 = (seg[i + len(chunk)]["s"] if i + len(chunk) < len(seg) else chunk[-1]["e"] + 0.3) - start
                f.write(f"Dialogue: 0,{ts(max(s0, 0))},{ts(e0)},Cap,{''.join(w['w'] for w in chunk).strip()}\n")
                i += len(chunk)
        # Source is 4:3: blurred fill behind a sharp centred copy.
        vf = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=30[bg];"
              f"[0:v]scale={W}:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,ass={ass}[v]")
        dst = os.path.join(out, f"{c['id']}_{fmt}.mp4")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{start:.2f}", "-to", f"{end:.2f}", "-i", src,
                        "-filter_complex", vf, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "26", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", dst], check=True)
        entry["files"][fmt] = {"file": os.path.basename(dst), "size": f"{W}x{H}",
                               "sha256": hashlib.sha256(open(dst, "rb").read()).hexdigest()}
        os.remove(ass)
    manifest["clips"].append(entry)
json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), indent=2)
print(json.dumps([{k: e[k] for k in ("id", "start", "end", "first_words", "last_words")} for e in manifest["clips"]], indent=1))
