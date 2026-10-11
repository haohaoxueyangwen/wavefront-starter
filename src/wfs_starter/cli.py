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
    def load(p):return image(path.parent/p)
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
            ref=np.stack([corrected(load(p['reference']),dark,flat) for p in pairs]);sam=np.stack([corrected(load(p['sample']),dark,flat) for p in pairs])
        else:
            ref=corrected(load(config['reference']),dark,flat);sam=corrected(load(config['sample']),dark,flat)
        arrays,meta=(speckle if mode in {'wxst','wsvt'} else grating if mode=='grating' else hartmann if mode=='hartmann' else invalid)(sam,ref,config)
    meta['config']=config;save_results(output,arrays,meta)
    print(json.dumps({'case':mode,'output':str(Path(output).resolve())},ensure_ascii=False))

def invalid(*args):raise ValueError('Unsupported mode.')

def main():
    p=argparse.ArgumentParser(description='Wavefront sensing teaching tools: preserved solvers with explicit configuration.')
    sub=p.add_subparsers(dest='command',required=True)
    r=sub.add_parser('run',help='Run a JSON configuration on grayscale TIFF/NPY input.');r.add_argument('config');r.add_argument('--output',required=True)
    d=sub.add_parser('demo',help='Generate and process known synthetic controls; no real experiment data.');d.add_argument('--output',required=True);d.add_argument('--case',choices=['all','wxst','wsvt','grating','hartmann','zernike'],default='all')
    sub.add_parser('check-env',help='Import every dependency and report versions.')
    u=sub.add_parser('ui',help='Open the local browser UI for all five methods.')
    u.add_argument('--port',type=int,default=8790)
    u.add_argument('--workspace',default='wavefront-runs')
    u.add_argument('--no-browser',action='store_true')
    args=p.parse_args()
    try:
        if args.command=='run':run_config(args.config,args.output)
        elif args.command=='demo':
            from .demos import run_demos
            run_demos(args.output,args.case)
        elif args.command=='ui':
            from .ui import serve
            serve(args.workspace,args.port,not args.no_browser)
        else:
            import importlib
            names=['numpy','scipy','matplotlib','pywt','numba','h5py','PIL','colorama']
            print(json.dumps({n:getattr(importlib.import_module(n),'__version__','import OK') for n in names},indent=2))
    except (ValueError,FileNotFoundError,FileExistsError,KeyError) as exc:
        p.exit(2,f'{type(exc).__name__}: {exc}\n')

if __name__=='__main__':main()
