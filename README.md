# Jazz Fusion

Original note-only MIDI construction kits. Four kits, five core roles, two variations of each role. The roles are drums, bass, keys, lead, and counterline. Each part is 8 bars. Each kit has one 32-bar arrangement built from variation A. There are no reference-only parts.

This is a creative direction: rhythmic interaction, motif development, controlled harmonic movement, and instrumental dialogue. It is not a claim that the files are authentic genre productions. The GitHub repository is https://github.com/mizcausevic-dev/jazz-fusion and it is public. The catalog address is https://mizcausevic-dev.github.io/jazz-fusion/ .

## What you can open

- `index.html` is the file catalog. The kit chooser draws lanes from the MIDI bytes.
- `media.html` is the screening room. The film sits under the pictures.
- `midi/arrangement.mid` is the Format 1 arrangement of Relay, variation A, 32 bars.
- The other three arrangements live next to their part files under `midi/`.
- Individual Format 0 parts live under `midi/`.
- `midi/validation-Cursor.json` is the report from reopening those exact bytes.
- `preview/preview.mp3` is the primary music preview. It is 18.495 seconds in the encoded file. preview, not a master.
- `film/preview.mp4` and `film/preview.vtt` are the film. On-picture and caption text is `preview, not master`.
- `art/hero.jpg` is a 1280x720 illustration. `art/square.jpg` is 1080x1080. Neither is a photograph.

Use either the combined arrangement or the separate parts. Do not stack the part files on top of the combined file.

## Kits

- k01 Relay: 104 BPM, parts 8 bars, arrangement 32 bars, D dorian, tonic D.
- k02 Trade: 128 BPM, parts 8 bars, arrangement 32 bars, A mixolydian, tonic A.
- k03 Grouped: 92 BPM, parts 8 bars, arrangement 32 bars, F lydian, tonic F.
- k04 Climb: 116 BPM, parts 8 bars, arrangement 32 bars, Bb major, tonic Bb.

Core files: 40. Reference files: 0. There is no reference-only part. All five roles are core. The arrangements reuse those files.

Drums use channel 10 and the map in this catalog. There is no separate percussion part. Bass is monophonic, MIDI 28 to 55. Keys are MIDI 48 to 81, at most five notes. Lead is monophonic, MIDI 60 to 84. Counterline is monophonic, MIDI 48 to 81. C4 is 60. PPQ is 960. Meter is 4/4. Offsets are 0. Seeds identify kits and are not random draws. Generator jazz-fusion-1.0.0.

Declared instruments: drums are a kit on channel 10, bass is electric bass and monophonic, keys are electric-piano voicings, lead is monophonic, and counterline is a second monophonic line. Slides, pitch bend, sustain pedal, and hat chokes are not encoded. A seventh chord in this pack includes the seventh. A ninth includes the seventh and the ninth.

## Preview path

The preview renders bars 9-16 of `midi/arrangement.mid` (ticks 30720 through 61440) with `simple-synth-1.0.0`. Those notes are variation A of all five Relay parts, each shifted by 8 bars. The 32-bar arrangement stays in the MIDI. It is not the MP3. Tempo authority is the encoded microsecond value in the MIDI, 576923 us per quarter note. Sample positions use `floor(seconds * 44100 + 0.5)` from the excerpt start. Intervals are not summed. Sample-exact repeating loops at an arbitrary BPM are not promised.

The synth mapping is a falling sine or a noise burst for drums, a sine for bass, a quiet sine for keys, a triangle for the lead, and a second sine for the counterline. The renderer stops at note-off. No program changes are encoded. A conventional GM player will normally use its default piano program for pitched channels unless configured otherwise; compatible GM channel 10 percussion is treated separately. Player behavior may vary. The mapping is not encoded in the MIDI.

Encoded MP3 settings: libmp3lame, 192 kbps. Film audio is AAC at 160 kbps re-encoded from that MP3, so the decoded film audio is not byte-identical to the MP3. Film duration probe: 18.461 seconds. MP3 container probe 18.495 seconds. MP4 probe 18.461 seconds. The film ends on a video frame, so it can be slightly shorter than the MP3 container. The music is the same preview, not a different excerpt. The picture is a still illustration with rasterized disclosure text. DejaVu Sans Bold from the build machine supplies the glyphs. The font file is not in this pack.

No human listening audition was performed for this build. A sample peak is recorded in the preview manifest. It is not a loudness figure and it is not a true peak.

## Build

From the repository root, with Python 3.11+ and ffmpeg (libmp3lame, aac, libx264):

```bash
python3 tools/build_pack.py
python3 -m http.server 43171
```

The page is static. It is served with Python's HTTP server so the MIDI and media keep working relative paths. There is no application server and no package install. Standard library only.

`build/` holds the intermediate WAV, the procedural PPM, and the film plate. Those files are gitignored. The delivered audio is the MP3.

## Checks the validator actually runs

File existence, parse, PPQ, tempo, 4/4, end-of-track boundary, note pairing, ranges, monophonic bass, lead, and counterline, keys polyphony cap of five, channel 10 map, same-pitch overlap, note-off before note-on at a shared tick, absence of program changes and other channel messages, chord names against the keys pitches, departure flags against the declared pitch-class set, agreement with the canonical score, and agreement between each arrangement and the placed source parts. Variation A attack times must differ across kits for each role. A negative overlap fixture is written outside the pack and must be rejected.

## Drafts and publication

Social captions, the X post, and the Medium article are drafts. They are not access controls. This repository is public, so the drafts are public. Do not treat them as posted to Instagram, X, or Medium.

Prepared repository description: Original note-only MIDI construction kits for jazz fusion, with matched validation and a simple-synth preview.

Prepared topics: midi, jazz-fusion, music-production, composition, harmony.

No release tag was created. `index.html` keeps its name because players and links depend on it. This page is the file catalog the pack requires. GitHub Pages serves the materialized tree when Pages is enabled for the gh-pages branch.

## Limitations

Variation A and variation B of a kit are alternatives. The arrangement already contains variation A, so stacking the part files on top of it doubles those notes. Parts from different kits do not share a tempo or a collection. Grouped's accent grid is 3+3+2 sixteenths inside 4/4. It does not change the meter. These parts are original.
