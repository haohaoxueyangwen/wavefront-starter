"""Copy a declared ROI from 100 BB11 TIFF pairs; never modify the experiment folder."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
from PIL import Image

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def prepare(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination == source or source in destination.parents:
        raise ValueError('Example output must be outside the experiment directory.')
    destination.mkdir(parents=True, exist_ok=False)
    files=[]
    # Central illuminated lens region; no resampling or image-intensity processing.
    roi = [686,1198,714,1226]  # y0,y1,x0,x1, exclusive upper limits
    for i in range(1,101):
        for role, prefix in [('reference','ref'),('sample','sample')]:
            original=source/f'{prefix}_1_{i:05}.tif'
            before=original.stat()
            original_sha=sha(original)
            with Image.open(original) as image: a=np.asarray(image).copy()
            if a.shape!=(2048,2048) or a.dtype!=np.uint16:
                raise ValueError('Unexpected original shape/dtype: '+original.name)
            crop=a[roi[0]:roi[1],roi[2]:roi[3]].copy()
            name=f'{role}_{i:03}.npy'
            np.save(destination/name,crop,allow_pickle=False)
            assert original.stat().st_size==before.st_size and original.stat().st_mtime_ns==before.st_mtime_ns
            files.append({'file':name,'sha256':sha(destination/name),'original_file':original.name,
                          'original_sha256':original_sha,'original_bytes':before.st_size})
        if i%25==0:print('CRL paired frames copied',i,flush=True)
    manifest={'dataset_id':'crl-bb11-20231102-roi512-v1','experiment':'20231102CRL/BB11/scan_speckle',
        'sample':{'material':'Diamond','nominal_radius_um':500,'source':'20231102CRL_notebook.docx'},
        'frames':100,'original_shape_yx':[2048,2048],'shape_yx':[512,512],'dtype':'uint16',
        'crop_y0_y1_x0_x1':roi,'processing':'Exact integer-pixel crop only; no interpolation, smoothing, normalization or synthetic displacement.',
        'calibration':{'energy_ev':12400.0,'pixel_size_m':1.625e-6,'distance_m':0.4845,
                       'source':'Historical BB11 WSVT_result.json / WXST_result.json',
                       'status':'Recorded reconstruction settings; effective-distance geometry not independently recalibrated here.'},
        'frame_pairing':'Identical acquisition index 001..100; WXST uses pair 001; WSVT uses all 100 pairs.',
        'files':files}
    (destination/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('CRL example bytes',sum(p.stat().st_size for p in destination.iterdir()),flush=True)
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',required=True,help='BB11 scan_speckle directory containing both ref_1_*.tif and sample_1_*.tif')
    p.add_argument('--output',required=True)
    a=p.parse_args();prepare(a.source,a.output)
