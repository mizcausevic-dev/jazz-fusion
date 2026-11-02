"""Factual article draft. Not published."""

from __future__ import annotations

from tools.statements import AUDITION, ON_PICTURE, PREVIEW_LINE, PROGRAM, PUBLICATION, WARNING

TITLE = "Jazz Fusion is a note-only MIDI construction kit"
SUBTITLE = "Four kits, 32-bar arrangements, and an 8-bar simple-synth preview that is not a master"
TAGS = ["midi", "jazz-fusion", "music-production", "composition", "harmony"]
TAG_LINE = "Tags: " + ", ".join(TAGS)

PARAGRAPHS: list[str] = []


def bind(mp3_seconds: str, film_seconds: str) -> None:
    global PARAGRAPHS
    PARAGRAPHS = [
        "DRAFT. " + PUBLICATION,
        TAG_LINE,
        "The pack is four construction kits in 4/4. Tempos are 104, 128, 92, and 116 BPM. Those integers sit in the project range 90 to 145. They are a creative direction, not a claim that the files are authentic jazz fusion productions. Every core part is 8 bars. Every kit has one 32-bar arrangement. Lengths were chosen before the notes were written.",
        "Each kit has two variations of five core roles: drums, bass, keys, lead, and counterline. That is 40 core files. There are no reference-only files. Variation B changes the phrase. It is not a velocity edit and not a uniform transpose of variation A. Relay is a D dorian dialogue at 104 BPM. The lead states D F A, then adds C, then turns the cell over, while the counterline answers in the rests. Keys hold Dm9 spelled D F A C E, G9 spelled G B D F A, Cmaj7 spelled C E G B, and Dm7 spelled D F A C. Trade is A mixolydian at 128 BPM. The lead takes the even bars and the counterline takes the odd bars. Keys are A9 spelled A C# E G B, Dmaj7 spelled D F# A C#, Bm7 spelled B D F# A, and Em9 spelled E G B D F#. Grouped is F lydian at 92 BPM. Accents use a 3+3+2 sixteenth grid inside 4/4. Keys hold Fmaj9 spelled F A C E G, then Cmaj7 spelled C E G B. Climb is Bb major at 116 BPM, with a half-time snare. The lead climbs and the counterline descends. Keys are Bbmaj7 spelled Bb D F A, Gm9 spelled G Bb D F A, Ebmaj9 spelled Eb G Bb D F, and F9 spelled F A C Eb G.",
        "Drums use channel 10: kick 36, snare 38, closed hat 42, open hat 46, crash 49. Closed and open hats do not overlap. Bass is monophonic, MIDI 28 to 55. Keys allow five notes, MIDI 48 to 81. Lead is monophonic, MIDI 60 to 84. Counterline is monophonic, MIDI 48 to 81. C4 is 60. The resolution is 960 ticks per quarter note. Offsets are 0. Trade counterline variation B uses one G#4 outside A mixolydian, and Climb bass variation B uses one B2 outside Bb major. Both are flagged. They are not in the keys.",
        PROGRAM,
        "The keys are ordinary notes. The preview synth plays them with a quiet sine. That envelope is not in the MIDI. Drums are short sines or noise bursts chosen by the MIDI pitch. Bass is a sine. The lead is a triangle. The counterline is a second sine. Nothing in the file is a sample or a program change. Electric piano, electric bass, and a lead instrument are the intended parts. The MIDI does not contain those instruments.",
        "The primary preview is bars 9-16 of Relay at 104 BPM, variation A, all five roles. The encoded MP3 is "
        + mp3_seconds
        + " seconds. The film is "
        + film_seconds
        + " seconds. The 32-bar arrangement remains in the MIDI and is not the MP3. "
        + PREVIEW_LINE
        + ". The film takes its audio from that preview and shows the words "
        + ON_PICTURE
        + " on the picture and in the WebVTT captions.",
        AUDITION
        + " The validator reopened the MIDI bytes and compared them with the canonical score. That is a structural check. The sample peak written beside the preview is the peak of the integer mix. It is not a loudness measurement. Nothing in this build is claimed as a master.",
        "The stills are procedural illustrations of five answering arcs on a walnut field. Brass arcs stand for the keys and the lead. A blue arc stands for the counterline. They are not photographs of a session or of performers.",
        "When you use the files, use either the combined arrangement or the separate parts. " + WARNING,
        "Call to action: keep the MIDI, the matched report, and the preview together. Do not publish this draft to Medium, Instagram, or X from the draft files alone.",
    ]


def markdown() -> str:
    body = "\n\n".join(PARAGRAPHS)
    return f"# {TITLE}\n\n{SUBTITLE}\n\n{body}\n"


def plain_text() -> str:
    lines = [TITLE, "", SUBTITLE, "", *PARAGRAPHS, ""]
    return "\n".join(lines) + "\n"
