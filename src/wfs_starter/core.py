"""Validated teaching adapters around preserved research primitives."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

# Explicit orthonormal real Zernike modes, ordered as Noll j=1..15.
MODES = [(0,0),(1,1),(1,-1),(2,0),(2,-2),(2,2),(3,-1),(3,1),
         (3,-3),(3,3),(4,0),(4,2),(4,-2),(4,4),(4,-4)]

def image(path: str | Path) -> np.ndarray:
    path=Path(path)
    if path.suffix.lower()=='.npy':
        a=np.load(path,allow_pickle=False)
    else:
        from PIL import Image
        with Image.open(path) as f:a=np.asarray(f)
    a=np.asarray(a,dtype=np.float64)
    if a.ndim!=2 or min(a.shape)<8 or not np.isfinite(a).all():
        raise ValueError('Input must be a finite grayscale 2D image, at least 8×8.')
    return a

def positive(value, name):
    value=float(value)
    if not np.isfinite(value) or value<=0:raise ValueError(name+' must be positive and finite.')
    return value

def corrected(a, dark=None, flat=None):
    a=np.asarray(a,dtype=np.float64)
    if dark is not None:
        if dark.shape!=a.shape:raise ValueError('Dark image shape differs.')
        a=a-dark
    if flat is not None:
        if flat.shape!=a.shape:raise ValueError('Flat image shape differs.')
        denominator=flat if dark is None else flat-dark
        if np.any(denominator<=0):raise ValueError('Flat minus dark must be positive; mask invalid pixels before using this teaching adapter.')
        a=a/denominator
    return np.maximum(a,0)

def speckle(sample,reference,config):
    mode=config['mode']
    if mode not in {'wxst','wsvt'}:raise ValueError('mode must be wxst or wsvt')
    ndim=2 if mode=='wxst' else 3
    if sample.shape!=reference.shape or sample.ndim!=ndim:raise ValueError('Sample/reference shapes or frame counts differ.')
    if sample.shape[-2]!=sample.shape[-1]:raise ValueError('Select an identical square ROI for sample and reference; this adapter does not silently crop rectangles.')
    if mode=='wsvt' and sample.shape[0]<2:raise ValueError('WSVT requires a frame stack, not one image pair.')
    if not np.isfinite(sample).all() or not np.isfinite(reference).all():raise ValueError('Nonfinite speckle data.')
    if np.std(reference)==0 or np.std(sample)==0:raise ValueError('Speckle input has no contrast.')
    if mode=='wsvt' and (np.any(np.std(reference,axis=0)==0) or np.any(np.std(sample,axis=0)==0)):
        raise ValueError('WSVT requires temporal variation at every pixel; identical frames or dead pixels need masking.')
    energy=positive(config['energy_ev'],'energy_ev')
    pixel=positive(config['pixel_size_m'],'pixel_size_m')
    distance=positive(config['distance_m'],'distance_m')
    half=int(config.get('search_half_window',3))
    template=int(config.get('template_half_window',2))
    if half<1 or template<1 or min(sample.shape[-2:])<=2*(half+template)+8:
        raise ValueError('Image too small for the selected search/template windows.')
    kwargs=dict(M_image=min(sample.shape[-2:]),cal_half_window=half,N_s_extend=2,
                n_cores=1,n_group=1,energy=energy,p_x=pixel,z=distance,
                wavelet_level_cut=0,pyramid_level=0,n_iter=1,use_wavelet=True)
    if mode=='wxst':
        from .vendor.speckle.WXST import WXST
        solver=WXST(sample,reference,N_s=template,**kwargs)
    else:
        from .vendor.speckle.WSVT import WSVT
        solver=WSVT(sample,reference,**kwargs)
    result=solver.run(result_path=None)
    result['ux_px']=result.pop('displace_x');result['uy_px']=result.pop('displace_y')
    result['phase_rad']=result.pop('phase')
    result['angle_x_rad_demeaned']=result.pop('DPC_x')
    result['angle_y_rad_demeaned']=result.pop('DPC_y')
    metadata=dict(case=mode,coordinate='image[y,x]; displacement [ux,uy]',
                  valid_input_crop_px=half,energy_ev=energy,pixel_size_m=pixel,distance_m=distance,
                  phase_convention='Preserved reference solver; displacement mean removed before DPC; phase zero-frequency removed. Absolute tilt and piston are not recovered.')
    return result,metadata

def grating(sample,reference,config):
    from .vendor.grating import phase_from_sideband,unwrap_phase_2d,frankot_chellappa
    if sample.shape!=reference.shape:raise ValueError('Sample/reference shapes differ.')
    fields={}
    for axis in ('x','y'):
        center=tuple(config[f'band_{axis}_center_rc']);size=tuple(config[f'band_{axis}_size_rc'])
        if len(center)!=2 or len(size)!=2 or any(int(v)!=v for v in center+size):raise ValueError('Sideband center/size must be two integer [row,column] coordinates.')
        center=tuple(map(int,center));size=tuple(map(int,size))
        if any(v<=0 or v%2==0 for v in size):raise ValueError('Use positive odd sideband dimensions.')
        for c,s,n in zip(center,size,sample.shape):
            if c-s//2<0 or c+s//2>=n:raise ValueError('Sideband extends outside the spectrum.')
        if center==(sample.shape[0]//2,sample.shape[1]//2):raise ValueError('DC is not a sideband.')
        ps=phase_from_sideband(sample,center,size);pr=phase_from_sideband(reference,center,size)
        wrapped=np.angle(np.exp(1j*(ps-pr)))
        fields[f'fringe_phase_{axis}_rad']=unwrap_phase_2d(wrapped) if config.get('unwrap',True) else wrapped
    if tuple(config['band_x_center_rc'])==tuple(config['band_y_center_rc']):raise ValueError('X and Y sidebands must differ.')
    meta=dict(case='grating',coordinate='Sideband centers [row,column] in fftshift spectrum',
              output='Differential fringe phase in radians; no automatic optical calibration.')
    scale=config.get('phase_gradient_scale_rad_per_m_per_fringe_rad')
    if scale is not None:
        if len(scale)!=2 or not np.isfinite(scale).all() or any(float(s)==0 for s in scale):raise ValueError('Supply two finite nonzero calibrated signed gradient scales.')
        pixel_x=positive(config['pixel_size_x_m'],'pixel_size_x_m');pixel_y=positive(config['pixel_size_y_m'],'pixel_size_y_m')
        gx=fields['fringe_phase_x_rad']*float(scale[0]);gy=fields['fringe_phase_y_rad']*float(scale[1])
        fields['phase_gradient_x_rad_per_m']=gx;fields['phase_gradient_y_rad_per_m']=gy
        fields['phase_rad']=frankot_chellappa(gx*pixel_x,gy*pixel_y)
        meta['output']='Calibrated phase gradient rad/m and integrated phase rad; Fourier periodic boundary; piston removed.'
        meta['calibration_source']=config['calibration_source']
    return fields,meta

def hartmann(sample,reference,config):
    from .vendor.hartmann import compute_cells,compute_centroids,centroid_shifts
    if sample.shape!=reference.shape:raise ValueError('Hartmann image shapes differ.')
    rows=int(config['grid_rows']);cols=int(config['grid_cols'])
    if rows<1 or cols<1 or min(sample.shape[0]//rows,sample.shape[1]//cols)<4:raise ValueError('Invalid Hartmann grid.')
    if np.min(sample)<0 or np.min(reference)<0:raise ValueError('Centroid input must be nonnegative after background correction.')
    cells=compute_cells(reference.shape,rows,cols)
    for (y0,y1),(x0,x1) in cells:
        if reference[y0:y1,x0:x1].sum()<=0 or sample[y0:y1,x0:x1].sum()<=0:raise ValueError('Empty spot cell; use a valid grid and reference.')
    ref=compute_centroids(reference,cells,rows,cols);sam=compute_centroids(sample,cells,rows,cols)
    shifts=centroid_shifts(ref,sam)
    result=dict(reference_centers_xy_px=ref,sample_centers_xy_px=sam,ux_px=shifts[...,0],uy_px=shifts[...,1])
    meta=dict(case='hartmann',coordinate='centers[x,y]; target minus reference',
              model='Fixed uniform cells; one isolated spot per cell; no auto spot pairing or dynamic demixing.')
    if 'distance_m' in config:
        pixel=positive(config['pixel_size_m'],'pixel_size_m');distance=positive(config['distance_m'],'distance_m')
        result.update(angle_x_rad=shifts[...,0]*pixel/distance,angle_y_rad=shifts[...,1]*pixel/distance)
        meta.update(pixel_size_m=pixel,distance_m=distance,angle='Paraxial detector shift relative to calibrated reference.')
    return result,meta

def zernike_fit(array,center_xy_px,radius_px,terms=15):
    from .vendor.zernike import zernike
    cx,cy=map(float,center_xy_px);radius=positive(radius_px,'radius_px')
    terms=int(terms)
    if not 1<=terms<=15:raise ValueError('Teaching fitter supports 1..15 explicit modes.')
    yy,xx=np.indices(array.shape,dtype=float);x=(xx-cx)/radius;y=(yy-cy)/radius
    rho=np.hypot(x,y);theta=np.arctan2(y,x);valid=(rho<=1)&np.isfinite(array)
    if valid.sum()<=terms:raise ValueError('Too few valid pupil samples.')
    design=np.column_stack([zernike(rho[valid],theta[valid],n,m) for n,m in MODES[:terms]])
    coeff,_,rank,_=np.linalg.lstsq(design,array[valid],rcond=None)
    if rank!=terms:raise ValueError('Zernike design matrix is rank deficient.')
    fit=np.full(array.shape,np.nan);fit[valid]=design@coeff
    residual=np.full(array.shape,np.nan);residual[valid]=array[valid]-fit[valid]
    values=array[valid]-array[valid].mean()
    return dict(coefficients=coeff,fit=fit,residual=residual,valid_mask=valid),dict(
        modes_nm=MODES[:terms],normalization='Real orthonormal unit disk; positive m cosine, negative m sine',
        valid_count=int(valid.sum()),rms_after_piston=float(np.sqrt(np.mean(values**2))),
        pv=float(np.ptp(array[valid])),residual_rms=float(np.sqrt(np.mean(residual[valid]**2))),
        center_xy_px=[cx,cy],radius_px=radius)

def save_results(folder,arrays,metadata):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    if (folder/'results.npz').exists():raise FileExistsError('Choose a new output directory; results.npz already exists.')
    np.savez_compressed(folder/'results.npz',**arrays)
    (folder/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    units={'ux_px':'px','uy_px':'px','phase_rad':'rad','fringe_phase_x_rad':'rad','fringe_phase_y_rad':'rad',
           'angle_x_rad':'rad','angle_y_rad':'rad','angle_x_rad_demeaned':'rad','angle_y_rad_demeaned':'rad'}
    for name,a in arrays.items():
        if np.asarray(a).ndim==2 and name in units:
            fig,ax=plt.subplots(figsize=(5,4));im=ax.imshow(a,origin='upper');ax.set(title=name,xlabel='column [px]',ylabel='row [px]')
            fig.colorbar(im,ax=ax,label=units[name]);fig.tight_layout();fig.savefig(folder/(name+'.png'),dpi=130);plt.close(fig)
