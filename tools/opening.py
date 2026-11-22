"""Sinal de Umbra, an original title theme in 7/8 for the MSX PSG."""

from tables import data

# Each row has fourteen sixteenth notes: accents in groups of 3 + 2 + 2 eighths.
# The three lines are lead, harmony and bass. A fourth line gives noise periods.
PATTERNS = (
    (
        ".   .   .   C#5 .   .   B4  .   .   E5  .   .   D#5 .",
        "C#4 .   G#3 .   C#4 .   A3  .   E4  .   B3  .   F#4 .",
        "C#2 C#2 .   C#2 .   C#2 A2  .   A2  .   B2  B2  .   B2",
        "05  .   .   0c  .   .   12  .   08  .   05  .   0c  .",
    ),
    (
        "G#4 .   .   B4  .   D#5 C#5 .   G#4 .   E5  .   B4  .",
        "E4  .   B3  .   E4  .   F#4 .   C#4 .   G#3 .   D#4 .",
        "E2  .   E2  E2  .   B2  F#2 .   F#2 F#2 G#2 .   G#2 .",
        "05  .   0c  .   .   08  12  .   0c  .   05  .   12  .",
    ),
    (
        "C#5 .   E5  .   G#5 .   B5  .   G#5 E5  D#5 .   C#5 .",
        "G#3 C#4 .   G#3 .   C#4 A3  .   E4  .   B3  .   D#4 .",
        "C#2 C#2 .   C#2 C#2 .   A2  .   A2  A2  B2  .   B2  .",
        "05  .   0c  .   08  .   12  .   08  .   05  .   12  .",
    ),
    (
        "A5  .   G#5 E5  .   D#5 F#5 .   E5  C#5 G#4 .   B4  .",
        "A3  .   E4  .   A3  B3  F#4 .   C#4 .   G#3 .   D#4 .",
        "A2  A2  .   A2  .   B2  F#2 .   F#2 .   G#2 G#2 .   G#2",
        "05  .   0c  .   .   08  12  .   08  .   05  .   12  0c",
    ),
    (
        ".   .   .   G#4 .   .   .   .   C#5 .   .   G#4 .   .",
        "E3  E3  .   E3  .   E3  G#3 .   G#3 .   C#4 .   G#3 .",
        "E2  E2  .   E2  .   E2  G#2 .   G#2 .   C#2 .   G#2 .",
        "05  .   .   0c  .   .   12  .   .   .   05  .   12  .",
    ),
    (
        "E5  .   F#5 G#5 .   E5  B4  .   C#5 .   D#5 .   B4  G#4",
        "A3  .   E4  A3  .   E4  B3  .   F#4 .   G#3 .   D#4 .",
        "A2  .   A2  A2  .   A2  B2  .   B2  B2  G#2 .   G#2 .",
        "05  .   0c  .   08  .   12  .   08  .   05  .   12  0c",
    ),
    (
        "C#6 G#5 E5  .   C#5 .   F#5 C#5 B4  .   G#5 .   E5  D#5",
        "C#4 .   G#3 .   E4  .   F#4 .   C#4 .   B3  .   G#3 .",
        "C#2 C#2 .   C#2 C#2 .   F#2 .   F#2 F#2 B2  .   G#2 .",
        "05  08  .   0c  .   .   12  .   08  .   05  .   12  0c",
    ),
    (
        "C#5 .   .   .   .   .   G#4 .   .   .   C#5 .   .   .",
        "E4  .   .   .   .   .   D#4 .   .   .   G#3 .   .   .",
        "C#2 .   .   .   C#2 .   G#2 .   .   .   C#2 .   .   .",
        "05  .   .   .   08  .   12  .   .   .   05  .   .   .",
    ),
)
ORDER = (0, 1, 0, 1, 2, 3, 2, 5, 4, 4, 5, 3, 6, 6, 2, 7)
STEPS_PER_BAR = 14
PSG_CLOCK = 1_789_772.5


def score_data():
    periods = [0]
    notes = {".": 0}

    def note_id(note):
        if note not in notes:
            semitone = "C C# D D# E F F# G G# A A# B".split().index(note[:-1])
            midi = 12 * (int(note[-1]) + 1) + semitone
            frequency = 440 * 2 ** ((midi - 69) / 12)
            period = round(PSG_CLOCK / (16 * frequency))
            if not 1 <= period <= 4095:
                raise ValueError(f"Nota fora do alcance do PSG: {note}")
            notes[note] = len(periods)
            periods.append(period)
        return notes[note]

    patterns = []
    for index, pattern in enumerate(PATTERNS):
        tracks = [line.split() for line in pattern]
        if any(len(track) != STEPS_PER_BAR for track in tracks):
            raise ValueError(f"Compasso incompleto na abertura: {index}")
        events = []
        for lead, harmony, bass, drums in zip(*tracks):
            noise = 0 if drums == "." else int(drums, 16)
            if not 0 <= noise <= 31:
                raise ValueError(f"Período de ruído inválido: {drums}")
            events.extend((note_id(lead), note_id(harmony), note_id(bass), noise))
        patterns.append(data(f"intro_pattern_{index}", events))

    return "\n".join((
        f"intro_bar_steps: equ {STEPS_PER_BAR}",
        data("intro_order", [*(f"intro_pattern_{index}" for index in ORDER), 0], "dw"),
        data("intro_periods", periods, "dw"),
        *patterns,
    ))
