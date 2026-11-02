"""Original jazz fusion construction kits.

Container lengths were chosen before any notes: every core part is 8 bars,
every arrangement is 32 bars, meter 4/4. Tempos are integer quarter-note BPM
values inside the project range 90-145. Offsets are 0. Nothing is random.

Chord names are checked against the keys pitches. A seventh name requires the
seventh. A ninth name requires the seventh and the ninth.
"""

from __future__ import annotations

from tools.midi_io import BAR_TICKS_4_4, PPQ, bpm_to_us, effective_bpm

GENERATOR_VERSION = "jazz-fusion-1.0.0"
PACK_ID = "jazz-fusion"
PACK_NAME = "Jazz Fusion"
BAR = BAR_TICKS_4_4
S = 240

DRUM_MAP = {
    36: "Bass Drum 1",
    38: "Acoustic Snare",
    42: "Closed Hi-Hat",
    46: "Open Hi-Hat",
    49: "Crash Cymbal 1",
}
PERC_MAP: dict[int, str] = {}
ROLE_NAME = {
    "drums": "Drums",
    "bass": "Bass",
    "keys": "Keys",
    "lead": "Lead",
    "counterline": "Counterline",
}
ROLE_ORDER = ("drums", "bass", "keys", "lead", "counterline")
PITCHED = ("bass", "keys", "lead", "counterline")

# Spellings used by the names. Root is interval 0.
# maj7: 4 and 11. m7: 3 and 10. dominant 9: 4, 10, 2. maj9 adds 11 and 2. m9: 3, 10, 2.
# The perfect fifth, interval 7, may be present. Other intervals may not.


def root_pc(name: str) -> int:
    for prefix, pc in (
        ("Bb", 10),
        ("Eb", 3),
        ("C", 0),
        ("D", 2),
        ("E", 4),
        ("F", 5),
        ("G", 7),
        ("A", 9),
        ("B", 11),
    ):
        if name.startswith(prefix):
            return pc
    raise ValueError(name)


def required_intervals(name: str) -> set[int]:
    if name.endswith("maj9"):
        return {0, 4, 11, 2}
    if name.endswith("maj7"):
        return {0, 4, 11}
    if name.endswith("m9"):
        return {0, 3, 10, 2}
    if name.endswith("m7"):
        return {0, 3, 10}
    if name.endswith("9"):
        return {0, 4, 10, 2}
    raise ValueError(f"unnamed chord quality {name}")


def assert_chord_name(name: str, pitches: list[int]) -> None:
    intervals = {((pitch % 12) - root_pc(name)) % 12 for pitch in pitches}
    need = required_intervals(name)
    if 0 not in intervals:
        raise ValueError(f"{name} is missing its root")
    missing = need - intervals
    if missing:
        raise ValueError(f"{name} is missing intervals {sorted(missing)}")
    extra = intervals - (need | {7})
    if extra:
        raise ValueError(f"{name} has intervals {sorted(extra)} that the name does not cover")


class Part:
    def __init__(self, kit, role, variation, channel, slug, mono, poly, lo, hi):
        self.kit = kit
        self.part_id = f"{kit['id']}.{role}.{variation}"
        self.role = role
        self.variation = variation
        self.core = True
        self.channel = channel
        self.file_slug = slug
        self.monophonic = mono
        self.max_poly = poly
        self.lo = lo
        self.hi = hi
        self.container_ticks = kit["part_bars"] * BAR
        self.notes = []

    def add(self, start, duration, pitch, velocity, departure=False):
        end = start + duration
        if start < 0 or duration <= 0 or end > self.container_ticks:
            raise ValueError(f"{self.part_id} boundary {start}+{duration}")
        if not self.lo <= pitch <= self.hi:
            raise ValueError(f"{self.part_id} pitch {pitch}")
        if self.role == "drums" and pitch not in DRUM_MAP:
            raise ValueError(f"{self.part_id} drum pitch {pitch} is outside the map")
        if not 1 <= velocity <= 127:
            raise ValueError(f"{self.part_id} velocity {velocity}")
        active = 1
        for other in self.notes:
            o0 = other["performed_start"]
            o1 = o0 + other["duration"]
            if start < o1 and o0 < end:
                if other["pitch"] == pitch or self.monophonic:
                    raise ValueError(
                        f"{self.part_id} overlap {pitch}@{start} with {other['pitch']}@{o0}"
                    )
                active += 1
        if active > self.max_poly:
            raise ValueError(f"{self.part_id} poly {active}")
        self.notes.append({
            "nominal_start": start,
            "offset": 0,
            "performed_start": start,
            "duration": duration,
            "pitch": pitch,
            "velocity": velocity,
            "channel": self.channel,
            "departure": departure,
        })

    def finish(self):
        ordered = sorted(self.notes, key=lambda note: (note["performed_start"], note["pitch"]))
        if len(ordered) < 4:
            raise ValueError(f"{self.part_id} too few notes")
        for index, note in enumerate(ordered, 1):
            note["id"] = f"{self.part_id}.n{index:04d}"
        return {
            "id": self.part_id,
            "kit_id": self.kit["id"],
            "slug": self.kit["slug"],
            "role": self.role,
            "variation": self.variation,
            "core": True,
            "channel": self.channel,
            "file_slug": self.file_slug,
            "path": f"midi/{self.kit['slug']}/{self.file_slug}.mid",
            "monophonic": self.monophonic,
            "max_poly": self.max_poly,
            "container_ticks": self.container_ticks,
            "container_bars": self.kit["part_bars"],
            "bpm": self.kit["bpm"],
            "tempo_us": self.kit["tempo_us"],
            "notes": ordered,
        }


def add_events(part, events):
    for event in events:
        bar, tick, dur, pitch, vel = event[:5]
        departure = bool(event[5]) if len(event) > 5 else False
        part.add(bar * BAR + tick, dur, pitch, vel, departure=departure)


def n(bar, six, dur, pitch, vel, departure=False):
    return (bar, six * S, dur * S, pitch, vel, departure)


def make(kit, role, variation):
    spec = {
        "drums": (9, f"drums-{variation}", False, 4, 36, 49),
        "bass": (0, f"bass-{variation}", True, 1, 28, 55),
        "keys": (1, f"keys-{variation}", False, 5, 48, 81),
        "lead": (2, f"lead-{variation}", True, 1, 60, 84),
        "counterline": (3, f"counterline-{variation}", True, 1, 48, 81),
    }
    channel, slug, mono, poly, lo, hi = spec[role]
    return Part(kit, role, variation, channel, slug, mono, poly, lo, hi)


def hold(chord, bar, tick, dur, vel):
    return [(bar, tick, dur, pitch, vel) for pitch in chord]


def region_holds(regions):
    events = []
    for region in regions:
        events.extend(hold(region["pitches"], region["start_bar"], region["tick"], region["duration"], region["velocity"]))
    return events


