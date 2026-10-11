"""Display-only plots for Zernike results; numerical files stay unchanged."""
from pathlib import Path
import json

def add_previews(root):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for path in Path(root).rglob('metadata.json'):
        meta = json.loads(path.read_text(encoding='utf-8'))
        if 'coefficient_unit' not in meta or not (path.parent/'results.npz').is_file():
            continue
        unit = meta['coefficient_unit']
        with np.load(path.parent/'results.npz', allow_pickle=False) as result:
            for key in ['fit', 'residual']:
                fig, ax = plt.subplots(figsize=(5,4))
                im = ax.imshow(result[key], origin='upper')
                ax.set(title=f'Zernike {key}', xlabel='column [px]', ylabel='row [px]')
                fig.colorbar(im, ax=ax, label=unit)
                fig.tight_layout();fig.savefig(path.parent/(key+'.png'),dpi=130);plt.close(fig)
            fig, ax = plt.subplots(figsize=(7,4))
            coeff = result['coefficients']
            ax.bar(np.arange(len(coeff)), coeff)
            ax.set_xticks(np.arange(len(coeff)), [f'{n},{m}' for n,m in meta['modes_nm']], rotation=45)
            ax.set(xlabel='Explicit (n,m) modes', ylabel=f'coefficient [{unit}]', title='Zernike coefficients')
            fig.tight_layout();fig.savefig(path.parent/'coefficients.png',dpi=130);plt.close(fig)
