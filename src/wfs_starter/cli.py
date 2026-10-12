from __future__ import annotations
import argparse,json,os,sys
from pathlib import Path
os.environ.setdefault('MPLBACKEND','Agg')
from .core import image,corrected,speckle,grating,hartmann,zernike_fit,save_results
import numpy as np

def run_config(path,output):
    path=Path(path).resolve();config=json.loads(path.read_text(encoding='utf-8-sig'))
    def check_filled(value,key='config'):
        if value is None:raise ValueError(f'Fill the real-data template field: {key}')
        if isinstance(value,dict):
            for k,v in value.items():check_filled(v,key+'.'+k)
        if isinstance(value,list):
            for i,v in enumerate(value):check_filled(v,f'{key}[{i}]')
    check_filled(config)
    for key in ('cpp_executable', 'gpu_executable'):
        if config.get(key):config[key]=str((path.parent/Path(config[key])).resolve())
    if config['mode'] in {'zernike_full','surface','focus'}:
        for key in ('phase','data_dir','dark_dir','flat_dir','analysis_source_dir','zernike_source_dir'):
            if config.get(key):config[key]=str((path.parent/Path(config[key])).resolve())
    if config['mode']=='zernike_full':
        from .advanced_zernike import run_full
        run_full(config,output)
        return
    if config['mode'] in {'surface','focus'}:
        from .legacy_tools import run_analysis
        run_analysis(config,output)
        return
    def load(p):
        file=path.parent/p
        # Preserve real uint16 for the native GPU ingress. Correction requires float arithmetic.
        if config.get('backend')=='gpu' and not config.get('dark') and not config.get('flat'):
            if file.suffix.lower()=='.npy':a=np.load(file,allow_pickle=False)
            else:
                from PIL import Image
                with Image.open(file) as f:a=np.asarray(f).copy()
            if a.ndim!=2 or min(a.shape)<8 or not np.isrealobj(a) or not np.isfinite(a).all():raise ValueError('Invalid GPU image.')
            return a
        return image(file)
    def preprocess(a,dark,flat):
        if config.get('backend')=='gpu' and dark is None and flat is None:return a
        return corrected(a,dark,flat)
    mode=config['mode']
    if mode=='zernike':
        a=load(config['phase']);arrays,meta=zernike_fit(a,config['center_xy_px'],config['radius_px'],config.get('terms',15))
        if config['phase_unit'] not in {'rad','m'}:raise ValueError('phase_unit must be rad or m')
        meta['coefficient_unit']=config['phase_unit']
    else:
        dark=load(config['dark']) if config.get('dark') else None
        flat=load(config['flat']) if config.get('flat') else None
        if mode=='wsvt':
            pairs=config['pairs']
            if len(pairs)<2:raise ValueError('Provide at least two explicitly paired frames.')
            ref=np.stack([preprocess(load(p['reference']),dark,flat) for p in pairs]);sam=np.stack([preprocess(load(p['sample']),dark,flat) for p in pairs])
        else:
            ref=preprocess(load(config['reference']),dark,flat);sam=preprocess(load(config['sample']),dark,flat)
        if mode in {'wxst','wsvt'}:
            from .speckle_backends import integer
            size=integer(config,'roi_size_px')
            if size:
                center=config.get('roi_center_xy_px',[-1,-1])
                if len(center)!=2 or not np.isfinite(center).all():raise ValueError('ROI center must be [x,y].')
                cx,cy=(ref.shape[-1]//2,ref.shape[-2]//2) if center==[-1,-1] else center
                if int(cx)!=cx or int(cy)!=cy:raise ValueError('ROI center must use integer pixel coordinates.')
                x0=int(cx)-size//2;y0=int(cy)-size//2
                if x0<0 or y0<0 or x0+size>ref.shape[-1] or y0+size>ref.shape[-2]:raise ValueError('ROI extends outside the input image.')
                ref=ref[...,y0:y0+size,x0:x0+size];sam=sam[...,y0:y0+size,x0:x0+size]
        arrays,meta=(speckle if mode in {'wxst','wsvt'} else grating if mode=='grating' else hartmann if mode=='hartmann' else invalid)(sam,ref,config)
    meta['config']=config;save_results(output,arrays,meta)
    print(json.dumps({'case':mode,'output':str(Path(output).resolve())},ensure_ascii=False))

def invalid(*args):raise ValueError('Unsupported mode.')

def main():
    p=argparse.ArgumentParser(description='Wavefront sensing teaching tools: preserved solvers with explicit configuration.')
    sub=p.add_subparsers(dest='command',required=True)
    r=sub.add_parser('run',help='Run a JSON configuration on grayscale TIFF/NPY input.');r.add_argument('config');r.add_argument('--output',required=True)
    d=sub.add_parser('demo',help='Run real CRL speckle examples and analytic controls for other methods.');d.add_argument('--output',required=True);d.add_argument('--case',choices=['all','wxst','wsvt','grating','hartmann','zernike'],default='all')
    sub.add_parser('check-env',help='Import every dependency and report versions.')
    u=sub.add_parser('ui',help='Open one of four independent local frontends.')
    u.add_argument('--port',type=int,default=8790)
    u.add_argument('--workspace',default='wavefront-runs')
    u.add_argument('--no-browser',action='store_true')
    u.add_argument('--app',choices=['home','speckle','grating','hartmann','wavefront'],default='home',help='Open one independent frontend.')
    args=p.parse_args()
    try:
        if args.command=='run':run_config(args.config,args.output)
        elif args.command=='demo':
            from .demos import run_demos
            run_demos(args.output,args.case)
        elif args.command=='ui':
            from .ui import serve
            serve(args.workspace,args.port,not args.no_browser,args.app)
        else:
            import importlib
            names=['numpy','scipy','matplotlib','pywt','numba','h5py','PIL','colorama']
            print(json.dumps({n:getattr(importlib.import_module(n),'__version__','import OK') for n in names},indent=2))
    except (ValueError,FileNotFoundError,FileExistsError,KeyError) as exc:
        p.exit(2,f'{type(exc).__name__}: {exc}\n')

if __name__=='__main__':main()