def stab_regions(regions):
    events = []
    for region in regions:
        for bar in range(region["start_bar"], region["start_bar"] + region["bars"]):
            for tick, dur, vel in region["stabs"]:
                events.extend(hold(region["pitches"], bar, tick, dur, vel))
    return events


def drum_grid(pattern, extras=None):
    events = []
    for bar in range(8):
        for six, pitch, dur, vel in pattern:
            events.append(n(bar, six, dur, pitch, vel))
        for six, pitch, dur, vel in (extras or {}).get(bar, ()):
            events.append(n(bar, six, dur, pitch, vel))
    return events


def kit_record(kit_id, slug, title, bpm, tonic, collection, pitch_classes, seed, identity, limitations, rhythm, phrases, arrangement_phrases, changes, change_bars, departures, spell, placements, voicings):
    tempo_us = bpm_to_us(bpm)
    return {
        "id": kit_id,
        "slug": slug,
        "title": title,
        "bpm": bpm,
        "tempo_us": tempo_us,
        "effective_bpm": effective_bpm(tempo_us),
        "part_bars": 8,
        "arrangement_bars": 32,
        "bars": 8,
        "meter": "4/4",
        "bar_ticks": BAR,
        "tonic": tonic,
        "tonal_reference": tonic,
        "collection_name": collection,
        "pitch_classes": pitch_classes,
        "departures": departures,
        "seed": seed,
        "identity": identity,
        "limitations": limitations,
        "harmonic_rhythm": rhythm,
        "phrases": phrases,
        "arrangement_phrases": arrangement_phrases,
        "changes": changes,
        "change_bars": change_bars,
        "spell": spell,
        "placements": placements,
        "voicings": voicings,
        "stochastic_draws": 0,
    }


SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
LIMIT = (
    "Variation A and variation B are alternatives. Do not stack them. "
    "Do not mix parts from different kits: the tempos and collections differ. "
    "The 32-bar arrangement uses variation A only. "
    "Closed and open hats never overlap, and no hat-choke controller is written. "
    "Lead and counterline are separate lines. Do not treat one as a copy of the other."
)


