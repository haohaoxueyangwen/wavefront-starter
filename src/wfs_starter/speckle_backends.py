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
    cpp = os.environ.get('WFS_CPP_EXE', '')
    gpu = os.environ.get('WFS_GPU_SOURCE', '')
    gpu_lib = Path(gpu) / ('edge_kernels.dll' if os.name == 'nt' else 'libedge_kernels.so')
    return {
        'python': {'name': 'Python CPU · 参考算法', 'available': True, 'reason': '完整原参数'},
        'cpp': {'name': 'C++ CPU · WSVT_CPP', 'available': bool(cpp and Path(cpp).is_file()),
                'path': cpp, 'reason': '已指定可执行文件' if cpp and Path(cpp).is_file() else '请选择本机 wsvt_cli 可执行文件'},
        'gpu': {'name': 'CUDA GPU · Edge 优化版',
                'available': bool(gpu and (Path(gpu)/'edge_runtime.py').is_file() and gpu_lib.is_file() and importlib.util.find_spec('torch')),
                'path': gpu, 'reason': '需要匹配本机的 CUDA 库及 PyTorch；Orin ARM 库不能直接在 Windows 使用',
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
        executable = config.get('cpp_executable') or os.environ.get('WFS_CPP_EXE', '')
        if not executable or not Path(executable).is_file():
            raise ValueError('C++ CPU 尚未配置：请浏览选择 wsvt_cli.exe（或 Linux wsvt_cli）。')
    if backend == 'gpu':
        for key, expected in catalog()['gpu']['constraints'].items():
            if key == 'template_half_window' and config['mode'] == 'wsvt':
                continue
            actual = p.get(key)
            if actual != expected:
                raise ValueError(f'Edge GPU 固定 {key}={expected}；收到 {actual}，不会静默忽略该参数。')
        if config.get('gpu_front', 'auto') not in {'auto', 'fused', 'materialized', 'baseline'}:
            raise ValueError('重排实验未通过全图门限，当前前端不启用 reordered。')
        if config.get('gpu_spline', 'gpu') not in {'cpu', 'gpu'}:
            raise ValueError('gpu_spline must be cpu or gpu')
        if config.get('gpu_input_dtype', 'auto') not in {'auto', 'uint16', 'float32'}:
            raise ValueError('Invalid GPU input dtype')
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
              'use_wavelet':p['use_wavelet'], 'use_gpu':False, 'save_img':False, 'h5_deflate':0}
    # Arrays have already undergone an explicit ROI selection. CLI 0 = complete supplied image.
    args = [str(executable),config['mode'],str(source),'sample',str(source),'reference',str(output)]
    for key,value in mapped.items():
        args += ['--'+key, str(value).lower() if isinstance(value,bool) else str(value)]
    return args

def native_speckle(sample, reference, config):
    backend,p = validate_backend(config)
    if backend == 'cpp':
        import h5py
        executable = Path(config.get('cpp_executable') or os.environ['WFS_CPP_EXE']).resolve()
        with tempfile.TemporaryDirectory(prefix='wfs-cpp-') as temp:
            folder = Path(temp); source = folder/'input.h5'; output = folder/'output'
            with h5py.File(source,'w') as f:
                f['sample'] = np.asarray(sample,dtype=np.float32)
                f['reference'] = np.asarray(reference,dtype=np.float32)
            args = cpp_arguments(executable,source,output,config)
            subprocess.run(args,check=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            file = output/(config['mode'].upper()+'_result.hdf5')
            with h5py.File(file,'r') as f:
                result = {key:np.asarray(f[key]) for key in f if f[key].ndim == 2}
        meta = {'backend':'cpp_cpu', 'executable_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(), 'parameters':p}
    else:
        folder = Path(config.get('gpu_source_dir') or os.environ.get('WFS_GPU_SOURCE','')).resolve()
        source = folder/'edge_runtime.py'
        if not source.is_file():raise ValueError('请浏览选择包含 edge_runtime.py 的 GPU 源目录。')
        library = folder/('edge_kernels.dll' if os.name=='nt' else 'libedge_kernels.so')
        if not library.is_file():raise ValueError('GPU 源码已找到，但缺少当前系统编译的 CUDA 库：'+str(library))
        if importlib.util.find_spec('torch') is None:raise ValueError('当前 Python 环境缺少 CUDA PyTorch。')
        import torch
        if not torch.cuda.is_available():raise ValueError('当前 Python 环境未检测到可用 CUDA GPU。')
        if p['gpu_device'] >= torch.cuda.device_count():raise ValueError('GPU 设备编号超出范围。')
        spec=importlib.util.spec_from_file_location('_wfs_edge_runtime',source)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        # The measured source loads .so. Windows builds can supply the same ABI as a DLL.
        if os.name=='nt':
            original_native=module.Native
            class WindowsNative(original_native):
                def __init__(self):
                    import ctypes as C
                    original_loader=module.C.CDLL
                    def loader(path,*args,**kwargs):
                        if str(path)==str(folder/'libedge_kernels.so'):path=library
                        return original_loader(path,*args,**kwargs)
                    module.C.CDLL=loader
                    try:super().__init__()
                    finally:module.C.CDLL=original_loader
            module.Native=WindowsNative
        front=config.get('gpu_front','auto')
        if front=='auto':front='fused' if config['mode']=='wxst' else 'baseline'
        allowed={'fused','materialized'} if config['mode']=='wxst' else {'baseline'}
        if front not in allowed:raise ValueError('GPU front 与当前方法不匹配。')
        if config['mode']=='wsvt' and sample.shape[0]!=100:raise ValueError('当前 Edge WSVT GPU 版本要求恰好 100 对帧。')
        dtype=config.get('gpu_input_dtype','auto')
        if dtype=='auto':dtype='uint16' if config['mode']=='wsvt' and sample.dtype==reference.dtype==np.uint16 else 'float32'
        if dtype=='uint16' and (config['mode']!='wsvt' or sample.dtype!=np.uint16 or reference.dtype!=np.uint16):
            raise ValueError('uint16 入口只接受真实 uint16 WSVT 图像；不量化浮点数据。')
        sample=np.ascontiguousarray(sample,dtype=dtype);reference=np.ascontiguousarray(reference,dtype=dtype)
        torch.set_num_threads(p['n_cores'])
        cls=module.WXSTEdgeSession if config['mode']=='wxst' else module.WSVTEdgeSession
        with cls(sample.shape[-2:],front=front,spline=config.get('gpu_spline','gpu'),device=p['gpu_device'],
                 cpu_threads=p['n_cores'],pixel=config['pixel_size_m'],distance=config['distance_m'],energy=config['energy_ev'],input_dtype=dtype) as session:
            session.prepare_reference(reference);result,info=session.solve(sample)
        meta={'backend':'cuda_edge', 'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
              'library_sha256':hashlib.sha256(library.read_bytes()).hexdigest(),'device':torch.cuda.get_device_name(p['gpu_device']), 'runtime':info}
    fields=normalize(result)
    required={'ux_px','uy_px','phase_rad','angle_x_rad_demeaned','angle_y_rad_demeaned'}
    if not required.issubset(fields):raise ValueError('Native backend missing required output fields: '+str(required-set(fields)))
    if any(not np.isfinite(v).all() for v in fields.values()):raise ValueError('Native backend produced nonfinite output.')
    return fields,meta
