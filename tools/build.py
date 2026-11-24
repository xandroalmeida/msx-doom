"""Assemble and pad the 32 KiB linear cartridge image."""

import argparse
from pathlib import Path
import struct
import subprocess
import sys

from levels import sector_data
from ending import ending_data
from opening import score_data
from music import gameplay_score
from tables import FONT, data, generate
from title_art import title_data

ROOT = Path(__file__).resolve().parents[1]
ROM_SIZE = 32 * 1024


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembler", default="pyz80", help="pyz80 executable or .py path")
    args = parser.parse_args()

    output = ROOT / "build"
    output.mkdir(exist_ok=True)
    source = output / "posto-umbra.generated.z80"
    modules = ("posto-umbra.z80", "combat.z80", "objects.z80", "menu.z80", "campaign.z80", "opening.z80")
    assembly = "\n".join((ROOT / "src" / module).read_text() for module in modules)
    late_modules = ("compass.z80", "mission.z80", "ending.z80")
    late_assembly = "\n".join((ROOT / "src" / module).read_text() for module in late_modules)
    music = (ROOT / "src" / "music.z80").read_text()
    source.write_text("\n".join((assembly, generate(), late_assembly, score_data(), ending_data(), title_data(data, FONT),
                                 music, gameplay_score(), sector_data(data), "rom_end:\n")))
    binary = output / "posto-umbra.bin"
    assembler = [args.assembler]
    if args.assembler.endswith(".py"):
        assembler.insert(0, sys.executable)

    try:
        subprocess.run(
            assembler + [
                f"--obj={binary}",
                f"--mapfile={output / 'posto-umbra.sym'}",
                str(source),
            ],
            cwd=output,
            check=True,
        )
    except FileNotFoundError:
        parser.exit(1, "Montador pyz80 indisponível. Instale pyz80 ou use --assembler.\n")

    code = binary.read_bytes()
    entry = struct.unpack_from("<H", code, 2)[0]
    if code[:2] != b"AB" or not 0x4010 <= entry < 0x8000:
        raise ValueError("Cabeçalho de cartucho MSX inválido.")
    if len(code) > ROM_SIZE:
        raise ValueError(f"O binário de {len(code)} bytes excede o cartucho de 32 KiB.")
    rom = output / "posto-umbra.rom"
    rom.write_bytes(code.ljust(ROM_SIZE, b"\xff"))
    print(f"{rom.relative_to(ROOT)}: {len(code)} / {ROM_SIZE} bytes usados")


if __name__ == "__main__":
    main()