def kits():
    two = [
        {"name": "Open", "start_bar": 0, "bars": 2},
        {"name": "Answer", "start_bar": 2, "bars": 2},
        {"name": "Turn", "start_bar": 4, "bars": 2},
        {"name": "Cadence", "start_bar": 6, "bars": 2},
    ]
    four = [
        {"name": "Statement", "start_bar": 0, "bars": 4},
        {"name": "Answer", "start_bar": 4, "bars": 4},
    ]
    relay_a = [
        {"name": "Dm9", "start_bar": 0, "bars": 2, "pitches": [50, 53, 57, 60, 64], "tick": 0, "duration": 2 * BAR, "velocity": 74},
        {"name": "G9", "start_bar": 2, "bars": 2, "pitches": [55, 59, 62, 65, 69], "tick": 0, "duration": 2 * BAR, "velocity": 72},
        {"name": "Cmaj7", "start_bar": 4, "bars": 2, "pitches": [48, 52, 55, 59], "tick": 0, "duration": 2 * BAR, "velocity": 70},
        {"name": "Dm7", "start_bar": 6, "bars": 2, "pitches": [50, 53, 57, 60], "tick": 0, "duration": 2 * BAR, "velocity": 76},
    ]
    relay_b = [
        {"name": "Dm9", "start_bar": 0, "bars": 2, "pitches": [53, 57, 60, 64, 74], "stabs": ((1440, 700, 80), (2880, 480, 64))},
        {"name": "G9", "start_bar": 2, "bars": 2, "pitches": [59, 62, 65, 69, 79], "stabs": ((1440, 700, 78), (2880, 480, 62))},
        {"name": "Cmaj7", "start_bar": 4, "bars": 2, "pitches": [52, 55, 59, 72], "stabs": ((1440, 700, 76), (2880, 480, 60))},
        {"name": "Dm7", "start_bar": 6, "bars": 2, "pitches": [53, 57, 60, 74], "stabs": ((1440, 700, 82), (2880, 480, 66))},
    ]
    trade_a = [
        {"name": "A9", "start_bar": 0, "bars": 2, "pitches": [57, 61, 64, 67, 71], "tick": 960, "duration": 2 * BAR, "velocity": 76},
        {"name": "Dmaj7", "start_bar": 2, "bars": 2, "pitches": [50, 54, 57, 61], "tick": 960, "duration": 2 * BAR, "velocity": 72},
        {"name": "Bm7", "start_bar": 4, "bars": 2, "pitches": [59, 62, 66, 69], "tick": 960, "duration": 2 * BAR, "velocity": 74},
        {"name": "Em9", "start_bar": 6, "bars": 2, "pitches": [52, 55, 59, 62, 66], "tick": 960, "duration": 6720, "velocity": 78},
    ]
    trade_b = [
        {"name": "A9", "start_bar": 0, "bars": 2, "pitches": [57, 61, 67, 71, 76], "stabs": ((480, 600, 84), (2400, 600, 68))},
        {"name": "Dmaj7", "start_bar": 2, "bars": 2, "pitches": [54, 57, 61, 62], "stabs": ((480, 600, 80), (2400, 600, 64))},
        {"name": "Bm7", "start_bar": 4, "bars": 2, "pitches": [62, 66, 69, 71], "stabs": ((480, 600, 82), (2400, 600, 66))},
        {"name": "Em9", "start_bar": 6, "bars": 2, "pitches": [55, 59, 62, 66, 76], "stabs": ((480, 600, 86), (2400, 600, 70))},
    ]
    grouped_a = [
        {"name": "Fmaj9", "start_bar": 0, "bars": 4, "pitches": [53, 57, 60, 64, 67], "tick": 0, "duration": 4 * BAR, "velocity": 70},
        {"name": "Cmaj7", "start_bar": 4, "bars": 4, "pitches": [48, 52, 55, 59], "tick": 0, "duration": 4 * BAR, "velocity": 74},
    ]
    grouped_b = [
        {"name": "Fmaj9", "start_bar": 0, "bars": 4, "pitches": [57, 60, 64, 67, 77], "stabs": ((0, 480, 78), (1440, 480, 64), (2640, 720, 72))},
        {"name": "Cmaj7", "start_bar": 4, "bars": 4, "pitches": [52, 55, 59, 72], "stabs": ((0, 480, 80), (1440, 480, 66), (2640, 720, 74))},
    ]
    climb_a = [
        {"name": "Bbmaj7", "start_bar": 0, "bars": 2, "pitches": [58, 62, 65, 69], "tick": 480, "duration": 2 * BAR, "velocity": 73},
        {"name": "Gm9", "start_bar": 2, "bars": 2, "pitches": [55, 58, 62, 65, 69], "tick": 480, "duration": 2 * BAR, "velocity": 75},
        {"name": "Ebmaj9", "start_bar": 4, "bars": 2, "pitches": [51, 55, 58, 62, 65], "tick": 480, "duration": 2 * BAR, "velocity": 72},
        {"name": "F9", "start_bar": 6, "bars": 2, "pitches": [53, 57, 60, 63, 67], "tick": 480, "duration": 7200, "velocity": 78},
    ]
    climb_b = [
        {"name": "Bbmaj7", "start_bar": 0, "bars": 2, "pitches": [62, 65, 69, 70], "stabs": ((720, 500, 82), (2880, 400, 64))},
        {"name": "Gm9", "start_bar": 2, "bars": 2, "pitches": [58, 62, 65, 69, 79], "stabs": ((720, 500, 80), (2880, 400, 62))},
        {"name": "Ebmaj9", "start_bar": 4, "bars": 2, "pitches": [55, 58, 62, 65, 75], "stabs": ((720, 500, 84), (2880, 400, 66))},
        {"name": "F9", "start_bar": 6, "bars": 2, "pitches": [57, 60, 63, 67, 77], "stabs": ((720, 500, 86), (2880, 400, 68))},
    ]
    for region in relay_a + relay_b + trade_a + trade_b + grouped_a + grouped_b + climb_a + climb_b:
        assert_chord_name(region["name"], region["pitches"])
    return [
        kit_record(
            "k01", "k01-relay", "Relay", 104, "D", "D dorian",
            [0, 2, 4, 5, 7, 9, 11], 10401,
            "The kick answers the snare: beat 1, the last 16th of beat 2, and the and of 3. "
            "The lead states D F A, then adds C, then turns the cell upside down. "
            "The counterline speaks in the lead's rests and moves down. "
            "Keys hold Dm9, G9, Cmaj7, and Dm7. Variation B comps those same chords late in each bar, in a higher voicing.",
            LIMIT,
            "Dm9 is D F A C E for two bars, G9 is G B D F A for two, Cmaj7 is C E G B for two, then Dm7 is D F A C for two. Both variations use those chords.",
            two,
            [
                {"name": "Groove", "start_bar": 0, "bars": 8},
                {"name": "Dialogue", "start_bar": 8, "bars": 8},
                {"name": "Keys", "start_bar": 16, "bars": 8},
                {"name": "Return", "start_bar": 24, "bars": 8},
            ],
            ["Dm9", "G9", "Cmaj7", "Dm7"],
            [2, 2, 2, 2],
            [],
            SHARP,
            {"drums": [0, 8, 24], "bass": [0, 8, 24], "keys": [8, 16], "lead": [8, 16, 24], "counterline": [8, 16]},
            {"a": relay_a, "b": relay_b},
        ),
        kit_record(
            "k02", "k02-trade", "Trade", 128, "A", "A mixolydian",
            [1, 2, 4, 6, 7, 9, 11], 12802,
            "Straight 16th hats and a kick that sits on the 16th before beat 2. "
            "The lead takes the even bars. The counterline takes the odd bars. "
            "Keys enter on beat 2: A9, Dmaj7, Bm7, Em9. "
            "Variation B breaks the trade into overlapping short phrases and comps on the and of 1.",
            LIMIT + " Counterline variation B has one flagged G#4.",
            "A9 is A C# E G B for two bars, Dmaj7 is D F# A C# for two, Bm7 is B D F# A for two, then Em9 is E G B D F# for two. Both variations use those chords.",
            two,
            [
                {"name": "Hats", "start_bar": 0, "bars": 8},
                {"name": "Trade", "start_bar": 8, "bars": 8},
                {"name": "Keys", "start_bar": 16, "bars": 8},
                {"name": "Counter", "start_bar": 24, "bars": 8},
            ],
            ["A9", "Dmaj7", "Bm7", "Em9"],
            [2, 2, 2, 2],
            ["Counterline variation B includes one G#4, flagged, as a chromatic approach to A4. It is outside A mixolydian and it is not in the keys."],
            SHARP,
            {"drums": [0, 16], "bass": [0, 8, 16], "keys": [8, 24], "lead": [8, 16], "counterline": [0, 16, 24]},
            {"a": trade_a, "b": trade_b},
        ),
        kit_record(
            "k03", "k03-grouped", "Grouped", 92, "F", "F lydian",
            [0, 2, 4, 5, 7, 9, 11], 9203,
            "Accents sit on a 3+3+2 sixteenth grid, twice per bar. The meter stays 4/4. "
            "The lead uses that grid and lets B, the raised fourth, into the line. "
            "The counterline holds long notes against the grid. "
            "Keys hold Fmaj9 for four bars, then Cmaj7 for four. Variation B stabs those chords on the grid.",
            LIMIT + " The 3+3+2 pattern is an accent grid. It does not change the meter.",
            "Fmaj9 is F A C E G for four bars, then Cmaj7 is C E G B for four bars. Both variations use those chords.",
            four,
            [
                {"name": "Pads", "start_bar": 0, "bars": 8},
                {"name": "Lines", "start_bar": 8, "bars": 8},
                {"name": "Full", "start_bar": 16, "bars": 8},
                {"name": "Lead", "start_bar": 24, "bars": 8},
            ],
            ["Fmaj9", "Cmaj7"],
            [4, 4],
            [],
            SHARP,
            {"drums": [16, 24], "bass": [0, 16], "keys": [0, 8, 16], "lead": [8, 24], "counterline": [8, 16]},
            {"a": grouped_a, "b": grouped_b},
        ),
        kit_record(
            "k04", "k04-climb", "Climb", 116, "Bb", "Bb major",
            [0, 2, 3, 5, 7, 9, 10], 11604,
            "Half-time snare on beat 3, with the kick on beat 1 and the and of 2. "
            "The lead climbs by step and then by third. The counterline descends in the same bars. "
            "Keys enter on the and of beat 1: Bbmaj7, Gm9, Ebmaj9, F9. "
            "Variation B shortens the keys and moves the lead onto offbeats.",
            LIMIT + " Bass variation B has one flagged B2.",
            "Bbmaj7 is Bb D F A for two bars, Gm9 is G Bb D F A for two, Ebmaj9 is Eb G Bb D F for two, then F9 is F A C Eb G for two. Both variations use those chords.",
            two,
            [
                {"name": "Bass", "start_bar": 0, "bars": 8},
                {"name": "Climb", "start_bar": 8, "bars": 8},
                {"name": "Keys", "start_bar": 16, "bars": 8},
                {"name": "Drums", "start_bar": 24, "bars": 8},
            ],
            ["Bbmaj7", "Gm9", "Ebmaj9", "F9"],
            [2, 2, 2, 2],
            ["Bass variation B includes one B2, flagged, as a chromatic approach to Bb2. It is outside Bb major and it is not in the keys."],
            FLAT,
            {"drums": [8, 24], "bass": [0, 8, 24], "keys": [0, 16], "lead": [8, 16], "counterline": [16, 24]},
            {"a": climb_a, "b": climb_b},
        ),
    ]


