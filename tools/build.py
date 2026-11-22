"""Assemble and pad the 16 KiB cartridge image."""

import argparse
from pathlib import Path
import struct
import subprocess
import sys

from tables import generate

ROOT = Path(__file__).resolve().parents[1]
ROM_SIZE = 16 * 1024


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembler", default="pyz80", help="pyz80 executable or .py path")
    args = parser.parse_args()

    output = ROOT / "build"
    output.mkdir(exist_ok=True)
    source = output / "posto-umbra.generated.z80"
    modules = ("posto-umbra.z80", "combat.z80", "objects.z80", "menu.z80")
    assembly = "\n".join((ROOT / "src" / module).read_text() for module in modules)
    source.write_text(assembly + "\n" + generate())
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
    if code[:2] != b"AB" or not 0x4010 <= entry < 0x4000 + len(code):
        raise ValueError("Cabeçalho de cartucho MSX inválido.")
    if len(code) > ROM_SIZE:
        raise ValueError(f"O binário de {len(code)} bytes excede o cartucho de 16 KiB.")
    rom = output / "posto-umbra.rom"
    rom.write_bytes(code.ljust(ROM_SIZE, b"\xff"))
    print(f"{rom.relative_to(ROOT)}: {len(code)} / {ROM_SIZE} bytes usados")


if __name__ == "__main__":
    main()
