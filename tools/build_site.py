"""Package the GitHub Pages site with a Posto Umbra release ROM."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
OUTPUT = ROOT / "build" / "site"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, default=ROOT / "build" / "posto-umbra.rom")
    parser.add_argument("--release", default="local")
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    if len(rom) != 32 * 1024 or not rom.startswith(b"AB"):
        parser.error("a ROM precisa ter 32 KiB e um cabeçalho de cartucho MSX")

    shutil.copytree(SITE, OUTPUT, dirs_exist_ok=True)
    assets = OUTPUT / "assets"
    for name in ("title.png", "gameplay.png", "map.png", "legend.png"):
        shutil.copy2(ROOT / "docs" / "screenshots" / name, assets / name)
    shutil.copytree(ROOT / "docs" / "packaging", OUTPUT / "art", dirs_exist_ok=True)
    (OUTPUT / "posto-umbra.rom").write_bytes(rom)
    rom_id = hashlib.sha256(rom).hexdigest()[:16]
    rom_directory = OUTPUT / "rom" / rom_id
    rom_directory.mkdir(parents=True, exist_ok=True)
    (rom_directory / "posto-umbra.rom").write_bytes(rom)
    metadata = {"version": args.release, "romId": rom_id}
    (OUTPUT / "release.json").write_text(json.dumps(metadata) + "\n", encoding="utf-8")
    print(f"{OUTPUT.relative_to(ROOT)}: site com a ROM {args.release}")


if __name__ == "__main__":
    main()