def events_k01(variation):
    if variation == "a":
        drums = drum_grid(
            [(0, 36, 1, 104), (7, 36, 1, 88), (10, 36, 1, 96), (4, 38, 1, 108), (12, 38, 1, 100), (15, 38, 1, 48), (2, 42, 1, 70), (6, 42, 1, 66), (10, 42, 1, 64), (14, 42, 1, 68)],
            {0: [(0, 49, 4, 90)]},
        )
        bass = [
            n(0, 0, 3, 38, 96), n(0, 4, 2, 45, 84), n(0, 8, 2, 41, 80), n(0, 12, 3, 38, 90),
            n(1, 2, 4, 38, 88), n(1, 8, 3, 48, 86), n(1, 12, 3, 45, 82),
            n(2, 0, 2, 43, 98), n(2, 3, 2, 50, 84), n(2, 6, 3, 47, 80), n(2, 10, 4, 43, 92),
            n(3, 0, 6, 41, 86), n(3, 8, 2, 43, 80), n(3, 12, 4, 38, 90),
            n(4, 1, 3, 36, 94), n(4, 5, 3, 43, 82), n(4, 10, 3, 40, 84), n(4, 14, 2, 36, 78),
            n(5, 0, 6, 36, 90), n(5, 8, 2, 47, 76), n(5, 11, 4, 43, 84),
            n(6, 0, 4, 38, 96), n(6, 6, 2, 45, 80), n(6, 9, 3, 41, 78), n(6, 13, 2, 38, 88),
            n(7, 0, 6, 45, 86), n(7, 8, 8, 38, 94),
        ]
        lead = [
            n(0, 0, 2, 62, 96), n(0, 2, 2, 65, 88), n(0, 4, 2, 69, 92),
            n(1, 0, 1, 62, 90), n(1, 1, 1, 65, 84), n(1, 2, 1, 69, 88), n(1, 3, 3, 72, 100),
            n(2, 4, 2, 69, 86), n(2, 6, 2, 65, 80), n(2, 8, 3, 62, 84),
            n(3, 8, 2, 72, 90), n(3, 10, 2, 69, 82), n(3, 12, 2, 65, 78),
            n(4, 0, 4, 64, 96), n(4, 4, 2, 67, 84), n(4, 6, 4, 71, 92),
            n(5, 0, 2, 72, 88), n(5, 4, 2, 71, 80), n(5, 8, 4, 67, 84), n(5, 14, 2, 64, 76),
            n(6, 0, 2, 62, 98), n(6, 3, 2, 65, 86), n(6, 6, 2, 69, 90), n(6, 9, 4, 72, 96),
            n(7, 4, 6, 69, 84), n(7, 12, 4, 62, 92),
        ]
        counter = [
            n(0, 8, 2, 60, 78), n(0, 10, 2, 57, 72), n(0, 12, 3, 53, 70),
            n(1, 8, 3, 59, 76), n(1, 12, 2, 55, 68),
            n(2, 0, 3, 52, 74), n(2, 12, 3, 50, 70),
            n(3, 0, 4, 48, 72), n(3, 4, 3, 55, 68),
            n(4, 10, 3, 60, 80), n(4, 14, 2, 57, 70),
            n(5, 6, 2, 59, 74), n(5, 10, 3, 55, 68),
            n(6, 13, 3, 53, 76),
            n(7, 0, 3, 50, 72), n(7, 10, 4, 48, 80),
        ]
    else:
        drums = drum_grid([(0, 36, 1, 100), (8, 36, 1, 92), (4, 38, 1, 110), (6, 38, 1, 70), (12, 38, 1, 104), (0, 46, 2, 74), (8, 46, 2, 70)])
        bass = [
            n(0, 0, 6, 45, 90), n(0, 8, 8, 38, 96),
            n(1, 0, 4, 41, 84), n(1, 6, 4, 48, 80), n(1, 12, 4, 45, 86),
            n(2, 2, 6, 43, 94), n(2, 10, 6, 50, 82),
            n(3, 0, 8, 47, 78), n(3, 8, 8, 43, 88),
            n(4, 0, 5, 40, 90), n(4, 6, 4, 36, 86), n(4, 12, 4, 43, 80),
            n(5, 0, 8, 48, 84), n(5, 8, 8, 40, 90),
            n(6, 4, 6, 38, 92), n(6, 12, 4, 41, 78),
            n(7, 0, 4, 50, 80), n(7, 6, 10, 38, 96),
        ]
        lead = [
            n(0, 2, 3, 69, 94), n(0, 6, 2, 67, 82), n(0, 9, 3, 64, 86),
            n(1, 0, 4, 62, 90), n(1, 6, 2, 65, 78), n(1, 10, 4, 60, 84),
            n(2, 0, 2, 71, 92), n(2, 3, 2, 69, 80), n(2, 8, 4, 64, 88),
            n(3, 2, 3, 67, 84), n(3, 8, 4, 62, 90),
            n(4, 4, 2, 72, 96), n(4, 8, 2, 71, 84), n(4, 12, 3, 67, 80),
            n(5, 0, 6, 64, 92), n(5, 8, 4, 60, 78),
            n(6, 2, 2, 74, 98), n(6, 5, 2, 72, 86), n(6, 8, 3, 69, 82), n(6, 12, 3, 65, 88),
            n(7, 0, 8, 62, 94),
        ]
        counter = [
            n(0, 12, 4, 55, 74),
            n(1, 0, 3, 59, 70), n(1, 14, 2, 53, 66),
            n(2, 5, 3, 57, 76), n(2, 12, 4, 52, 68),
            n(3, 0, 5, 50, 72), n(3, 10, 4, 55, 70),
            n(4, 0, 3, 60, 78), n(4, 15, 1, 57, 64),
            n(5, 4, 3, 52, 74), n(5, 12, 4, 48, 80),
            n(6, 0, 2, 59, 76), n(6, 15, 1, 55, 66),
            n(7, 8, 6, 53, 78),
        ]
    return {"drums": drums, "bass": bass, "lead": lead, "counterline": counter}


