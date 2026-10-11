"""User-directed local browsing; no upload and no recursive data traversal."""
from pathlib import Path
import base64
import io
import os
import re

IMAGE_SUFFIXES={'.tif','.tiff','.png','.bmp','.jpg','.jpeg','.npy'}

def natural_key(path):
    return [(1,int(part)) if part.isdigit() else (0,part.casefold()) for part in re.split(r'(\d+)',path.name)]

def browse(raw='',kind='file',base=''):
    if kind not in {'file','directory'}:raise ValueError('Invalid browse kind')
    path=(Path(base or Path.cwd())/raw).expanduser().resolve() if raw else Path(base or Path.cwd()).expanduser().resolve()
    if not path.exists():path=Path(base or Path.cwd()).expanduser().resolve()
    if path.is_file():path=path.parent
    if not path.is_dir():raise ValueError('目录不存在：'+str(path))
    entries=[]
    for p in sorted(path.iterdir(),key=lambda p:(not p.is_dir(),natural_key(p))):
        if p.name.startswith('.') or p.is_symlink():continue
        try:
            if p.is_dir():entries.append({'name':p.name,'path':str(p),'directory':True})
            elif kind=='file' and (p.suffix.lower() in IMAGE_SUFFIXES|{'.exe','.json','.npz','.h5','.hdf5'} or p.name=='wsvt_cli'):
                entries.append({'name':p.name,'path':str(p),'directory':False})
        except OSError:continue
    drives=[f'{letter}:/' for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ' if Path(f'{letter}:/').is_dir()] if os.name=='nt' else ['/']
    return {'path':str(path),'parent':str(path.parent),'entries':entries,'drives':drives}

def paired_directories(reference,sample):
    folders=[Path(value).expanduser().resolve() for value in (reference,sample)]
    if not all(p.is_dir() for p in folders):raise ValueError('请选择参考帧和样品帧目录。')
    files=[sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES),key=natural_key) for folder in folders]
    if len(files[0])!=len(files[1]) or len(files[0])<2:
        raise ValueError(f'目录需包含相同数量的至少两帧；目前 {len(files[0])} / {len(files[1])}。')
    return {'pairs':[{'reference':str(a),'sample':str(b)} for a,b in zip(*files)],
            'ordering':'自然文件名顺序；运行前请核对逐行对应，不推断扫描坐标。'}

def preview(raw,base='',spectrum=False):
    from .core import image
    import numpy as np
    from PIL import Image
    path=(Path(base or Path.cwd())/raw).resolve()
    a=image(path);shape=list(a.shape)
    if spectrum:a=np.log1p(np.abs(np.fft.fftshift(np.fft.fft2(a))))
    lo,hi=np.percentile(a,[1,99.8]);a=np.clip((a-lo)/(hi-lo if hi>lo else 1),0,1)
    picture=Image.fromarray(np.uint8(a*255),'L');picture.thumbnail((1000,1000))
    stream=io.BytesIO();picture.save(stream,format='PNG')
    return {'shape_rc':shape,'image':'data:image/png;base64,'+base64.b64encode(stream.getvalue()).decode('ascii')}
