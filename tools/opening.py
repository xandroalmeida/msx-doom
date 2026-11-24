"""Sinal de Umbra, the 7/8 title theme, and Voz na Serra, the ending theme, for the MSX PSG."""

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


def psg_period(note):
    semitone = "C C# D D# E F F# G G# A A# B".split().index(note[:-1])
    midi = 12 * (int(note[-1]) + 1) + semitone
    frequency = 440 * 2 ** ((midi - 69) / 12)
    period = round(PSG_CLOCK / (16 * frequency))
    if not 1 <= period <= 4095:
        raise ValueError(f"Nota fora do alcance do PSG: {note}")
    return period


# Voz na Serra plays after the last sector: the minor signal resolved in E major.
# Bars have sixteen steps. A dash holds the previous pitch at a lower volume.
ENDING_CHORDS = {
    "E": ("E4 G#4 B4 G#4", "E2 . E3 ."),
    "B": ("B3 D#4 F#4 D#4", "B1 . B2 ."),
    "C#m": ("C#4 E4 G#4 E4", "C#2 . C#3 ."),
    "A": ("A3 C#4 E4 C#4", "A1 . A2 ."),
}
ENDING_DRUMS = "12 .  05 .  08 .  05 .  12 .  12 .  08 .  05 05"
ENDING_BARS = (
    ("E", "G#4 - - -  B4 - - -  E5 - - -  - - - -"),
    ("B", "D#5 - - -  C#5 - - -  B4 - - -  - - - -"),
    ("C#m", "C#5 - - -  E5 - - -  G#5 - - -  F#5 - - -"),
    ("A", "E5 - - -  - - - -  C#5 - - -  B4 - - -"),
    ("A", "C#5 - - -  E5 - - -  A5 - - -  - - - -"),
    ("B", "G#5 - - -  F#5 - - -  D#5 - - -  F#5 - - -"),
)
ENDING_ORDER = (0, 1, 2, 3, 0, 1, 4, 5)
ENDING_STEPS = 8                   # each bar is stored as two shared half bars
HOLD = 0xFF


def score_data():
    periods = [0]
    notes = {".": 0}

    def note_id(note):
        if note == "-":
            return HOLD
        if note not in notes:
            notes[note] = len(periods)
            periods.append(psg_period(note))
        return notes[note]

    def events(lines, label):
        tracks = [line.split() for line in lines]
        if len({len(track) for track in tracks}) != 1:
            raise ValueError(f"Compasso incompleto: {label}")
        values = []
        for lead, harmony, bass, drums in zip(*tracks):
            noise = 0 if drums == "." else int(drums, 16)
            if not 0 <= noise <= 31:
                raise ValueError(f"Período de ruído inválido: {drums}")
            values.extend((note_id(lead), note_id(harmony), note_id(bass), noise))
        return values

    patterns = []
    for index, pattern in enumerate(PATTERNS):
        values = events(pattern, f"abertura {index}")
        if len(values) != 4 * STEPS_PER_BAR:
            raise ValueError(f"Compasso incompleto na abertura: {index}")
        patterns.append(data(f"intro_pattern_{index}", values))

    halves, ending_order = {}, []
    for bar in ENDING_ORDER:
        chord, lead = ENDING_BARS[bar]
        harmony, bass = ENDING_CHORDS[chord]
        values = events((lead, " ".join([harmony] * 4), " ".join([bass] * 4), ENDING_DRUMS), f"final {bar}")
        if len(values) != 8 * ENDING_STEPS:
            raise ValueError(f"O compasso final {bar} deve ter 16 passos.")
        for start in range(0, len(values), 4 * ENDING_STEPS):
            half = tuple(values[start:start + 4 * ENDING_STEPS])
            ending_order.append(halves.setdefault(half, f"ending_pattern_{len(halves)}"))
    if len(periods) >= HOLD:
        raise ValueError("Notas demais para a tabela de períodos.")

    return "\n".join((
        f"intro_bar_steps: equ {STEPS_PER_BAR}",
        f"ending_bar_steps: equ {ENDING_STEPS}",
        f"intro_hold: equ {HOLD}",
        data("intro_order", [*(f"intro_pattern_{index}" for index in ORDER), 0], "dw"),
        data("ending_order", [*ending_order, 0], "dw"),
        data("intro_periods", periods, "dw"),
        *patterns,
        *(data(label, half) for half, label in halves.items()),
    ))