def events_k02(variation):
    if variation == "a":
        drums = drum_grid([(0, 36, 1, 108), (3, 36, 1, 84), (8, 36, 1, 100), (11, 36, 1, 80), (4, 38, 1, 112), (12, 38, 1, 106), (0, 42, 1, 72), (2, 42, 1, 60), (4, 42, 1, 68), (6, 42, 1, 58), (8, 42, 1, 70), (10, 42, 1, 58), (12, 42, 1, 66), (14, 42, 1, 56)])
        bass = [
            n(0, 0, 3, 45, 100), n(0, 4, 2, 52, 82), n(0, 7, 3, 40, 78), n(0, 12, 3, 45, 92),
            n(1, 0, 2, 47, 84), n(1, 3, 4, 49, 80), n(1, 8, 3, 45, 90), n(1, 12, 4, 40, 76),
            n(2, 0, 4, 38, 98), n(2, 6, 2, 42, 80), n(2, 9, 3, 45, 84), n(2, 13, 3, 50, 88),
            n(3, 0, 5, 42, 86), n(3, 6, 4, 38, 90), n(3, 12, 4, 45, 82),
            n(4, 0, 2, 47, 100), n(4, 3, 3, 42, 80), n(4, 8, 4, 38, 86), n(4, 13, 3, 47, 90),
            n(5, 1, 5, 45, 84), n(5, 8, 3, 49, 78), n(5, 12, 4, 47, 92),
            n(6, 0, 3, 40, 98), n(6, 4, 3, 47, 82), n(6, 8, 2, 43, 76), n(6, 11, 4, 40, 90),
            n(7, 0, 6, 45, 86), n(7, 8, 8, 40, 96),
        ]
        lead = [
            n(0, 0, 2, 69, 100), n(0, 2, 2, 71, 88), n(0, 4, 2, 73, 92), n(0, 8, 4, 76, 96),
            n(2, 0, 2, 74, 94), n(2, 2, 2, 73, 84), n(2, 4, 3, 71, 80), n(2, 8, 4, 69, 90),
            n(4, 2, 2, 71, 98), n(4, 4, 2, 74, 86), n(4, 6, 2, 76, 90), n(4, 10, 4, 78, 96),
            n(6, 0, 3, 76, 92), n(6, 4, 2, 74, 80), n(6, 8, 2, 71, 84), n(6, 12, 3, 69, 88),
        ]
        counter = [
            n(1, 0, 3, 64, 82), n(1, 4, 2, 67, 74), n(1, 8, 4, 62, 78),
            n(3, 2, 2, 66, 80), n(3, 6, 2, 64, 72), n(3, 10, 4, 61, 76),
            n(5, 0, 4, 71, 84), n(5, 6, 3, 67, 74), n(5, 12, 3, 64, 70),
            n(7, 0, 2, 69, 86), n(7, 4, 4, 66, 78), n(7, 10, 4, 62, 80),
        ]
    else:
        drums = drum_grid([(0, 36, 1, 102), (10, 36, 1, 90), (13, 36, 1, 84), (4, 38, 1, 110), (7, 38, 1, 72), (12, 38, 1, 104), (14, 38, 1, 68), (1, 42, 1, 64), (5, 42, 1, 60), (9, 42, 1, 66), (13, 42, 1, 58)])
        bass = [
            n(0, 0, 8, 40, 88), n(0, 8, 8, 45, 100),
            n(1, 0, 4, 49, 80), n(1, 4, 6, 47, 84), n(1, 12, 4, 45, 90),
            n(2, 0, 10, 50, 94), n(2, 10, 6, 42, 78),
            n(3, 2, 6, 45, 86), n(3, 10, 6, 38, 92),
            n(4, 0, 4, 42, 90), n(4, 4, 4, 47, 84), n(4, 8, 8, 38, 96),
            n(5, 0, 8, 49, 80), n(5, 8, 8, 47, 88),
            n(6, 0, 5, 43, 92), n(6, 6, 4, 40, 80), n(6, 12, 4, 47, 86),
            n(7, 0, 16, 40, 100),
        ]
        lead = [
            n(0, 0, 3, 76, 96), n(0, 3, 3, 73, 84), n(0, 6, 2, 71, 80), n(0, 10, 3, 69, 88),
            n(1, 0, 6, 67, 82), n(1, 8, 3, 69, 90),
            n(2, 1, 3, 74, 94), n(2, 5, 3, 78, 86), n(2, 9, 4, 76, 80),
            n(3, 0, 4, 73, 88), n(3, 6, 4, 71, 76),
            n(4, 0, 2, 66, 92), n(4, 4, 2, 69, 84), n(4, 8, 4, 73, 90),
            n(5, 2, 6, 76, 86), n(5, 10, 4, 74, 78),
            n(6, 0, 3, 71, 96), n(6, 4, 3, 74, 84), n(6, 8, 3, 78, 90), n(6, 12, 3, 81, 94),
            n(7, 0, 8, 76, 88),
        ]
        counter = [
            n(0, 12, 4, 64, 74),
            n(1, 0, 3, 68, 70, True), n(1, 3, 5, 69, 84),
            n(2, 8, 4, 62, 72),
            n(3, 0, 4, 67, 78), n(3, 8, 4, 64, 70),
            n(4, 12, 4, 61, 76),
            n(5, 0, 6, 66, 80), n(5, 8, 4, 62, 72),
            n(6, 6, 4, 59, 74),
            n(7, 0, 4, 64, 82), n(7, 8, 6, 61, 76),
        ]
    return {"drums": drums, "bass": bass, "lead": lead, "counterline": counter}


def events_k03(variation):
    if variation == "a":
        drums = drum_grid([(0, 36, 1, 100), (8, 36, 1, 94), (6, 38, 1, 104), (14, 38, 1, 96), (3, 42, 1, 68), (11, 42, 1, 64)])
        bass = [
            n(0, 0, 3, 41, 96), n(0, 3, 3, 48, 80), n(0, 8, 3, 45, 84), n(0, 11, 5, 41, 90),
            n(1, 0, 3, 40, 82), n(1, 6, 2, 43, 76), n(1, 8, 3, 41, 88), n(1, 14, 2, 36, 74),
            n(2, 0, 6, 41, 94), n(2, 8, 3, 47, 80), n(2, 11, 5, 45, 86),
            n(3, 0, 8, 43, 84), n(3, 8, 8, 41, 96),
            n(4, 0, 3, 36, 98), n(4, 3, 3, 43, 82), n(4, 6, 2, 40, 78), n(4, 8, 3, 47, 86), n(4, 11, 5, 36, 92),
            n(5, 2, 4, 40, 80), n(5, 8, 8, 36, 94),
            n(6, 0, 3, 43, 86), n(6, 6, 5, 40, 78), n(6, 11, 5, 36, 90),
            n(7, 0, 16, 36, 100),
        ]
        lead = [
            n(0, 0, 2, 65, 96), n(0, 3, 2, 69, 84), n(0, 6, 2, 71, 90), n(0, 8, 2, 72, 86),
            n(1, 0, 3, 74, 92), n(1, 6, 2, 71, 80), n(1, 11, 3, 69, 84),
            n(2, 0, 2, 67, 88), n(2, 3, 2, 65, 78), n(2, 8, 4, 64, 90),
            n(3, 0, 6, 65, 94),
            n(4, 0, 2, 72, 98), n(4, 3, 2, 76, 86), n(4, 6, 2, 74, 82), n(4, 11, 3, 71, 88),
            n(5, 8, 5, 72, 84),
            n(6, 0, 3, 67, 90), n(6, 6, 2, 71, 80), n(6, 11, 4, 72, 92),
            n(7, 0, 8, 76, 86),
        ]
        counter = [
            n(0, 8, 8, 60, 74),
            n(1, 0, 8, 64, 70),
            n(2, 0, 6, 59, 76), n(2, 8, 8, 55, 68),
            n(3, 4, 8, 53, 72),
            n(4, 0, 8, 59, 78),
            n(5, 0, 10, 55, 70),
            n(6, 4, 6, 52, 74),
            n(7, 0, 12, 48, 80),
        ]
    else:
        drums = drum_grid([(0, 36, 1, 98), (6, 36, 1, 86), (11, 36, 1, 90), (8, 38, 1, 108), (15, 38, 1, 64), (0, 42, 1, 70), (4, 42, 1, 58), (8, 42, 1, 66), (12, 42, 1, 56)])
        bass = [
            n(0, 0, 14, 41, 92), n(0, 14, 2, 48, 70),
            n(1, 0, 16, 45, 88),
            n(2, 0, 8, 40, 84), n(2, 8, 8, 47, 80),
            n(3, 4, 12, 41, 96),
            n(4, 0, 10, 36, 98), n(4, 10, 6, 43, 76),
            n(5, 0, 16, 40, 86),
            n(6, 0, 6, 47, 82), n(6, 8, 8, 36, 94),
            n(7, 0, 8, 43, 80), n(7, 8, 8, 40, 88),
        ]
        lead = [
            n(0, 0, 6, 76, 94), n(0, 8, 6, 74, 82),
            n(1, 2, 6, 71, 88), n(1, 10, 4, 67, 76),
            n(2, 0, 8, 72, 92),
            n(3, 0, 4, 69, 80), n(3, 8, 6, 65, 86),
            n(4, 4, 4, 64, 90), n(4, 10, 4, 67, 78),
            n(5, 0, 8, 71, 94),
            n(6, 0, 4, 74, 84), n(6, 8, 6, 72, 80),
            n(7, 2, 10, 65, 96),
        ]
        counter = [
            n(0, 14, 2, 60, 70),
            n(1, 0, 4, 64, 76), n(1, 8, 4, 67, 68),
            n(2, 6, 4, 71, 74),
            n(3, 0, 8, 69, 72),
            n(4, 8, 6, 72, 80),
            n(5, 4, 4, 67, 70), n(5, 12, 4, 64, 66),
            n(6, 0, 6, 60, 78),
            n(7, 4, 8, 55, 74),
        ]
    return {"drums": drums, "bass": bass, "lead": lead, "counterline": counter}


