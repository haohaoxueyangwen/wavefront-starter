"""Locate bundled native programs and probe them without running a reconstruction."""
from pathlib import Path
from functools import lru_cache
import json, os, shutil, subprocess

ROOT = Path(__file__).resolve().parents[2]

def executable(kind, config=None):
    key = 'cpp_executable' if kind == 'cpp' else 'gpu_executable'
    env = 'WFS_CPP_EXE' if kind == 'cpp' else 'WFS_GPU_EXE'
    supplied = (config or {}).get(key) or os.environ.get(env)
    if supplied: return str(Path(supplied).expanduser().resolve())
    name = 'wsvt_cli' if kind == 'cpp' else 'speckle_gpu'
    if os.name == 'nt': name += '.exe'
    bundled = ROOT/'runtime/native/windows'/('cpu' if kind=='cpp' else 'gpu')/name
    if bundled.is_file(): return str(bundled)
    return shutil.which(name) or ''

@lru_cache(maxsize=8)
def probe(path, stamp):
    try:
        p = subprocess.run([path,'--probe'],capture_output=True,text=True,encoding='utf-8',errors='replace',
                           timeout=5,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if p.returncode:
            return {'available':False,'reason':(p.stderr.strip() or p.stdout.strip() or
                '程序无法启动，运行库或 NVIDIA 驱动不可用')[:500]}
        data = json.loads(p.stdout)
        if 'devices' in data:
            devices=data['devices'];ready=[d for d in devices if d.get('available')]
            return {'available':bool(ready),'devices':devices,'default_device':ready[0]['index'] if ready else 0,
                    'reason':'; '.join(d['name']+' · '+str(round(d['memory_bytes']/2**30,1))+' GB 显存' for d in ready)
                             if ready else '没有检测到与随包 CUDA/cuFFT 兼容的 NVIDIA GPU；请选择 C++ CPU。'}
        return {'available':True,'reason':'随包 C++ CPU 已就绪（HDF5 / FFTW / OpenMP）'}
    except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
        return {'available':False,'reason':'本机后端检查失败：'+str(exc)[:350]}

def status(kind):
    path=executable(kind)
    if not path or not Path(path).is_file():
        return {'available':False,'path':'','reason':'源码包未含 Windows 程序；请下载 GitHub Release 的 windows-x64.zip 完整包。'}
    # Frozen Linux CLIs predate --probe; preserve their explicit executable workflow.
    data=probe(path,Path(path).stat().st_mtime_ns) if os.name=='nt' else {'available':True,'reason':'本机原生程序已找到'}
    return {'path':path,**data}
