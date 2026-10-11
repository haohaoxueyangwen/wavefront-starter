"""Single packaged source for CLI examples and browser configuration templates."""
import json
from pathlib import Path

MODES = ("wxst", "wsvt", "grating", "hartmann", "zernike")

def load_templates():
    root = Path(__file__).with_name("configs")
    return {mode: json.loads((root / (mode + ".json")).read_text(encoding="utf-8")) for mode in MODES}
