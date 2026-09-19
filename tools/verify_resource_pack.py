from pathlib import Path
import json
import re
import zipfile

PACK = Path(__file__).resolve().parents[1] / "HerasGardenRP.zip"

ANIMAL_RE = re.compile(r"^assets/minecraft/textures/entity/(?:axolotl|bee|cat|chicken|cow|fox|frog|goat|horse|llama|panda|parrot|pig|rabbit|sheep|sniffer|strider|turtle|wolf)/|^assets/minecraft/textures/entity/(?:chicken|dolphin|squid)\\.png$|^assets/minecraft/optifine/mob/(?:bear|cow|fox|pig|rabbit|squid|strider|turtle)/|^assets/minecraft/optifine/mob/(?:chicken(?:2|3)?\\.png|chicken\\.properties|dolphin2\\.png|dolphin\\.properties)$|^assets/minecraft/optifine/cem/rabbit(?:/|\\.jem$)")

with zipfile.ZipFile(PACK) as archive:
    names = archive.namelist()
    animal_overrides = [name for name in names if ANIMAL_RE.search(name)]
    assert not animal_overrides, f"Animal overrides remain: {animal_overrides[:20]}"
    for font in ("classic", "clean", "medieval", "storybook", "smooth"):
        path = f"assets/garden/font/{font}.json"
        assert path in names, f"Missing font definition: {path}"
        json.loads(archive.read(path))
    assert archive.testzip() is None, "ZIP contains a corrupt entry"

print("Resource pack verification passed.")