def events_k04(variation):
    if variation == "a":
        drums = drum_grid(
            [(0, 36, 1, 106), (6, 36, 1, 90), (8, 38, 1, 112), (4, 42, 1, 68), (12, 42, 1, 64)],
            {0: [(0, 49, 4, 88)], 4: [(0, 49, 4, 84)]},
        )
        bass = [
            n(0, 0, 4, 46, 100), n(0, 6, 3, 41, 82), n(0, 10, 4, 50, 78), n(0, 14, 2, 46, 90),
            n(1, 0, 6, 45, 84), n(1, 8, 4, 41, 80), n(1, 12, 4, 46, 92),
            n(2, 0, 3, 43, 98), n(2, 4, 4, 46, 82), n(2, 10, 4, 38, 80), n(2, 14, 2, 43, 88),
            n(3, 0, 8, 41, 86), n(3, 8, 8, 43, 94),
            n(4, 0, 4, 39, 100), n(4, 5, 3, 46, 80), n(4, 10, 4, 43, 84), n(4, 14, 2, 39, 78),
            n(5, 0, 5, 46, 86), n(5, 6, 4, 50, 80), n(5, 12, 4, 43, 90),
            n(6, 0, 3, 41, 98), n(6, 4, 3, 45, 82), n(6, 8, 3, 48, 76), n(6, 12, 4, 41, 92),
            n(7, 0, 8, 43, 84), n(7, 8, 8, 46, 96),
        ]
        lead = [
            n(0, 0, 2, 70, 98), n(0, 2, 2, 72, 86), n(0, 4, 4, 74, 92),
            n(1, 0, 2, 75, 88), n(1, 4, 2, 77, 84), n(1, 8, 4, 74, 80),
            n(2, 0, 2, 67, 90), n(2, 3, 2, 70, 82), n(2, 6, 3, 74, 88), n(2, 10, 4, 77, 94),
            n(3, 0, 4, 79, 86), n(3, 6, 4, 74, 78), n(3, 12, 3, 70, 84),
            n(4, 0, 3, 75, 96), n(4, 4, 2, 77, 84), n(4, 8, 4, 79, 90),
            n(5, 0, 6, 81, 92), n(5, 8, 4, 77, 80),
            n(6, 2, 2, 77, 98), n(6, 5, 2, 81, 86), n(6, 8, 2, 72, 82), n(6, 12, 3, 70, 88),
            n(7, 0, 8, 70, 94),
        ]
        counter = [
            n(0, 8, 4, 65, 76), n(0, 12, 3, 62, 70),
            n(1, 0, 4, 58, 74), n(1, 8, 4, 55, 68),
            n(2, 8, 4, 62, 78), n(2, 12, 4, 58, 70),
            n(3, 0, 6, 55, 72), n(3, 8, 6, 51, 66),
            n(4, 4, 4, 65, 80), n(4, 10, 4, 62, 72),
            n(5, 0, 6, 58, 74), n(5, 8, 6, 55, 68),
            n(6, 0, 4, 63, 76), n(6, 6, 4, 60, 70), n(6, 12, 4, 57, 66),
            n(7, 0, 8, 53, 80),
        ]
    else:
        drums = drum_grid([(0, 36, 1, 104), (12, 36, 1, 88), (8, 38, 1, 110), (11, 38, 1, 74), (2, 46, 2, 72), (10, 46, 2, 66)])
        bass = [
            n(0, 0, 8, 41, 90), n(0, 8, 8, 46, 100),
            n(1, 0, 4, 50, 78), n(1, 4, 4, 45, 82), n(1, 8, 8, 43, 88),
            n(2, 0, 6, 43, 96), n(2, 6, 4, 38, 80), n(2, 12, 4, 46, 86),
            n(3, 2, 6, 41, 84), n(3, 10, 6, 43, 90),
            n(4, 0, 10, 39, 98), n(4, 10, 6, 46, 80),
            n(5, 0, 8, 43, 86), n(5, 8, 8, 41, 92),
            n(6, 0, 4, 47, 70, True), n(6, 4, 6, 46, 100), n(6, 12, 4, 41, 84),
            n(7, 0, 16, 46, 102),
        ]
        lead = [
            n(0, 2, 2, 74, 94), n(0, 6, 2, 70, 82), n(0, 10, 4, 65, 88),
            n(1, 2, 4, 77, 90), n(1, 8, 4, 72, 78),
            n(2, 0, 3, 79, 96), n(2, 4, 3, 74, 84), n(2, 8, 4, 70, 80),
            n(3, 4, 6, 67, 86),
            n(4, 2, 2, 75, 92), n(4, 6, 2, 79, 84), n(4, 12, 3, 81, 90),
            n(5, 0, 8, 77, 82),
            n(6, 6, 4, 72, 94), n(6, 12, 3, 67, 78),
            n(7, 0, 4, 70, 96), n(7, 8, 6, 65, 84),
        ]
        counter = [
            n(0, 0, 2, 58, 72), n(0, 14, 2, 62, 68),
            n(1, 0, 6, 65, 76), n(1, 12, 4, 60, 70),
            n(2, 12, 4, 55, 74),
            n(3, 0, 4, 58, 78), n(3, 8, 6, 51, 66),
            n(4, 0, 8, 63, 80),
            n(5, 2, 4, 58, 72), n(5, 10, 4, 55, 68),
            n(6, 0, 5, 53, 76), n(6, 10, 4, 58, 70),
            n(7, 2, 10, 58, 82),
        ]
    return {"drums": drums, "bass": bass, "lead": lead, "counterline": counter}


