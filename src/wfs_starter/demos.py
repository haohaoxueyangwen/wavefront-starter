"""Real CRL speckle examples and named analytic controls for other methods."""
from __future__ import annotations
import json,time
from pathlib import Path
import numpy as np
from .core import grating,hartmann,zernike_fit,save_results,MODES

def run_demos(output,case='all'):
    root=Path(output)
    if root.exists():raise FileExistsError('Choose a new demo directory.')
    root.mkdir(parents=True)
    report={};start=time.monotonic()
    for kind in ['wxst','wsvt','grating','hartmann','zernike']:
        if case not in {'all',kind}:continue
        folder=root/kind;folder.mkdir();data=folder/'data';data.mkdir()
        if kind in {'wxst','wsvt'}:
            from .native_examples import example
            from .runtime_backends import status
            from .cli import run_config
            backend='cpp' if status('cpp')['available'] else 'python'
            config=example(root,kind,backend)['config']
            (folder/'config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
            run_config(folder/'config.json',folder/'results')
            report[kind]=dict(passed=True,dataset=config['example_dataset_id'],backend=backend,
                scope='Real CRL execution and output delivery; no known-displacement truth or synthetic EPE criterion.')
            continue
        elif kind=='grating':
            n=128;yy,xx=np.indices((n,n));k=2*np.pi/n
            phase=.2*np.sin(k*xx)+.1*np.cos(k*yy)
            gx=.2*k*np.cos(k*xx);gy=-.1*k*np.sin(k*yy)
            ref=3+np.cos(10*k*xx)+np.cos(10*k*yy)
            sam=3+np.cos(10*k*xx+gx)+np.cos(10*k*yy+gy)
            np.save(data/'reference.npy',ref);np.save(data/'sample.npy',sam);np.save(data/'known_phase_rad.npy',phase)
            config=dict(mode=kind,reference='data/reference.npy',sample='data/sample.npy',band_x_center_rc=[64,74],band_y_center_rc=[74,64],band_x_size_rc=[9,9],band_y_size_rc=[9,9],unwrap=True,pixel_size_x_m=1e-6,pixel_size_y_m=1e-6,phase_gradient_scale_rad_per_m_per_fringe_rad=[1e6,1e6],calibration_source='Analytic synthetic carrier encoding: fringe phase equals phase derivative per pixel; not Talbot optical calibration.')
            arrays,meta=grating(sam,ref,config)
            metrics=dict(phase_rmse_rad=float(np.sqrt(np.mean((arrays['phase_rad']-phase)**2))),control='Analytic periodic carrier encoded with known phase derivatives.')
            passed=metrics['phase_rmse_rad']<1e-4
        elif kind=='hartmann':
            n=128;yy,xx=np.indices((n,n));ref=np.zeros((n,n));sam=ref.copy()
            for cy in [16,48,80,112]:
                for cx in [16,48,80,112]:
                    ref+=np.exp(-((xx-cx)**2+(yy-cy)**2)/8)
                    sam+=np.exp(-((xx-cx-.35)**2+(yy-cy+.2)**2)/8)
            np.save(data/'reference.npy',ref);np.save(data/'sample.npy',sam)
            config=dict(mode=kind,reference='data/reference.npy',sample='data/sample.npy',grid_rows=4,grid_cols=4,pixel_size_m=1e-6,distance_m=.5,metadata_note='Gaussian spots shifted by ux=+0.35, uy=-0.2 px; illustrative geometry.')
            arrays,meta=hartmann(sam,ref,config)
            metrics=dict(max_displacement_error_px=float(np.max(np.hypot(arrays['ux_px']-.35,arrays['uy_px']+.2))),control='Known Gaussian centroid translation in fixed isolated cells.')
            passed=metrics['max_displacement_error_px']<1e-6
        else:
            from .vendor.zernike import zernike
            yy,xx=np.indices((64,64));x=(xx-31.5)/28;y=(yy-31.5)/28;rho=np.hypot(x,y);theta=np.arctan2(y,x)
            known=np.zeros(15);known[[0,1,3,5]]=[.3,.04,.2,-.07]
            a=sum(c*zernike(rho,theta,n,m) for c,(n,m) in zip(known,MODES));np.save(data/'phase_rad.npy',a)
            config=dict(mode=kind,phase='data/phase_rad.npy',phase_unit='rad',center_xy_px=[31.5,31.5],radius_px=28,terms=15)
            arrays,meta=zernike_fit(a,[31.5,31.5],28);meta['coefficient_unit']='rad'
            metrics=dict(max_coefficient_error_rad=float(np.max(np.abs(arrays['coefficients']-known))),residual_rms_rad=meta['residual_rms'],control='Explicit orthonormal modes with known coefficients.')
            passed=metrics['max_coefficient_error_rad']<1e-10
        (folder/'config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
        meta['config']=config;meta['synthetic_control_metrics']=metrics
        save_results(folder/'results',arrays,meta)
        report[kind]=dict(passed=bool(passed),**metrics)
    report['scope']='WSVT/WXST use real BB11 CRL data; other cases are named analytic controls. Successful execution does not establish physical accuracy.'
    report['seconds']=time.monotonic()-start
    (root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not all(v['passed'] for v in report.values() if isinstance(v,dict)):raise ValueError('One or more examples failed; keep report and inspect.')
