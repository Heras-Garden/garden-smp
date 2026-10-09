#!/usr/bin/env python3
"""Reduce Hera's Garden to obols, emerald blocks, leaves and flowers.

Run from the repo root: python tools/trim_resource_pack.py --apply
A backup is created before replacing the deployable ZIP.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import shutil
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "HerasGardenRP.zip"

# Flowers whose vanilla resource names don't include the word "flower".
FLOWERS = (
    "dandelion", "poppy", "blue_orchid", "allium", "azure_bluet",
    "tulip", "oxeye_daisy", "cornflower", "lily_of_the_valley",
    "wither_rose", "sunflower", "lilac", "rose_bush", "peony",
    "torchflower", "pitcher_plant", "spore_blossom", "pink_petals",
    "eyeblossom", "flowering_azalea", "wildflowers", "cactus_flower",
    "closed_eyeblossom", "open_eyeblossom", "short_dry_grass",
)
# Avoid retaining unrelated objects simply because a directory contains "flower".
FLOWER_NAMES = set(FLOWERS)

def keep(name: str) -> bool:
    n = name.lower().replace("\\", "/")
    if n.endswith("/"):
        return False
    if n in {"pack.mcmeta", "pack.png"} or n.startswith("licenses/"):
        return True
    if not n.startswith("assets/"):
        return False

    # We keep paired .png.mcmeta animation metadata automatically.
    target = n[:-7] if n.endswith(".mcmeta") else n
    stem = Path(target).stem
    basename = stem.removesuffix("_top").removesuffix("_side").removesuffix("_bottom")
    parts = set(re.split(r"[/_.-]+", target))

    if "obol" in parts or "obols" in parts or "emerald" in parts:
        return True
    if "leaves" in parts or stem.endswith("_leaves") or "leaf" in parts:
        return True
    if ("flower" in parts or "flowers" in parts or
            "flower" in stem or basename in FLOWER_NAMES or
            any(stem.startswith(f + "_") for f in FLOWER_NAMES)):
        return True
    return False

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write ZIP and save backup")
    args = parser.parse_args()
    if not PACK.exists():
        parser.error(f"Missing resource pack: {PACK}")

    with ZipFile(PACK) as source:
        entries = [info for info in source.infolist() if not info.is_dir()]
        retained = [info for info in entries if keep(info.filename)]
        removed = [info for info in entries if not keep(info.filename)]
        selected = [info.filename.lower() for info in retained]
        required = {
            "emerald/obol": any("emerald" in n or "obol" in n for n in selected),
            "leaves": any("leaves" in n for n in selected),
            "flowers": any("flower" in n or Path(n).stem in FLOWER_NAMES for n in selected),
            "pack.mcmeta": "pack.mcmeta" in selected,
        }
        print(f"Files: {len(entries)} existing, {len(retained)} retained, {len(removed)} removed.")
        for item, ok in required.items():
            print(f"  {item}: {'OK' if ok else 'NOT FOUND'}")
        for info in retained:
            print(f"  KEEP {info.filename}")
        if not all(required.values()):
            raise SystemExit("Aborted: expected resource group missing; inspect the ZIP first.")
        if not args.apply:
            print("Preview only. Run again with --apply to save.")
            return

        backup = ROOT / "HerasGardenRP.before-vanilla-cleanup.zip"
        if backup.exists():
            raise SystemExit(f"Backup already exists: {backup}; will not overwrite it.")
        with tempfile.NamedTemporaryFile(prefix="garden-pack-", suffix=".zip", dir=ROOT, delete=False) as tmp:
            temporary = Path(tmp.name)
        try:
            with ZipFile(temporary, "w") as output:
                for info in retained:
                    output.writestr(info, source.read(info))
            with ZipFile(temporary) as check:
                assert check.testzip() is None, "Corrupt ZIP member"
                assert sorted(check.namelist()) == sorted(i.filename for i in retained)
            shutil.copy2(PACK, backup)
            temporary.replace(PACK)
            print(f"Updated {PACK.name}. Backup at {backup.name}.")
        finally:
            temporary.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
