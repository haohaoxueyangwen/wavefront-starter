"""Complete original manual-pupil workflow, with explicit indexing/unit corrections.

Original sources are loaded unchanged. The two corrections are scoped to this
worker's module instance, and are recorded in metadata, not applied to old files.
"""
from pathlib import Path
import csv
import hashlib
import importlib.util
import json
import math
import os
import re
import sys

import numpy as np
from scipy.constants import h, c, electron_volt

INDEX_REFERENCE = 'https://aotools.readthedocs.io/en/latest/_modules/aotools/functions/zernike.html#zernIndex'

def noll_to_nm(j):
    if isinstance(j, bool) or int(j) != j or j < 1:
        raise ValueError('Noll index must be a positive integer')
    n = int((math.sqrt(8*(j-1)+1)-1)//2)
    position = j-n*(n+1)//2
    m = 2*((position+n%2)//2)-n%2
    return n, -m if j%2 else m

def wavelength_um(energy_kev):
    energy = float(energy_kev)
    if not math.isfinite(energy) or not .1 <= energy <= 100:
        raise ValueError('光子能量须为 0.1–100 keV。')
    return h*c/(energy*1000*electron_volt)*1e6

def run_name(value):
    value = str(value or 'analysis').strip()
    if value in {'.','..'} or re.search(r'[<>:"/\\|?*\x00-\x1f]', value) or value.endswith(('.', ' ')):
        raise ValueError('运行名称不能包含路径或 Windows 文件名禁用字符。')
    if value.split('.')[0].upper() in {'CON','PRN','AUX','NUL', *('COM'+str(i) for i in range(1,10)), *('LPT'+str(i) for i in range(1,10))}:
        raise ValueError('运行名称不能使用 Windows 保留名称。')
    return value

def progress(percent, message):
    print('WFS_PROGRESS '+json.dumps({'percent':percent,'message':str(message)},ensure_ascii=False),flush=True)

def safe_json(value):
    if isinstance(value, dict):return {k:safe_json(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)):return [safe_json(v) for v in value]
    if isinstance(value, (float,np.floating)) and not np.isfinite(value):
        return 'Infinity' if value > 0 else '-Infinity' if value < 0 else None
    if isinstance(value,np.generic):return value.item()
    return value

def run_full(config, output):
    source_root=config.get('zernike_source_dir') or os.environ.get('WFS_ZERNIKE_SOURCE','')
    source = Path(source_root).expanduser().resolve()/'analysis_zernike.py' if source_root else Path(__file__).with_name('vendor')/'advanced_zernike_original.py'
    if not source.is_file():raise ValueError('请选择包含 analysis_zernike.py 的原高级 Zernike 工程。')
    if config.get('phase_unit') != 'rad':raise ValueError('完整原 Zernike 分析接收相位 rad；OPD 请先按实际能量转换。')
    terms, remove = config['terms'], config['max_order_remove']
    for value,lo,hi,name in [(terms,5,50,'Zernike 项数'),(remove,0,10,'去除的最大径向阶数')]:
        if isinstance(value,bool) or int(value)!=value or not lo<=value<=hi:raise ValueError(f'{name}须为 {lo}–{hi} 的整数。')
    pixel = float(config['pixel_size_um'])
    if not math.isfinite(pixel) or not .001<=pixel<=1000:raise ValueError('像素尺寸须为 0.001–1000 µm。')
    wave = wavelength_um(config['photon_energy_kev'])
    center = np.asarray(config['center_xy_px'],dtype=float)
    radius = float(config['radius_px'])
    phase_path = Path(config['phase']).resolve()
    phase = np.load(phase_path,allow_pickle=False)
    if phase.ndim!=2 or min(phase.shape)<8 or not np.isrealobj(phase):raise ValueError('相位须为至少 8×8 的二维实数 NPY。')
    if center.shape!=(2,) or not np.isfinite(center).all() or not np.isfinite(radius) or radius<=0:raise ValueError('请填写有限圆心 [x,y] 和正半径。')
    if not 0<=center[0]<phase.shape[1] or not 0<=center[1]<phase.shape[0]:raise ValueError('圆心必须在图像内。')
    yy,xx=np.indices(phase.shape);mask=(xx-center[0])**2+(yy-center[1])**2<=radius**2
    if mask.sum()<terms or not np.isfinite(phase[mask]).all():raise ValueError('圆瞳内需要足够的有限相位采样点；请排除 NaN 区域。')
    # Check identifiability using at most 4096 evenly selected pupil samples.
    ids=np.flatnonzero(mask);ids=ids[np.linspace(0,len(ids)-1,min(len(ids),4096),dtype=int)]
    rho=np.hypot(xx.ravel()[ids]-center[0],yy.ravel()[ids]-center[1])/radius
    theta=np.arctan2(yy.ravel()[ids]-center[1],xx.ravel()[ids]-center[0])
    name=run_name(config.get('run_name') or phase_path.stem)
    spec=importlib.util.spec_from_file_location('_wfs_original_advanced_zernike',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    old_indices=[list(module.noll_to_nm(j)) for j in range(1,terms+1)]
    module.noll_to_nm=noll_to_nm
    design=np.column_stack([module.zernike(rho,theta,*noll_to_nm(j)) for j in range(1,terms+1)])
    if np.linalg.matrix_rank(design)!=terms:raise ValueError('当前圆瞳不足以唯一拟合所选项数；请扩大 ROI 或减少项数。')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    captured={}
    target=module.perform_advanced_zernike_analysis
    # Capture the ORIGINAL function's returned-frame maps, avoiding a second solver.
    def capture(frame,event,arg):
        if event=='return' and frame.f_code is target.__code__:
            for key in ('original_masked','fitted_background_2d','residual_2d','phase_error_2d'):
                if key in frame.f_locals:captured[key]=frame.f_locals[key]
    stage_percent=15
    def report(message):
        nonlocal stage_percent
        percent=65 if 'Visualization' in message else 55 if 'Curvature' in message else 40 if 'Fitting complete' in message else 15
        stage_percent=max(stage_percent,percent)
        progress(stage_percent,message)
    old_profiler=sys.getprofile();sys.setprofile(capture)
    try:
        result=target(phase.astype(float),pixel,wave,*center,radius,
            zernike_terms_to_fit=int(terms),max_order_remove=int(remove),
            output_dir=str(output),base_filename=name,progress_callback=report)
    finally:sys.setprofile(old_profiler)
    if result.get('status')!='success':raise ValueError(result.get('message','原 Zernike 分析失败。'))
    required=('report_figure_path','higher_order_path')
    if any(not result.get(k) or not Path(result[k]).is_file() for k in required):raise ValueError('原完整报告或高阶像差图未成功生成。')
    maps={
        'original_phase_rad':captured['original_masked'],
        'fitted_phase_rad':captured['fitted_background_2d'],
        'fitting_residual_rad':captured['residual_2d'],
        'higher_order_phase_rad':captured['phase_error_2d'],
        'removed_low_order_rad':captured['original_masked']-captured['phase_error_2d']}
    coeffs=np.asarray(result['zernike_coeffs'])
    modes=np.array([noll_to_nm(j) for j in range(1,terms+1)])
    np.savez_compressed(output/'results.npz',**maps,pupil_mask=mask,coefficients_rad=coeffs,modes_nm=modes)
    with (output/f'{name}_coefficients.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['Noll_j','n','m','coefficient_rad','coefficient_waves','removed'])
        writer.writerows((j,*modes[j-1],coef,coef/(2*np.pi),bool(modes[j-1,0]<=remove)) for j,coef in enumerate(coeffs,1))
    progress(80,'导出原函数的相位图、拟合图、低阶背景、高阶像差及残差')
    import matplotlib.pyplot as plt
    from PIL import Image
    for key,array in maps.items():
        np.save(output/f'{name}_{key}.npy',array,allow_pickle=False)
        fig,ax=plt.subplots(figsize=(7,5));im=ax.imshow(array,origin='upper',cmap='RdYlGn')
        fig.colorbar(im,ax=ax,label='Phase (rad)');ax.set(title=key,xlabel='X (pixels)',ylabel='Y (pixels)')
        fig.savefig(output/f'{name}_{key}.png',dpi=160,bbox_inches='tight')
        if config.get('export_tiff',True):
            fig.savefig(output/f'{name}_{key}_colorbar.tiff',dpi=300,bbox_inches='tight',pil_kwargs={'compression':'tiff_lzw'})
            Image.fromarray(array.astype(np.float32),mode='F').save(output/f'{name}_{key}_float32.tiff',compression='tiff_lzw')
        plt.close(fig)
    result.update(wavelength_um=wave,pixel_size_um=pixel,photon_energy_kev=config['photon_energy_kev'],
        terms=terms,max_order_remove=remove,center_xy_px=center.tolist(),radius_px=radius,
        roi_points=int(mask.sum()),image_shape_rc=list(phase.shape),
        pv_fitting_residual_rad=float(np.ptp(maps['fitting_residual_rad'][mask])),
        rms_fitting_residual_rad=float(np.std(maps['fitting_residual_rad'][mask])),
        coefficients=[{'j':j,'n':int(modes[j-1,0]),'m':int(modes[j-1,1]),'rad':float(v),'waves':float(v/(2*np.pi)),'removed':bool(modes[j-1,0]<=remove)} for j,v in enumerate(coeffs,1)],
        curvature_definition='Original fixed X/Y formula using Noll j4 and j6; not rotated principal curvatures.')
    metadata={'case':'zernike_full','config':config,'source_file':str(source),
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'input_sha256':hashlib.sha256(phase_path.read_bytes()).hexdigest(),
        'corrections':{'indexing':'Standard Noll; original mapping had invalid/duplicate modes.',
            'original_indices_nm':old_indices,'reference':INDEX_REFERENCE,
            'wavelength':'hc/E in µm; original GUI 1.24/E_keV was nm mislabeled µm.'},
        'scope':'Original fitting, radial-order subtraction, ROC formula and complete report. Corrected Noll indexing and energy units are explicit.'}
    (output/'metadata.json').write_text(json.dumps(safe_json(metadata),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    (output/'summary.json').write_text(json.dumps(safe_json(result),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    (output/f'{name}_analysis_report.txt').write_text(json.dumps(safe_json(result),ensure_ascii=False,indent=2),encoding='utf-8')
    progress(100,'完整 Zernike 分析完成')