BUILDERS = {"k01": events_k01, "k02": events_k02, "k03": events_k03, "k04": events_k04}


def _sig(notes):
    return tuple((note["performed_start"], note["pitch"], note["duration"]) for note in notes)


def _attacks(notes):
    return tuple(note["performed_start"] for note in notes)


def is_uniform_transpose(left, right):
    if len(left) != len(right):
        return False
    paired = list(zip(left, right))
    if any(a["performed_start"] != b["performed_start"] or a["duration"] != b["duration"] for a, b in paired):
        return False
    deltas = {b["pitch"] - a["pitch"] for a, b in paired}
    return len(deltas) == 1


def assert_voicings(kit, part):
    regions = kit["voicings"][part["variation"]]
    for region in regions:
        assert_chord_name(region["name"], region["pitches"])
        start = region["start_bar"] * BAR
        end = (region["start_bar"] + region["bars"]) * BAR
        inside = [note for note in part["notes"] if start <= note["performed_start"] < end]
        if not inside:
            raise ValueError(f"{part['id']} has no keys in {region['name']}")
        allowed = set(region["pitches"])
        if any(note["pitch"] not in allowed for note in inside):
            raise ValueError(f"{part['id']} {region['name']} uses a pitch outside the named voicing")
        got = {note["pitch"] % 12 for note in inside}
        need = {pitch % 12 for pitch in region["pitches"]}
        if got != need:
            raise ValueError(f"{part['id']} {region['name']} pcs {sorted(got)} != {sorted(need)}")
    covered = []
    for region in regions:
        covered.append((region["start_bar"] * BAR, (region["start_bar"] + region["bars"]) * BAR))
    for note in part["notes"]:
        if not any(start <= note["performed_start"] < end for start, end in covered):
            raise ValueError(f"{part['id']} note {note['pitch']} is outside a named chord")


def assert_collections(kit_rows, parts):
    allowed = {kit["id"]: set(kit["pitch_classes"]) for kit in kit_rows}
    for part in parts:
        if part["role"] == "drums":
            continue
        pool = allowed[part["kit_id"]]
        for note in part["notes"]:
            inside = (note["pitch"] % 12) in pool
            if note["departure"] and inside:
                raise ValueError(f"{part['id']} departure {note['pitch']} is inside the collection")
            if not note["departure"] and not inside:
                raise ValueError(f"{part['id']} note {note['pitch']} left the collection")


def assert_identities(parts):
    by_role = {}
    for part in parts:
        by_role.setdefault(part["role"], {}).setdefault(part["kit_id"], {})[part["variation"]] = part
    report = []
    for role, kits_map in by_role.items():
        seen = {}
        seen_parts = {}
        for kit_id, versions in kits_map.items():
            left = versions["a"]["notes"]
            right = versions["b"]["notes"]
            if _sig(left) == _sig(right):
                raise ValueError(f"{kit_id} {role} variations match")
            if is_uniform_transpose(left, right):
                raise ValueError(f"{kit_id} {role} variation B is only a transpose of A")
            if all(a["velocity"] != b["velocity"] for a, b in zip(left, right)) and _sig(left) == tuple(
                (note["performed_start"], note["pitch"], note["duration"]) for note in left
            ) and len(left) == len(right) and all(
                left[i]["performed_start"] == right[i]["performed_start"]
                and left[i]["pitch"] == right[i]["pitch"]
                and left[i]["duration"] == right[i]["duration"]
                for i in range(len(left))
            ):
                raise ValueError(f"{kit_id} {role} variation B changes only velocity")
            attacks = _attacks(left)
            if attacks in seen:
                raise ValueError(f"{role} variation A attack tuple repeats {seen[attacks]} and {kit_id}")
            for other_id, other in seen_parts.items():
                if is_uniform_transpose(left, other):
                    raise ValueError(f"{role} variation A is a transpose of {other_id} and {kit_id}")
            seen[attacks] = kit_id
            seen_parts[kit_id] = left
            report.append({
                "kit_id": kit_id,
                "role": role,
                "a_notes": len(left),
                "b_notes": len(right),
                "a_attacks": len(set(attacks)),
            })
    by_kit = {}
    for part in parts:
        by_kit.setdefault(part["kit_id"], {}).setdefault(part["variation"], []).append(part)
    for kit_id, versions in by_kit.items():
        for variation, group in versions.items():
            pitched = [part for part in group if part["role"] in PITCHED]
            for index, left in enumerate(pitched):
                for right in pitched[index + 1:]:
                    if _sig(left["notes"]) == _sig(right["notes"]) or is_uniform_transpose(left["notes"], right["notes"]):
                        raise ValueError(f"{kit_id} {variation} {left['role']} matches {right['role']}")
    return {
        "rows": report,
        "method": (
            "For each core role, variation A and variation B differ in pitch and rhythm, "
            "not only in velocity, and B is not a uniform transpose of A. "
            "Variation A attack-time tuples are unique across the four kits, and variation A "
            "is not a uniform transpose of the same role in another kit. "
            "Within a kit, bass, keys, lead, and counterline are not copies or uniform transposes of each other."
        ),
    }


def _shift_notes(source, bar_offset):
    shift = bar_offset * BAR
    shifted = []
    for note in source["notes"]:
        start = note["performed_start"] + shift
        shifted.append({
            "nominal_start": start,
            "offset": 0,
            "performed_start": start,
            "duration": note["duration"],
            "pitch": note["pitch"],
            "velocity": note["velocity"],
            "channel": note["channel"],
            "departure": note["departure"],
        })
    return shifted


