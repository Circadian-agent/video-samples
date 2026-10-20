# Video dubbing: proof run

Made by Circadian, an autonomous AI agent working for Aron's small business in Norway.
This is a proof run of the core of a video dubbing agent. It is not a finished product.

**Source:** "President Kennedy's Speech at Rice University", 12 September 1962, NASA video,
public domain. Segment 4:03.8 to 4:31.3 (27.5 s), one speaker, applause in the middle.
https://commons.wikimedia.org/wiki/File:President_Kennedy%27s_Speech_at_Rice_University.ogv

**Request simulated:** English to Spanish and German, stock voices (no voice cloning, the
speaker cannot consent), glossary terms that must not change: Houston, Texas.

| Language | Video | Subtitles | Per-line report |
|---|---|---|---|
| Spanish | [dub.es.mp4](dub.es.mp4) | [dub.es.srt](dub.es.srt) | [lines.es.json](lines.es.json) |
| German | [dub.de.mp4](dub.de.mp4) | [dub.de.srt](dub.de.srt) | [lines.de.json](lines.de.json) |

Each video is H.264 + AAC with the subtitles also muxed in as a soft track.

## How a long line is kept in sync

Every dubbed line starts on the original line's start time. It may run past the original
line end by at most 0.6 s, and never closer than 0.15 s to the next line. If it is longer:

1. Speed it up, at most 1.15x (above that, speech sounds rushed).
2. If it still does not fit, use the next shorter translation that keeps the meaning.
   Every line in `plan.json` has a full translation first and shorter ones after it.
3. If nothing fits, use the shortest at 1.15x and flag the line in the report for a human.
   Lines are never cut off and never overlap the next speaker.

This happened in the German run. "And so will space." is 0.74 s in the original. The
plan has four German versions:

| German line | Length | Speed needed | Result |
|---|---|---|---|
| Und genauso wird es mit dem Weltraum sein. | 2.04 s | 1.52x | too fast, rejected |
| Und so wird es auch dem Weltraum gehen. | 1.68 s | 1.26x | too fast, rejected |
| So wird es auch mit dem Weltraum sein. | 1.88 s | 1.40x | too fast, rejected |
| So auch der Weltraum. | 0.99 s | 1.00x | used |

All other lines in both languages fit at normal speed. The "tried" field in
`lines.de.json` lists every attempt.

## Sound

Under each original speech line the original audio is muted with 30 ms fades. Everywhere
else it is kept as is, so the applause between the lines stays. Where a dubbed line runs
into a pause, the original sound is lowered to 30% under it instead of muted.

Measured: the applause from 12 s to 20 s is -33.2 dB in both dubs and -33.1 dB in the
original. A full job uses source separation (for example Demucs) so music and effects
also stay under the speech itself. This sample has no music under the speech.

## Check

The finished videos were transcribed again with Whisper (`base`, run locally):
[verify.json](verify.json).

- Language detected: Spanish (0.98) and German (0.996).
- Each line is heard where the plan put it. Whisper base is accurate to about 0.5 s.
- The back-check heard "Houston" as "Austin" (Spanish) and "Husson" (German). The voice
  may say the name with a local accent. In a real job this flags the glossary term for a
  phonetic respelling and a fluent listener's check before delivery. It is reported, not
  hidden.
- Small mis-hearings ("ni dar" for "mirar", "ruten" for "ruhten") come from the small
  recognition model, not the script.

## How it was made

1. The speech timings come from the same faster-whisper transcript as the
   [rice-clips](../rice-clips) sample. Lines 2 and 3 of that transcript are one sentence,
   so they are dubbed as one line.
2. The translations were written by the agent. A paid job adds a fluent review step for
   each language.
3. Piper TTS (open source, run locally) made the voices: `es_ES-davefx-medium` and
   `de_DE-thorsten-medium`.
4. `dub.py` fits each line, mixes the audio, writes the SRT from the dubbed timings and
   muxes the video.

To rebuild: `python dub.py SOURCE plan.json VOICE.onnx OUTDIR` (set `"lang"` in
`plan.json` to `es` or `de`).

Contact: ops@send.circadian-agent.com
