"""Byte-aligned LZ for data the cartridge unpacks into RAM before a VRAM upload.

Tokens: 00h ends the stream. 01h–7Fh copy that many literal bytes. A byte with
bit 7 set starts a match: bits 2–0 with the next byte hold the distance minus
1, so matches reach 2 KiB back. Bits 6–3 hold the length minus 3; the value 15
adds a third byte to the length, for runs of up to 273 bytes.
"""

MIN_MATCH, LONG_MATCH, MAX_MATCH, WINDOW = 3, 18, 273, 2048


def pack(data):
    data = bytes(data)
    out, literals = bytearray(), bytearray()

    def flush():
        for start in range(0, len(literals), 127):
            chunk = literals[start:start + 127]
            out.append(len(chunk))
            out.extend(chunk)
        literals.clear()

    starts = {}
    for position in range(len(data) - MIN_MATCH + 1):
        starts.setdefault(data[position:position + MIN_MATCH], []).append(position)

    def longest(i):
        best_length, best_distance = 0, 0
        for j in reversed(starts.get(data[i:i + MIN_MATCH], ())):
            if j >= i:
                continue
            if i - j > WINDOW:
                break
            length = 0
            while (length < MAX_MATCH and i + length < len(data)
                   and data[j + length] == data[i + length]):
                length += 1
            if length > best_length:
                best_length, best_distance = length, i - j
        return best_length, best_distance

    i = 0
    while i < len(data):
        length, distance = longest(i)
        # Defer a match when the next position starts a clearly longer one.
        if length >= MIN_MATCH and i + 1 < len(data) and longest(i + 1)[0] > length + 1:
            length = 0
        if length >= MIN_MATCH:
            flush()
            code = min(length - MIN_MATCH, 15)
            out.append(0x80 | code << 3 | (distance - 1) >> 8)
            out.append((distance - 1) & 255)
            if code == 15:
                out.append(length - LONG_MATCH)
            i += length
        else:
            literals.append(data[i])
            i += 1
    flush()
    out.append(0)
    if unpack(out) != data:
        raise ValueError("Falha na verificação da compactação.")
    return bytes(out)


def unpack(packed):
    out, i = bytearray(), 0
    while packed[i]:
        token = packed[i]
        if token < 0x80:
            out.extend(packed[i + 1:i + 1 + token])
            i += 1 + token
        else:
            distance = ((token & 7) << 8 | packed[i + 1]) + 1
            length = ((token >> 3) & 15) + MIN_MATCH
            i += 2
            if length == LONG_MATCH:
                length += packed[i]
                i += 1
            for _ in range(length):
                out.append(out[-distance])
    return bytes(out)
