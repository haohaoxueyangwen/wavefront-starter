"""Double-click check_windows.cmd for a readable machine-specific diagnosis."""
from pathlib import Path
import json, platform, struct, sys
from wfs_starter.speckle_backends import catalog

root=Path(__file__).resolve().parents[1]
report={'system':platform.platform(),'python':platform.python_version(),'process_bits':struct.calcsize('P')*8,
        'package_root':str(root),'backends':catalog()}
print('Wavefront Starter · 本机环境检查\n')
print('系统：',report['system']);print('随包 Python：',report['python']);print('进程：',report['process_bits'],'位')
for key in ('cpp','gpu'):
    data=report['backends'][key]
    print('\n'+data['name']+'：'+('可用' if data['available'] else '不可用'))
    print(data['reason'])
print('\nCPU 可用就可以开始使用；GPU 不是必需条件。')
folder=root/'local-runs';folder.mkdir(exist_ok=True)
(folder/'environment_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('检查记录：'+str(folder/'environment_check.json'))
sys.exit(0 if report['backends']['cpp']['available'] else 1)
