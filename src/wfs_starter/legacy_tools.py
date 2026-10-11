"""Adapters to user's maintained advanced tools, without copying scientific implementations."""
from pathlib import Path
import hashlib
import importlib
import os
import sys
import threading

_hartmann_lock=threading.Lock()

def project(env):
    root=Path(os.environ.get(env,'')).expanduser().resolve()
    if not os.environ.get(env) or not root.is_dir():raise ValueError(f'请在启动环境配置 {env} 指向原算法工程。')
    return root

def hartmann_module():
    root=project('WFS_HARTMANN_PROJECT')
    if str(root) not in sys.path:sys.path.insert(0,str(root))
    return importlib.import_module('modes.xray.visualization.hartmann_designer_server')

def hartmann_operation(route,data):
    with _hartmann_lock:
        module=hartmann_module()
        if route=='/api/simulate':return module.run_simulation(data)
        if route=='/api/recover':return module.run_recovery(data)
        if route=='/api/summary':return module.collect_summary(module._resolve_run_dir(data.get('run_dir')),method=data.get('method'))
        if route in {'/api/rotation/estimate','/api/rotation/run'}:
            service=importlib.import_module('modes.xray.visualization.rotation_parameter_service')
            return (service.estimate if route.endswith('estimate') else service.start_trial)(data)
        raise ValueError('Unknown Hartmann operation')

def hartmann_file(relative):
    module=hartmann_module();root=module.ROOT.resolve();path=(root/relative).resolve()
    if not path.is_relative_to(root/'result'/'xray') or not path.is_file():raise FileNotFoundError('Only Hartmann output files can be viewed.')
    if path.suffix.lower() not in {'.png','.jpg','.json','.csv','.npz','.npy','.txt','.html'}:raise FileNotFoundError('Unsupported result type')
    return path

def source_locations():
    return {'wavefront':os.environ.get('WFS_ANALYSIS_SOURCE',''), 'hartmann':os.environ.get('WFS_HARTMANN_PROJECT','')}

def run_analysis(config,output):
    import json
    root=Path(config.get('analysis_source_dir') or os.environ.get('WFS_ANALYSIS_SOURCE','')).expanduser().resolve()
    if not (root/'zernike_ui'/'runner.py').is_file():raise ValueError('请选择包含 zernike_ui 和 focus_analysis 的原波前分析工程。')
    sys.path.insert(0,str(root))
    output=Path(output).resolve();output.mkdir(exist_ok=False,parents=True)
    mode=config['mode']
    if mode=='surface':
        if config.get('phase_unit')!='rad':raise ValueError('原曲率/高度分析入口接收相位 rad；OPD 请先明确转换。')
        if config.get('use_delta') and float(config.get('delta',0))<=0:raise ValueError('启用材料转换时，请提供正的 delta。')
        from .core import positive
        positive(config['energy_ev'],'energy_ev');positive(config['pixel_size_um'],'pixel_size_um')
        runner=importlib.import_module('zernike_ui.runner')
        params=dict(phase_path=config['phase'],phase_unit='rad',output_dir=str(output),run_name='analysis',
                    energy_ev=config['energy_ev'],delta=config['delta'],pixel_size_um=config['pixel_size_um'],
                    threshold=config['threshold_value'] if config['threshold_mode']=='custom' else config['threshold_mode'],
                    select_mode=config['select_mode'],use_delta=config['use_delta'],
                    refit_residual=config['refit_residual'],surfaces=config['surfaces'],show=False)
        # Keep original PDF exports and additionally save the same figures for browser previews.
        from matplotlib.figure import Figure
        savefig=Figure.savefig
        def save_with_preview(figure,filename,*args,**kwargs):
            result=savefig(figure,filename,*args,**kwargs)
            if isinstance(filename,(str,Path)):
                file=Path(filename).resolve()
                if file.is_relative_to(output) and file.suffix.lower()=='.pdf':
                    savefig(figure,file.with_suffix('.png'),dpi=130,bbox_inches='tight')
            return result
        Figure.savefig=save_with_preview
        try:runner.run_workflow(params,log_cb=print)
        finally:Figure.savefig=savefig
        source=root/'zernike_ui'/'runner.py'
    elif mode=='focus':
        if float(config['step_z'])==0:raise ValueError('扫描步长不能为 0。')
        for flag,key in [('do_dark','dark_dir'),('do_flat','flat_dir')]:
            if config.get(flag) and not config.get(key):raise ValueError('启用校正时必须选择 '+key)
        for key in ('images_per_pos','n_workers'):
            value=config[key]
            if isinstance(value,bool) or int(value)!=value or value<1:raise ValueError(key+' must be a positive integer')
        runner=importlib.import_module('focus_analysis.run_analysis')
        params={k:v for k,v in config.items() if k not in {'mode','analysis_source_dir'}}
        params.update(output_dir=str(output),show_plots=False)
        runner.run_analysis(params,progress_callback=print)
        source=root/'focus_analysis'/'run_analysis.py'
    else:raise ValueError('Unknown advanced analysis mode')
    metadata={'case':mode,'config':config,'source_file':str(source),
              'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
              'scope':'Uses the existing analysis workflow; outputs are isolated from input data.'}
    (output/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'case':mode,'output':str(output)},ensure_ascii=False))