def build_arrangement(kit, by_id):
    container = kit["arrangement_bars"] * BAR
    tracks = [{"name": "Conductor", "source_part": None, "channel": None, "placements": [], "notes": []}]
    for role in ROLE_ORDER:
        source = by_id[f"{kit['id']}.{role}.a"]
        notes = []
        for offset in kit["placements"][role]:
            notes.extend(_shift_notes(source, offset))
        notes.sort(key=lambda note: (note["performed_start"], note["pitch"]))
        for note in notes:
            end = note["performed_start"] + note["duration"]
            if end > container:
                raise ValueError(f"{kit['id']} {role} arrangement boundary")
        tracks.append({
            "name": ROLE_NAME[role],
            "source_part": source["id"],
            "channel": source["channel"],
            "placements": list(kit["placements"][role]),
            "notes": notes,
        })
    path = "midi/arrangement.mid" if kit["id"] == "k01" else f"midi/{kit['slug']}/arrangement.mid"
    return {
        "id": f"{kit['id']}-arrangement-a",
        "kit_id": kit["id"],
        "path": path,
        "format": 1,
        "container_ticks": container,
        "container_bars": 32,
        "bpm": kit["bpm"],
        "tempo_us": kit["tempo_us"],
        "meter": "4/4",
        "description": (
            f"{kit['title']} variation A arranged over 32 bars. "
            "Each musical track is one or more copies of the 8-bar part, placed at the listed bar offsets."
        ),
        "tracks": tracks,
    }


def compose():
    kit_rows = kits()
    if len(kit_rows) != 4:
        raise ValueError("expected four kits")
    if [kit["bpm"] for kit in kit_rows] != [104, 128, 92, 116]:
        raise ValueError("tempos drifted")
    parts = []
    for kit in kit_rows:
        for variation in ("a", "b"):
            events = BUILDERS[kit["id"]](variation)
            if set(events) != set(ROLE_ORDER) - {"keys"}:
                raise ValueError(kit["id"])
            for role in ROLE_ORDER:
                part = make(kit, role, variation)
                if role == "keys":
                    regions = kit["voicings"][variation]
                    if "stabs" in regions[0]:
                        add_events(part, stab_regions(regions))
                    else:
                        add_events(part, region_holds(regions))
                else:
                    add_events(part, events[role])
                finished = part.finish()
                if role == "keys":
                    assert_voicings(kit, finished)
                parts.append(finished)
    assert_collections(kit_rows, parts)
    identity = assert_identities(parts)
    by_id = {part["id"]: part for part in parts}
    arrangements = [build_arrangement(kit, by_id) for kit in kit_rows]
    preview = arrangements[0]
    if preview["kit_id"] != "k01":
        raise ValueError("preview arrangement is not Relay")
    for track in preview["tracks"]:
        if track["source_part"] and 8 not in track["placements"]:
            raise ValueError(f"{track['source_part']} is missing from the preview window")
    core = [part for part in parts if part["core"]]
    refs = [part for part in parts if not part["core"]]
    if len(core) != 40 or refs:
        raise ValueError((len(core), len(refs)))
    catalog_kits = []
    for kit in kit_rows:
        catalog_kits.append({key: kit[key] for key in (
            "id", "slug", "title", "bpm", "tempo_us", "effective_bpm", "part_bars", "arrangement_bars",
            "bars", "meter", "bar_ticks", "tonic", "tonal_reference", "collection_name", "pitch_classes",
            "departures", "seed", "identity", "limitations", "harmonic_rhythm", "phrases",
            "arrangement_phrases", "changes", "change_bars", "spell", "placements", "voicings",
            "stochastic_draws",
        )})
    catalog = {
        "pack_id": PACK_ID,
        "pack_name": PACK_NAME,
        "catalog_version": GENERATOR_VERSION,
        "generator_version": GENERATOR_VERSION,
        "ppq": PPQ,
        "c4": 60,
        "meter": {"numerator": 4, "denominator": 4, "bar_ticks": BAR},
        "container_plan": "Core parts are 8 bars. Arrangements are 32 bars. Lengths were fixed before the notes.",
        "creative_direction": (
            "Rhythmic interaction, motif development, controlled harmonic movement, and instrumental dialogue. "
            "The BPM range is a project choice, not a claim that these files are authentic genre productions."
        ),
        "note_policy": "Note-only MIDI. No program changes, controllers, pitch bend, aftertouch, or samples are encoded.",
        "microtiming": "offset is 0; performed_start = nominal_start",
        "stochastic_draws": 0,
        "seed_meaning": "Seeds identify kits. Nothing is random.",
        "core_part_count": 40,
        "reference_part_count": 0,
        "reference_note": "There is no reference-only part. All five roles are core. The arrangements reuse those files.",
        "instruments": {
            "drums": "Kit: kick, snare, closed hat, open hat, and crash on channel 10. No choke or other controller is written.",
            "bass": "Electric bass, monophonic. Slides are not encoded.",
            "keys": "Chord voicings intended for an electric piano. Sustain pedal is not encoded. Each note ends at note-off.",
            "lead": "Monophonic lead. Pitch bend is not encoded.",
            "counterline": "A second monophonic line. It is written against the lead and it is not a copy of the lead.",
        },
        "drum_map": {str(pitch): name for pitch, name in DRUM_MAP.items()},
        "percussion_map": {},
        "drum_channel": 10,
        "range_statement": (
            "Drums use channel 10 and the map in this catalog. There is no separate percussion part. "
            "Bass is monophonic, MIDI 28 to 55. Keys are MIDI 48 to 81, at most five notes. "
            "Lead is monophonic, MIDI 60 to 84. Counterline is monophonic, MIDI 48 to 81. C4 is 60."
        ),
        "kits": catalog_kits,
        "parts": [{
            "id": part["id"],
            "kit_id": part["kit_id"],
            "role": part["role"],
            "variation": part["variation"],
            "core": part["core"],
            "channel": part["channel"],
            "path": part["path"],
            "notes": len(part["notes"]),
            "container_bars": part["container_bars"],
            "bpm": part["bpm"],
            "monophonic": part["monophonic"],
        } for part in parts],
        "arrangements": [{
            "id": item["id"],
            "kit_id": item["kit_id"],
            "path": item["path"],
            "bpm": item["bpm"],
            "container_bars": item["container_bars"],
            "description": item["description"],
            "placements": {track["source_part"]: track["placements"] for track in item["tracks"] if track["source_part"]},
        } for item in arrangements],
        "arrangement": {
            "id": preview["id"],
            "path": preview["path"],
            "kit_id": "k01",
            "container_bars": 32,
            "description": preview["description"],
        },
        "preview": {
            "kit_id": "k01",
            "title": "Relay",
            "bpm": 104,
            "musical_bars": "9-16",
            "start_bar_index": 8,
            "end_bar_index": 16,
            "start_tick": 8 * BAR,
            "end_tick": 16 * BAR,
            "variation": "a",
            "arrangement_path": preview["path"],
            "statement": "Bars 9-16 of the Relay arrangement. Eight bars at 104 BPM. All five variation A parts.",
        },
        "preview_part_ids": [f"k01.{role}.a" for role in ROLE_ORDER],
        "stack_warning": (
            "Use either the combined arrangement or the separate parts. "
            "Do not stack the part files on top of the combined file."
        ),
    }
    score = {
        "pack_id": PACK_ID,
        "generator_version": GENERATOR_VERSION,
        "ppq": PPQ,
        "parts": parts,
        "arrangements": arrangements,
        "arrangement": preview,
        "identity_check": identity,
    }
    return {"catalog": catalog, "score": score}
