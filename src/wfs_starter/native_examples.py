"""Real BB11 CRL data shared by CPU, GPU and reference solvers."""
from pathlib import Path
import hashlib, json, re, tempfile, urllib.request, zipfile
from .config_templates import load_templates
from .speckle_backends import catalog

ROOT=Path(__file__).resolve().parents[2]
DATASET_ID='crl-bb11-20231102-roi512-v1'
ARCHIVE_SHA256='1eab44c5f689a2a25230746ff1d38ab180b01d987fffb981b56444ea3fa5f62f'
ARCHIVE_URL='https://github.com/haohaoxueyangwen/wavefront-starter/releases/download/v0.6.1/'+DATASET_ID+'.zip'

def verify(folder):
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('dataset_id')!=DATASET_ID or manifest.get('frames')!=100 or manifest.get('shape_yx')!=[512,512]:
        raise ValueError('CRL 示例清单不匹配，请使用本版发布的数据包。')
    names={f'{role}_{i:03}.npy' for role in ('reference','sample') for i in range(1,101)}
    if {item['file'] for item in manifest['files']}!=names or len(manifest['files'])!=200:
        raise ValueError('CRL 示例必须含原始扫描索引对应的 100 对帧。')
    for item in manifest['files']:
        if hashlib.sha256((folder/item['file']).read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('CRL 示例文件校验失败：'+item['file'])
    return manifest

def dataset(workspace):
    bundled=ROOT/'example-data/crl-bb11-v1'
    cached=Path(workspace)/'crl-bb11-v1'
    for folder in (bundled,cached):
        if folder.exists():return folder,verify(folder)
    workspace=Path(workspace);workspace.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='crl-download-',dir=workspace) as temporary:
        temp=Path(temporary);archive=temp/'data.zip';digest=hashlib.sha256();size=0
        try:
            with urllib.request.urlopen(ARCHIVE_URL,timeout=60) as response,archive.open('wb') as stream:
                while block:=response.read(1024*1024):
                    size+=len(block)
                    if size>125*1024*1024:raise ValueError('CRL 下载大小超过预期。')
                    digest.update(block);stream.write(block)
        except OSError as exc:
            raise ValueError('CRL 数据尚未安装。Windows 用户请下载 v0.6.1 完整包；源码用户需联网首次下载。数据地址：'+ARCHIVE_URL) from exc
        if digest.hexdigest()!=ARCHIVE_SHA256:raise ValueError('CRL 下载 SHA256 不匹配，请重新下载。')
        with zipfile.ZipFile(archive) as z:
            for name in z.namelist():
                if not re.fullmatch(r'crl-bb11-v1/(manifest\.json|(?:reference|sample)_\d{3}\.npy)',name):
                    raise ValueError('CRL 数据包含非预期路径。')
                target=temp/name;target.parent.mkdir(exist_ok=True)
                target.write_bytes(z.read(name))
        manifest=verify(temp/'crl-bb11-v1')
        (temp/'crl-bb11-v1').rename(cached)
    return cached,manifest

def example(workspace, mode, backend):
    if mode not in {'wsvt','wxst'} or backend not in {'cpp','gpu','python'}:raise ValueError('无效的散斑示例')
    folder,manifest=dataset(workspace)
    config=load_templates()[mode];calibration=manifest['calibration']
    config.update(backend=backend,energy_ev=calibration['energy_ev'],pixel_size_m=calibration['pixel_size_m'],distance_m=calibration['distance_m'],
        search_half_window=10,template_half_window=3,extended_half_window=4,pyramid_level=1,wavelet_level_cut=1,
        n_iter=1,n_cores=2,phase_cores=2,n_group=1,roi_size_px=0,
        example_dataset_id=DATASET_ID,example_crop_y0_y1_x0_x1=manifest['crop_y0_y1_x0_x1'],
        metadata_note='BB11 金刚石 CRL 实测数据，512×512 原值裁剪；沿用历史重建标定。')
    if mode=='wsvt':config.pop('template_half_window',None)
    if backend=='gpu':
        device=catalog()['gpu'];config.update(device['constraints']);config['gpu_device']=device.get('default_device',0)
    if mode=='wsvt':config['pairs']=[{'reference':str(folder/f'reference_{i:03}.npy'),'sample':str(folder/f'sample_{i:03}.npy')} for i in range(1,101)]
    else:config.update(reference=str(folder/'reference_001.npy'),sample=str(folder/'sample_001.npy'))
    return {'config':config,'base_dir':str(folder),
        'note':'已载入 BB11 CRL 实测数据：金刚石透镜，512×512 中央区域；'+('100 对扫描帧。' if mode=='wsvt' else '第 001 对参考 / 样品图。')+'点击运行算法。标定沿用实验历史重建记录。'}
