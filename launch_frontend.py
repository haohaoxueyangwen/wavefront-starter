"""Open one frontend and start its local service if needed."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time,webbrowser
from urllib.request import urlopen

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app',choices=['speckle','grating','hartmann','wavefront'],required=True)
    parser.add_argument('--port',type=int,default=8790)
    args=parser.parse_args();root=Path(__file__).resolve().parent
    config_file=root/'.local_runtime.json'
    config=json.loads(config_file.read_text(encoding='utf-8')) if config_file.is_file() else {}
    python=config.get('python') or str(root/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python'))
    if not Path(python).is_file():python=sys.executable
    workspace=Path(config.get('workspace') or root/'local-runs').resolve()
    workspace.mkdir(parents=True,exist_ok=True)
    origin=f'http://127.0.0.1:{args.port}'
    def ready():
        try:
            with urlopen(origin+'/api/session',timeout=1) as response:session=json.load(response)
            if session.get('application')!='wavefront-frontends':raise RuntimeError('端口被另一服务占用，请用 --port 选择其他端口。')
            return True
        except (OSError,ValueError):return False
    if not ready():
        env=os.environ.copy();env.update(config.get('environment',{}))
        log=workspace/'service.log'
        with log.open('ab') as stream:
            process=subprocess.Popen([python,'-B','-m','wfs_starter','ui','--no-browser','--port',str(args.port),'--workspace',str(workspace)],
                cwd=root,env=env,stdout=stream,stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),start_new_session=os.name!='nt')
        end=time.monotonic()+15
        while not ready():
            if process.poll() is not None or time.monotonic()>end:raise RuntimeError('启动失败，请查看 '+str(log))
            time.sleep(.2)
    webbrowser.open(origin+'/'+args.app)
    print(origin+'/'+args.app)

if __name__=='__main__':main()
