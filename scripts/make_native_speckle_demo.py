"""Export the real BB11 CRL example as native-ingress NPZ files; no solver run."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from wfs_starter.native_examples import dataset

def generate(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    folder, source = dataset(output)
    reference = np.stack([np.load(folder/f'reference_{i:03}.npy',allow_pickle=False) for i in range(1,101)])
    sample = np.stack([np.load(folder/f'sample_{i:03}.npy',allow_pickle=False) for i in range(1,101)])
    inputs = {'wsvt': (sample, reference), 'wxst': (sample[0].astype(np.float32), reference[0].astype(np.float32))}
    records = {}
    for mode, (sam, ref) in inputs.items():
        np.savez_compressed(output/(mode+'.npz'), sample=sam, reference=ref)
        records[mode] = {key: dict(shape=list(a.shape), dtype=str(a.dtype),
                                  sha256=hashlib.sha256(memoryview(a).cast('B')).hexdigest())
                         for key, a in (('sample', sam), ('reference', ref))}
    manifest = dict(dataset_id=source['dataset_id'],crop_y0_y1_x0_x1=source['crop_y0_y1_x0_x1'],
                    geometry=source['calibration'],purpose='Real CRL acquisition; no synthetic displacement truth.',inputs=records)
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    return manifest

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    args=parser.parse_args()
    print(json.dumps(generate(args.out), indent=2))
