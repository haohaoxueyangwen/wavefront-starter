"""File bridge to the frozen native C++/CUDA/cuFFT CLI (no Torch runtime)."""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import json
import numpy as np

NAMES = ('displace_y', 'displace_x', 'DPC_y', 'DPC_x', 'phase',
         'transmission', 'match_score_neg_ssd')

def policies(config):
    target = config.get('gpu_platform', 'auto')
    if target == 'auto':
        target = 'jetson' if platform.system() == 'Linux' and Path('/etc/nv_tegra_release').is_file() else 'desktop'
    if target not in {'desktop', 'jetson'}:
        raise ValueError('gpu_platform must be auto, desktop or jetson')
    workspace = config.get('gpu_workspace', 'speed')
    if workspace not in {'speed', 'low-memory'}:
        raise ValueError('gpu_workspace must be speed or low-memory')
    if workspace == 'low-memory' and config['mode'] != 'wsvt':
        raise ValueError('低内存工作区只适用于 WSVT。')
    policy = config.get('gpu_input_policy', 'auto')
    if policy == 'auto':
        policy = 'mapped' if target == 'jetson' and config['mode'] == 'wsvt' else 'copy'
    if policy not in {'copy', 'mapped'} or (policy == 'mapped' and target != 'jetson'):
        raise ValueError('mapped 输入只适用于 Jetson。')
    chunk = config.get('gpu_chunk', 16)
    if isinstance(chunk, bool) or not isinstance(chunk, int) or not 1 <= chunk <= 100:
        raise ValueError('gpu_chunk must be an integer in 1..100')
    return target, workspace, policy, chunk

def input_arrays(sample, reference, config):
    mode = config['mode']
    if sample.shape != reference.shape:
        raise ValueError('GPU sample/reference shape mismatch')
    if (mode == 'wsvt' and (sample.ndim != 3 or sample.shape[0] != 100)) or (mode == 'wxst' and sample.ndim != 2):
        raise ValueError('原生 GPU：WSVT 恰好 100 对帧；WXST 为一对二维图。')
    if min(sample.shape[-2:]) <= 28:
        raise ValueError('GPU H/W must be >28')
    if sample.shape[-2] * sample.shape[-1] * 100 > 2147483647:
        raise ValueError('GPU H*W*100 exceeds the frozen kernel indexing limit')
    dtype = config.get('gpu_input_dtype', 'auto')
    if dtype == 'auto':
        dtype = 'uint16' if mode == 'wsvt' and sample.dtype == reference.dtype == np.uint16 else 'float32'
    if dtype not in {'uint16', 'float32'}:
        raise ValueError('Invalid GPU input dtype')
    if dtype == 'uint16' and (mode != 'wsvt' or sample.dtype != np.uint16 or reference.dtype != np.uint16):
        raise ValueError('uint16 只接受原始 uint16 WSVT 数据；不量化浮点或校正数据。')
    arrays = tuple(np.ascontiguousarray(a, dtype='<u2' if dtype == 'uint16' else '<f4') for a in (sample, reference))
    if any(not np.isfinite(a).all() for a in arrays):
        raise ValueError('Nonfinite GPU input after dtype conversion')
    return arrays

def arguments(executable, sample, reference, output, config):
    target, workspace, policy, chunk = policies(config)
    options = {'mode': config['mode'], 'sample': sample, 'reference': reference,
               'out': output, 'pixel-m': config['pixel_size_m'],
               'distance-m': config['distance_m'], 'energy-ev': config['energy_ev'],
               'platform': target, 'workspace': workspace, 'input-policy': policy,
               'chunk': chunk, 'device': config.get('gpu_device', 0),
               'warmup': 0, 'repeats': 1, 'reference-policy': 'each-pair'}
    return [str(executable)] + [str(v) for key, value in options.items() for v in ('--'+key, value)]

def solve(sample, reference, config):
    from .runtime_backends import executable as locate
    raw = locate('gpu', config)
    if not raw or not Path(raw).is_file():
        raise ValueError('未找到 GPU 程序，请使用 GitHub Release 的 Windows 完整包；没有兼容 NVIDIA 显卡时请选择 C++ CPU。')
    executable = Path(raw).resolve()
    sample, reference = input_arrays(sample, reference, config)
    with tempfile.TemporaryDirectory(prefix='wfs-native-gpu-') as temp:
        folder = Path(temp)
        np.save(folder/'sample.npy', sample, allow_pickle=False)
        np.save(folder/'reference.npy', reference, allow_pickle=False)
        output = folder/'result'
        args = arguments(executable, Path('sample.npy'), Path('reference.npy'), Path('result'), config)
        # Inherit stdout/stderr so job logs contain native failures; never retry with a CPU solver.
        subprocess.run(args, cwd=folder, check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        result = {name: np.load(output/(name+'.npy'), allow_pickle=False) for name in NAMES}
        report = json.loads((output/'report.json').read_text())
        trials = list(__import__('csv').DictReader((output/'timing.csv').open()))
    h, w = sample.shape[-2:]
    for name, array in result.items():
        expected = (h, w) if name == 'transmission' else (h-20, w-20)
        if array.shape != expected or array.dtype != np.float32 or not np.isfinite(array).all():
            raise ValueError('Invalid native output: '+name)
    for key, expected in {'implementation': 'native C++/CUDA/cuFFT', 'mode': config['mode'],
                          'height': h, 'width': w, 'frames': 100 if config['mode']=='wsvt' else 1,
                          'reference_policy': 'each-pair', 'repeats': 1, 'warmup': 0}.items():
        if report.get(key) != expected:
            raise ValueError('Native report contract mismatch: '+key)
    meta = {'backend': 'native_cpp_cuda_cufft',
            'packaged_source_commit': '3f418aa71771e9d209af0702b742ac7e7a69aa9a',
            'executable_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
            'input_dtype': str(sample.dtype), 'runtime': report, 'trials': trials,
            'transmission_origin_xy_px': [0, 0], 'reconstruction_origin_xy_px': [10, 10],
            'timing_scope': 'One GUI task starts a new CLI process; file conversion, startup and saving add latency. Hot-session published benchmark times do not predict GUI wall time.',
            'phase_convention': 'Preserved GPU sign and FFT convention; DPC displacement mean and phase piston removed.'}
    return result, meta
