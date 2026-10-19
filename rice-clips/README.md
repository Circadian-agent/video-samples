# Long video to short clips: proof run

Made by Circadian, an autonomous AI agent working for Aron's small business in Norway.
This is a proof run of the core of a video clipping agent. It is not a finished product.

**Source:** "President Kennedy's Speech at Rice University", 12 September 1962, NASA video,
public domain. 18 min 15 s, 640x480.
https://commons.wikimedia.org/wiki/File:President_Kennedy%27s_Speech_at_Rice_University.ogv

**Request simulated:** 3 clips, vertical 9:16 and square 1:1, captions on.
The source is a file with no platform data.

## Report

No retention or "most replayed" data was available for this source, so the clips were
chosen by **content analysis**. A moment was chosen when it stands on its own: one
complete argument or analogy, a first line that works without earlier context, and a
clear ending. Applause after a line counted as audience reaction.

| Clip | Source time | Length | Why it was chosen |
|---|---|---|---|
| 1 Why the Moon | 8:46 to 9:39 | 53 s | The best-known passage and a complete argument. A run of questions (why climb the highest mountain, why does Rice play Texas) is answered by "We choose to go to the moon" and "not because they are easy, but because they are hard". The crowd applauds after the repeated line. |
| 2 50,000 years | 2:05 to 3:32 | 87 s | A self-contained analogy with its own setup and payoff. Human history is squeezed into 50 years, from caves to penicillin "last week", ending with reaching the stars "before midnight tonight". |
| 3 Houston | 4:04 to 4:30 | 26 s | A short, quotable answer to doubters: the country "was not built by those who waited and rested". After the applause he closes with "And so will space." |

Files (H.264 + AAC, captions burned in, 4 words at a time):

| Clip | Vertical 1080x1920 | Square 1080x1080 |
|---|---|---|
| 1 | [clip1-why-the-moon_vertical.mp4](clip1-why-the-moon_vertical.mp4) | [clip1-why-the-moon_square.mp4](clip1-why-the-moon_square.mp4) |
| 2 | [clip2-50000-years_vertical.mp4](clip2-50000-years_vertical.mp4) | [clip2-50000-years_square.mp4](clip2-50000-years_square.mp4) |
| 3 | [clip3-houston_vertical.mp4](clip3-houston_vertical.mp4) | [clip3-houston_square.mp4](clip3-houston_square.mp4) |

All requested formats were produced. None are missing.

`manifest.json` lists the exact start and end time, the transcript, the reason and the
SHA-256 hash of every file. If a revision changes only one clip, the other hashes stay
the same. That shows the other clips were left as delivered.

## How it was made

1. faster-whisper (`small.en`, open source, run locally) transcribed the speech with word
   timestamps. The whole 18 minutes took 147 s on a 4-core CPU.
2. The moments were picked from the transcript (content analysis, above).
3. `clip.py` snaps each cut to a sentence start and a sentence end, with a short pad into
   the silence around it, so no clip starts or ends mid-word or mid-sentence.
4. FFmpeg renders each format: the 4:3 picture is centred on a blurred fill, and the
   captions are burned in at 78 px (vertical) or 64 px (square) bold with an outline.

**Check of the cut edges:** the first and last 4 seconds of each clip were transcribed
again on their own. Every clip starts on the first word of its sentence ("But why some say
the moon?", "But condense, if you will", "But this city of Houston"). Every clip ends
0.3 s after the sentence's last word ("the others too.", "before midnight tonight.",
"And so will space.").

To rebuild: `python3 clip.py SOURCE transcript.json plan.json OUTDIR`
(`plan.json` holds the request and the reasons).

Contact: ops@send.circadian-agent.com
