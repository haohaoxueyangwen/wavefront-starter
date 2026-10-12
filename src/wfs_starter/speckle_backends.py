"""Explicit CPU / CUDA bridges. Never silently substitutes another implementation."""
from __future__ import annotations
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import numpy as np

PARAMETERS = {
    'search_half_window': (3, 1), 'template_half_window': (2, 1),
    'extended_half_window': (2, 1), 'n_cores': (1, 1), 'n_group': (1, 1),
    'n_iter': (1, 1), 'wavelet_level_cut': (0, 0), 'pyramid_level': (0, 0),
    'phase_cores': (1, 1), 'roi_size_px': (0, 0), 'gpu_device': (0, 0),
}

def integer(config, name):
    default, minimum = PARAMETERS[name]
    value = config.get(name, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value) or int(value) != value or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}')
    return int(value)

def settings(config):
    result = {key: integer(config, key) for key in PARAMETERS}
    if not isinstance(config.get('use_wavelet', True), bool):
        raise ValueError('use_wavelet must be boolean')
    result['use_wavelet'] = config.get('use_wavelet', True)
    return result

def catalog():
    from .runtime_backends import status
    cpp, gpu = status('cpp'), status('gpu')
    return {
        'python': {'name': 'Python CPU · 参考算法', 'available': True, 'reason': '完整原参数'},
        'cpp': {'name': 'C++ CPU · WSVT_CPP', **cpp},
        'gpu': {'name': 'GPU · 原生 C++ / CUDA / cuFFT 速度版',
                **gpu,
                'constraints': {'search_half_window':10, 'template_half_window':3, 'extended_half_window':4,
                                'pyramid_level':1, 'wavelet_level_cut':1, 'n_iter':1, 'use_wavelet':True},
                'wsvt_frames':100},
    }


def validate_backend(config):
    backend = config.get('backend', 'python')
    if backend not in {'python', 'cpp', 'gpu'}:
        raise ValueError('Unknown speckle backend')
    p = settings(config)
    if backend == 'cpp':
        from .runtime_backends import executable as locate
        executable = locate('cpp', config)
        if not executable or not Path(executable).is_file():
            raise ValueError('未找到 C++ CPU 程序，请使用 GitHub Release 的 Windows 完整包。')
    if backend == 'gpu':
        for key, expected in catalog()['gpu']['constraints'].items():
            if key == 'template_half_window' and config['mode'] == 'wsvt':
                continue
            actual = p.get(key)
            if actual != expected:
                raise ValueError(f'Edge GPU 固定 {key}={expected}；收到 {actual}，不会静默忽略该参数。')
        if config.get('gpu_front', 'auto') not in {'auto', 'fused', 'baseline'}:
            raise ValueError('重排实验未通过全图门限，当前前端不启用 reordered。')
        if config.get('gpu_spline', 'gpu') != 'gpu':
            raise ValueError('原生速度版固定 GPU 样条；旧 CPU 样条配置请改为 gpu。')
        if config.get('gpu_input_dtype', 'auto') not in {'auto', 'uint16', 'float32'}:
            raise ValueError('Invalid GPU input dtype')
        from .native_gpu import policies
        policies(config)
    return backend, p

def normalize(result):
    names = {'displace_x':'ux_px', 'displace_y':'uy_px', 'phase':'phase_rad',
             'DPC_x':'angle_x_rad_demeaned', 'DPC_y':'angle_y_rad_demeaned'}
    return {names.get(k,k): np.asarray(v) for k,v in result.items()}

def cpp_arguments(executable, source, output, config):
    p = settings(config)
    mapped = {'m_image':0, 'cal_half_window':p['search_half_window'], 'n_s':p['template_half_window'],
              'n_s_extend':p['extended_half_window'], 'n_cores':p['n_cores'], 'phase_cores':p['phase_cores'],
              'n_group':p['n_group'], 'energy':config['energy_ev'], 'p_x':config['pixel_size_m'],
              'z':config['distance_m'], 'wavelet_level_cut':p['wavelet_level_cut'],
              'pyramid_level':p['pyramid_level'], 'n_iter':p['n_iter'],
              'use_wavelet':p['use_wavelet'], 'use_gpu':False, 'save_img':False, 'h5_deflate':0, 'calc_darkfield':False}
    if config['mode'] == 'wsvt':
        mapped.pop('m_image'); mapped.pop('n_s')
        mapped.update(crop=0, n_template=0)
    # Arrays have already undergone an explicit ROI selection. CLI 0 = complete supplied image.
    args = [str(executable),config['mode'],str(source),'sample',str(source),'reference',str(output)]
    for key,value in mapped.items():
        args += ['--'+key, str(value).lower() if isinstance(value,bool) else str(value)]
    return args

def native_speckle(sample, reference, config):
    backend,p = validate_backend(config)
    if backend == 'cpp':
        import h5py
        from .runtime_backends import executable as locate
        executable = Path(locate('cpp',config)).resolve()
        with tempfile.TemporaryDirectory(prefix='wfs-cpp-') as temp:
            folder = Path(temp); source = folder/'input.h5'; output = folder/'output'
            with h5py.File(source,'w') as f:
                f['sample'] = np.asarray(sample,dtype=np.float32)
                f['reference'] = np.asarray(reference,dtype=np.float32)
            # Keep native I/O arguments ASCII even for Chinese Windows user/temp paths.
            args = cpp_arguments(executable,Path('input.h5'),Path('output'),config)
            subprocess.run(args,cwd=folder,check=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            file = output/(config['mode'].upper()+'_result.hdf5')
            with h5py.File(file,'r') as f:
                result = {key:np.asarray(f[key]) for key in f if f[key].ndim == 2}
        meta = {'backend':'cpp_cpu', 'executable_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(), 'parameters':p}
    else:
        from .native_gpu import solve
        result,meta = solve(sample, reference, config)
    fields=normalize(result)
    required={'ux_px','uy_px','phase_rad','angle_x_rad_demeaned','angle_y_rad_demeaned'}
    if not required.issubset(fields):raise ValueError('Native backend missing required output fields: '+str(required-set(fields)))
    if any(not np.isfinite(v).all() for v in fields.values()):raise ValueError('Native backend produced nonfinite output.')
    return fields,meta
