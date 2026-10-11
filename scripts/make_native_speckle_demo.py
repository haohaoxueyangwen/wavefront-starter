"""Generate tiny deterministic native-ingress examples; never launch a solver."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from scipy.ndimage import gaussian_filter, shift

def generate(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    rng = np.random.default_rng(20261012)
    reference = np.stack([gaussian_filter(rng.random((64, 64)), .7) for _ in range(100)])
    reference = np.ascontiguousarray(np.rint(reference*30000+1000), dtype=np.uint16)
    sample = np.stack([shift(frame, (-1, 1), order=0, mode='reflect') for frame in reference])
    inputs = {'wsvt': (sample, reference), 'wxst': (sample[0].astype(np.float32), reference[0].astype(np.float32))}
    records = {}
    for mode, (sam, ref) in inputs.items():
        np.savez_compressed(output/(mode+'.npz'), sample=sam, reference=ref)
        records[mode] = {key: dict(shape=list(a.shape), dtype=str(a.dtype),
                                  sha256=hashlib.sha256(memoryview(a).cast('B')).hexdigest())
                         for key, a in (('sample', sam), ('reference', ref))}
    manifest = dict(seed=20261012, image_transform_shift_yx_px=[-1, 1], boundary='reflect',
                    geometry=dict(pixel_m=1.625e-6, distance_m=.4845, energy_ev=12400),
                    purpose='Synthetic input/axis exercise; not experimental or physical-accuracy acceptance.', inputs=records)
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    return manifest

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    args=parser.parse_args()
    print(json.dumps(generate(args.out), indent=2))
