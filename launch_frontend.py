"""Open one frontend and start its local service if needed."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time,webbrowser
from urllib.request import urlopen

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app',choices=['speckle','grating','hartmann','wavefront'],required=True)
    parser.add_argument('--port',type=int,default=8790)
    parser.add_argument('--no-browser',action='store_true',help='仅用于诊断：启动后台但不打开浏览器')
    args=parser.parse_args();root=Path(__file__).resolve().parent
    config_file=root/'.local_runtime.json'
    config=json.loads(config_file.read_text(encoding='utf-8')) if config_file.is_file() else {}
    bundled=root/'runtime/python/python.exe'
    python=str(bundled) if os.name=='nt' and bundled.is_file() else config.get('python') or str(root/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python'))
    if not Path(python).is_file():python=sys.executable
    workspace=Path(config.get('workspace') or root/'local-runs').resolve()
    workspace.mkdir(parents=True,exist_ok=True)
    origin=f'http://127.0.0.1:{args.port}'
    def ready():
        try:
            with urlopen(origin+'/api/session',timeout=8) as response:session=json.load(response)
            if session.get('application')!='wavefront-frontends':raise RuntimeError('端口被另一服务占用，请用 --port 选择其他端口。')
            if session.get('version')!='0.6.3':raise RuntimeError('检测到旧版后台仍在运行。请关闭旧版启动窗口或运行 stop_frontends.cmd，再重新启动新版。')
            if Path(session.get('application_root','')).resolve()!=root:raise RuntimeError('另一份目录的波前工具后台正在运行。请先用该目录的 stop_frontends.cmd 停止，再打开这一份。')
            return True
        except (OSError,ValueError):return False
    if not ready():
        env=os.environ.copy();env.update(config.get('environment',{}))
        log=workspace/'service.log'
        with log.open('ab') as stream:
            process=subprocess.Popen([python,'-B','-m','wfs_starter','ui','--no-browser','--port',str(args.port),'--workspace',str(workspace)],
                cwd=root,env=env,stdout=stream,stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),start_new_session=os.name!='nt')
        end=time.monotonic()+30
        while not ready():
            if process.poll() is not None or time.monotonic()>end:raise RuntimeError('启动失败，请查看 '+str(log))
            time.sleep(.2)
    if not args.no_browser:webbrowser.open(origin+'/'+args.app)
    print(origin+'/'+args.app)

if __name__=='__main__':main()
