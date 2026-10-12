"""Small native-ingress examples, generated away from users' experiment data."""
from pathlib import Path
import json, numpy as np
from scipy.ndimage import gaussian_filter, shift
from .config_templates import load_templates
from .speckle_backends import catalog

def example(workspace, mode, backend):
    if mode not in {'wsvt','wxst'} or backend not in {'cpp','gpu','python'}:raise ValueError('无效的散斑示例')
    folder=Path(workspace)/'speckle-examples-v060'
    folder.mkdir(exist_ok=True)
    marker=folder/'manifest.json'
    if not marker.is_file():
        rng=np.random.default_rng(20261012)
        for i in range(100):
            ref=np.rint(gaussian_filter(rng.random((64,64)),.7)*30000+1000).astype(np.uint16)
            sam=shift(ref,(-1,1),order=0,mode='reflect')
            np.save(folder/f'reference_{i:03}.npy',ref,allow_pickle=False)
            np.save(folder/f'sample_{i:03}.npy',sam,allow_pickle=False)
        marker.write_text(json.dumps({'seed':20261012,'shape':[100,64,64],'image_shift_yx_px':[-1,1],
            'geometry':'synthetic teaching values; replace with your experiment calibration'},indent=2),encoding='utf-8')
    config=load_templates()[mode]
    config.update(backend=backend,energy_ev=12400,pixel_size_m=1.625e-6,distance_m=.4845,
        search_half_window=10,template_half_window=3,extended_half_window=4,pyramid_level=1,wavelet_level_cut=1,
        n_iter=1,n_cores=2,phase_cores=2,n_group=1,roi_size_px=0,metadata_note='合成教学示例，标定值不是实验值')
    if mode=='wsvt':config.pop('template_half_window',None)
    if backend=='gpu':config.update(catalog()['gpu']['constraints'])
    if mode=='wsvt':config['pairs']=[{'reference':str(folder/f'reference_{i:03}.npy'),'sample':str(folder/f'sample_{i:03}.npy')} for i in range(100)]
    else:config.update(reference=str(folder/'reference_000.npy'),sample=str(folder/'sample_000.npy'))
    return {'config':config,'base_dir':str(folder),'note':'64×64 合成示例已载入。保持当前 CPU / GPU 选择，点击运行算法。标定值只用于教学。'}
