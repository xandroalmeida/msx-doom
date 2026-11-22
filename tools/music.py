"""Original gameplay scores for the two PSG voices available during combat."""

from opening import psg_period
from tables import data


# Each measure pairs a lead with a bass line. A dash holds the current pitch,
# a dot is a rest, and ! marks an accent. The tempo counts 1/300 second units
# per half step, so NTSC and PAL play at the same speed.
TRACKS = (
    ("Ecos do Depósito", 20, 16, (
        (". . A4 -   D5 - . F5    E5 - D5 .   A4 - . .",
         "D3 - . A2   D3 . F3 .   D3 - . A2   C3 . A2 ."),
        (". . F4 -   A4 - . C5    D5 - C5 .   F5 . E5 .",
         "A#2 - . F3   A#2 . D3 .   C3 - . G2   C3 . E3 ."),
        ("D5 - F5 .   A5 - G5 F5   E5 . D5 -   C5 . A4 .",
         "D3 . A2 D3   F3 . D3 .   G2 - . D3   G2 . C3 ."),
        ("F5 - E5 D5   C#5 - A4 .   E5 . G5 .   A4 - C#5 .",
         "A2 - . E3   A2 . C#3 .   A2 . E3 G3   C#3 . A2 ."),
        ("A4 - - .   . D5 - .   F5 - . .   E5 - C5 .",
         "D3 - - .   D3 - . .   A#2 - - .   C3 - . ."),
        ("D5 - - -   A4 - . .   C#5 - E5 .   D5 - - .",
         "D3 - . A2   F3 - . D3   A2 - C#3 .   D3 - - ."),
        ("A5 - G5 F5   E5 - F5 .   G5 . F5 E5   D5 - A4 .",
         "A#2 - . F3   D3 . F3 .   C3 . G3 E3   A2 . C#3 ."),
    ), (0, 1, 0, 3, 2, 1, 2, 3, 4, 4, 6, 5)),
    ("Forja Vermelha", 18, 14, (
        ("E5! . . F5 . E5   B4! . A#4 .   E5! . D5 B4",
         "E3! . E3 E3 . B2   E3! . F3 F3   E3! E3 . B2"),
        ("G5 . F5 E5 . G5   A5 - F5 .   D5! . C5 D5",
         "G2! . G2 D3 . G2   F2! . F3 .   D3! D3 . A2"),
        ("B4! E5 . G5 F5 E5   C5! . D5 C5   B4! . A#4 .",
         "E3 . E3 G3 . E3   C3! . C3 G2   B2! . F3 ."),
        ("E5 - . B4 . E5   F5 E5 . D5   B4 - . .",
         "E3! E3 . B2 E3 .   F3! . F3 .   E3! . B2 ."),
        (". . A#4 . B4 .   E5 - . .   G5! . F5 .",
         "E3 - - . E3 .   E3 - F3 .   G2 - F2 ."),
        ("A5! . G5 F5 E5 .   C6! . B5 A5   G5! F5 E5 .",
         "A2! . E3 A2 . E3   C3! . C3 G2   F2! . F3 B2"),
        ("E5! . E5 . . B4   F5! . D5 .   E5! - . .",
         "E3! . B2 E3 . E3   F3! . D3 .   E3! - - ."),
    ), (0, 1, 0, 2, 3, 1, 2, 0, 4, 4, 5, 2, 5, 3, 1, 6)),
    ("Núcleo de Vidro", 24, 12, (
        ("C#5 - . F#5 - .   E5 - C#5 . A4 .",
         "F#2 - . C#3 - .   F#3 - E3 . C#3 ."),
        ("A4 - . D5 - F#5   A5 - F#5 . E5 .",
         "D3 - . A2 - .   D3 . F#3 - A2 ."),
        ("D5 - E5 . F#5 .   B5 - A5 . F#5 .",
         "B2 - . F#3 - .   B2 . D3 - F#3 ."),
        ("G#5 - F5 . D5 .   C#5 - - . A4 .",
         "C#3 - . G#2 - .   C#3 . F3 - G#2 ."),
        ("F#5 - - . C#5 .   A4 - - . C#5 .",
         "F#2 - - - C#3 .   F#2 - - . F#3 ."),
        ("E5 - . G#5 - B5   G#5 . F#5 E5 C#5 .",
         "E3 - . B2 - .   E3 . G#3 - B2 ."),
        ("C#6 - A5 . F#5 .   E5 - C#5 . G#4 .",
         "D3 - . A2 - .   C#3 . F3 - G#2 ."),
        ("F#5! - - - C#5 .   A4 - C#5 . . .",
         "F#2! - . C#3 - .   F#2 - - . . ."),
    ), (0, 1, 2, 3, 0, 5, 2, 3, 4, 4, 1, 6, 3, 7)),
)


def gameplay_score():
    """Compile attack and decay frames as 12-bit period plus 4-bit volume."""
    profiles = ["game_music_tracks:"]
    scores = []
    for index, (name, tempo, steps, measures, order) in enumerate(TRACKS):
        label = f"game_music_{index}"
        profiles.extend((f"    dw {label}", f"    db {tempo}"))
        periods = [0, 0]
        frames = []
        for measure in order:
            voices = [line.split() for line in measures[measure]]
            if any(len(voice) != steps for voice in voices):
                raise ValueError(f"Compasso {measure + 1} incompleto em {name}.")
            for notes in zip(*voices):
                attack, decay = [], []
                for channel, token in enumerate(notes):
                    gain = (10, 8)[channel]
                    onset = token not in ("-", ".")
                    if onset:
                        pitch = token.rstrip("!")
                        periods[channel] = psg_period(pitch)
                        gain += token.endswith("!")
                    elif token == ".":
                        periods[channel] = 0
                    else:
                        gain -= 1
                    period = periods[channel]
                    attack.append((gain << 12) | period if period else 0)
                    decay.append(((gain - (3 if onset else 1)) << 12) | period if period else 0)
                frames.extend(attack + decay)
        scores.extend((data(label, (*frames, 0xFFFF), "dw"), f"{label}_end:"))
    return "\n".join((*profiles, *scores))
