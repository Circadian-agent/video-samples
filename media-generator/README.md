# Media generator: proof run

Made by Circadian, an AI agent working for Aron's small business in Norway.
This is a proof run of the core loop of a pay-per-use media generator agent:
brief, rules check, generate, check each file, report. It is not the finished product.

It runs three of the four sample scenarios from the job brief. The video scenario was not run here.

| Scenario | Result | Files |
|---|---|---|
| 3 product photos of a ceramic mug on a wooden table, square | Delivered. 3 files, each 768x768. Mug and table visible in all 3. | [mug-1](out/mug-1.jpg), [mug-2](out/mug-2.jpg), [mug-3](out/mug-3.jpg) |
| 30-second voiceover from a script, female voice | **Not delivered. Flagged for review** by the checks. See below. | [voiceover.wav](out/voiceover.wav) (last attempt, kept for inspection) |
| Image of a well-known celebrity holding the product | Declined before any call to a provider. Reason in the report. | none |

Reports: [report.mug-celebrity.json](out/report.mug-celebrity.json), [report.voiceover.json](out/report.voiceover.json).
Each file has its provider, model, seed or settings, and SHA-256. Code: [mg.py](mg.py), input: [brief.json](brief.json).

## What the checks caught

**Voiceover.** The buyer's 69-word script reads in about 23 to 24 seconds at a natural pace,
not 30. The agent first fills the gap with longer pauses between sentences, and slows speech by
at most 10%. Then Whisper transcribes the audio and compares it to the script word by word.

- Attempt 1 (first voice): 26.7 s, too short. Whisper heard "mugs" as "monks".
- 4 more attempts with pause fill and two different public domain voices: one hit 29.7 s, but
  every attempt still had 2 to 4 words that did not match ("pick" heard as "make" or "take").

So the voiceover was **not delivered**. In a real job the agent would tell the buyer the script
is short for 30 seconds, offer longer pauses or a few more words, and hold the file until it passes.
The mismatched words changed from one render to the next. That points at the small checker model
(Whisper base, used here because of disk space) as much as at the voice. That is why the
production version uses a larger speech model for the check, and a second model when the two disagree.

**Images.** The free tier used in this proof adds a small "pollinations.ai" mark in the corner
and does not say which model it used. Both are reasons it is a proof provider only. On mug 3
the rim is slightly uneven: a small visual error of the kind the brief warns about.

## How the production agent picks a provider

1. Filter by what the brief needs: media type, size or aspect ratio, length, reference image or script input.
2. Drop providers whose terms do not allow commercial use and resale of outputs.
3. Rank the rest by cost per file, typical time, and pass rate on our own checks for that kind of brief.
4. If a file fails a check, regenerate once with the same provider and a new seed, then try the
   next provider. After that, deliver what passed and list what did not, with the reason.

Revisions change only the named files. The report keeps the SHA-256 of every file, so the buyer can
see that the other files are unchanged.
