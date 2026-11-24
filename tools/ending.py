"""Ending screen: the radio room, the last transmission and the credits."""

from ending_art import COLS, ROWS, scene
from pack import pack
from tables import FONT, data

# The art fills rows 0–10. The two lower banks receive this font once per ink,
# so a text tile name is ink * glyph count + glyph. The middle bank keeps the
# art's lowest rows after the font.
INKS = {"W": 15, "Y": 11, "G": 14}
INK_ORDER = "WYG"
EXTRA_GLYPHS = {
    ".": "0000000000000c",
    ",": "00000000000c18",
    ">": "180c0603060c18",
    "<": "060c1830180c06",
    "#": "3f3f3f3f3f3f3f",
}
GLYPHS = {**FONT, **EXTRA_GLYPHS}

TX, RX = 0, 1
LABELS = ((TX, "W", "> POSTO UMBRA"), (RX, "Y", "< CENTRAL"))
LABEL_ROW, MESSAGE_ROW, COLUMN = 13, 15, 2
TEXT_ROWS = (12, 23)                # rows cleared before each message
# Messages alternate. Each one is typed alone, as if heard on the radio.
DIALOGUE = (
    (TX, "POSTO UMBRA CHAMANDO CENTRAL.", "CAMBIO."),
    (RX, "CENTRAL NA ESCUTA, UMBRA.", "PASSAMOS A NOITE OLHANDO", "PARA O FAROL."),
    (TX, "O POSTO FOI RECUPERADO.", "DOZE SETORES, TODOS LIMPOS.", "AS LUZES AINDA ESTAO ACESAS."),
    (RX, "RECEBIDO, ALTO E CLARO.", "A EQUIPE SOBE A SERRA", "AO AMANHECER."),
    (TX, "ENTENDIDO. FICO NA ESCUTA.", "POSTO UMBRA, DESLIGO."),
    (RX, "BOM TRABALHO, UMBRA.", "CENTRAL DESLIGA."),
)
PAUSE_LINE, PAUSE_READ, PAUSE_END = 4, 50, 60

CREDITS = (
    (12, "W", "POSTO UMBRA"),
    (13, "G", "UM JOGO ORIGINAL PARA MSX 1"),
    (15, "Y", "CRIACAO E PROGRAMACAO"),
    (16, "W", "ALEXANDRO ALMEIDA"),
    (18, "Y", "TRILHA SONORA"),
    (19, "W", "SINAL DE UMBRA  ECOS DO DEPOSITO"),
    (20, "W", "FORJA VERMELHA  NUCLEO DE VIDRO"),
    (21, "W", "VOZ NA SERRA"),
    (22, "W", "OBRIGADO POR JOGAR"),
    (23, "Y", "ESP VOLTAR AO INICIO"),
)
SKIP_HINT = (23, 21, "G", "ESP PULAR")


def ending_data():
    texts = [text for *_, text in LABELS] + [line for _, *lines in DIALOGUE for line in lines]
    texts += [text for *_, text in CREDITS] + [SKIP_HINT[3], "#"]
    used = sorted({char for text in texts for char in text} - {" "})
    missing = [char for char in used if char not in GLYPHS]
    if missing:
        raise ValueError(f"Sem glifo para {''.join(missing)} na tela final.")
    glyph = {" ": 0, **{char: index for index, char in enumerate(used, 1)}}
    stride = len(glyph)

    def tiles(text, ink):
        return [0 if char == " " else INK_ORDER.index(ink) * stride + glyph[char] for char in text]

    def block(row, column, names):
        offset = (row - 4) * 32 + column   # panels are relative to the view at row 4
        if not (ROWS < row < 24 and 0 <= column <= 32 - len(names) and names):
            raise ValueError("Texto da tela final fora da área de texto.")
        return [len(names), offset & 255, (offset >> 8) & 255, *names]

    script = []
    for index, (speaker, *lines) in enumerate(DIALOGUE):
        if index and speaker == DIALOGUE[index - 1][0]:
            raise ValueError("As mensagens do rádio devem alternar.")
        if MESSAGE_ROW + 2 * len(lines) > TEXT_ROWS[1]:
            raise ValueError("Mensagem longa demais.")
        script.append(0xFE | speaker)
        for row, line in zip(range(MESSAGE_ROW, 24, 2), lines):
            if len(line) > 32 - COLUMN:
                raise ValueError(f"Linha longa demais: {line}")
            if row > MESSAGE_ROW:
                script.append(128 | PAUSE_LINE)
            script += block(row, COLUMN, tiles(line, "WY"[speaker]))
        script.append(128 | (PAUSE_END if index == len(DIALOGUE) - 1 else PAUSE_READ))
    script.append(0)

    credits = []
    for row, ink, text in CREDITS:
        credits += block(row, (32 - len(text)) // 2, tiles(text, ink))
    credits.append(0)
    hint_row, hint_column, hint_ink, hint_text = SKIP_HINT
    hint = block(hint_row, hint_column, tiles(hint_text, hint_ink)) + [0]
    labels = [block(LABEL_ROW, COLUMN, tiles(text, ink)) + [0] for _, ink, text in LABELS]

    # Tile banks: the upper one holds art only, the lower ones the font.
    banks, names, channels = scene()
    art_base = len(INK_ORDER) * stride
    if art_base + len(banks[1]) - 1 > 256:
        raise ValueError("A fonte e a arte não cabem no banco do meio.")

    def art_name(row, local):
        return local if row < 8 or not local else art_base + local - 1

    font_patterns, font_colors = [], []
    for ink in INK_ORDER:
        for char in [" ", *used]:
            rows = bytes.fromhex(GLYPHS[char]) if char != " " else bytes(7)
            font_patterns += [row << 1 for row in rows] + [0]
            font_colors += [(INKS[ink] << 4) | 1] * 8

    def art_tiles(bank):
        ordered = sorted(bank, key=bank.get)
        patterns = [pattern for tile in ordered for pattern, _ in tile for _ in range(2)]
        colors = [color for tile in ordered for _, color in tile for _ in range(2)]
        return patterns, colors

    upper = art_tiles(banks[0])
    middle_art = art_tiles({tile: index for tile, index in banks[1].items() if index})
    middle = (font_patterns + middle_art[0], font_colors + middle_art[1])
    lower = (font_patterns, font_colors)

    channel_data = []
    for label, cells, frames in channels:
        values = [len(cells)]
        for row, col in cells:
            values += [(row * COLS + col) & 255, (row * COLS + col) >> 8]
        for frame in frames:
            values += [art_name(row, local) for (row, _), local in zip(cells, frame)]
        channel_data.append(data(f"ending_{label}", values))

    return "\n".join((
        f"ending_cursor: equ {tiles('#', 'W')[0]}",
        f"ending_text_top: equ {TEXT_ROWS[0] * 32}",
        f"ending_text_size: equ {(TEXT_ROWS[1] - TEXT_ROWS[0]) * 32}",
        f"ending_names_size: equ {ROWS * COLS}",
        data("ending_names", (art_name(row, local) for row, line in enumerate(names) for local in line)),
        *(data(f"ending_bank_{index}_{part}", pack(table))
          for index, bank in enumerate((upper, middle, lower))
          for part, table in zip(("patterns", "colors"), bank)),
        *channel_data,
        data("ending_labels", ("ending_label_tx", "ending_label_rx"), "dw"),
        data("ending_label_tx", labels[0]),
        data("ending_label_rx", labels[1]),
        data("ending_dialogue", script),
        data("ending_credits", credits),
        data("ending_skip", hint),
    ))
