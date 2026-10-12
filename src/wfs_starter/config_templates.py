"""Single packaged source for CLI examples and browser configuration templates."""
import json
from pathlib import Path

MODES = ("wxst", "wsvt", "grating", "hartmann", "zernike", "zernike_full", "surface", "focus")

def load_templates():
    root = Path(__file__).with_name("configs")
    templates={mode: json.loads((root / (mode + ".json")).read_text(encoding="utf-8")) for mode in MODES}
    from .runtime_backends import status
    if status('cpp')['available']:
        for mode in ('wxst','wsvt'):templates[mode]['backend']='cpp'
    return templates
