"""Loopback teaching UI; jobs call the existing CLI in an owned CPU subprocess."""
from __future__ import annotations

import json
import math
import mimetypes
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse
import webbrowser

MODES = ('wxst', 'wsvt', 'grating', 'hartmann', 'zernike')
ASSETS = Path(__file__).with_name('web')

def phase_result(job):
    """Advertise only an actual reconstructed phase, never a fringe phase."""
    import numpy as np
    folder = Path(job['output_dir'])
    result = folder/'demo'/job['mode']/'results'/'results.npz' if job['action'] == 'demo' else folder/'results'/'results.npz'
    if job['status'] != 'succeeded' or not result.is_file():
        return None
    with np.load(result, allow_pickle=False) as arrays:
        if 'phase_rad' not in arrays.files:
            return None
    return {'file':result.relative_to(folder).as_posix(), 'field':'phase_rad', 'unit':'rad'}

def prepare_config(config, base):
    """Resolve user-declared input paths; never infer physical calibration."""
    if not isinstance(config, dict) or config.get('mode') not in MODES:
        raise ValueError('请选择有效的方法并提供 JSON 配置对象。')
    base = Path(base).expanduser().resolve()
    if not base.is_dir():
        raise ValueError('数据基准目录不存在。')
    def visit(value, key='config'):
        if value is None:
            raise ValueError(f'请填写配置项 {key}；标定数值不能留空。')
        if isinstance(value, dict):
            return {k: visit(v, f'{key}.{k}') for k, v in value.items()}
        if isinstance(value, list):
            return [visit(v, f'{key}[{i}]') for i, v in enumerate(value)]
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f'{key} 必须是有限数值。')
        if key.rsplit('.', 1)[-1] in {'reference', 'sample', 'phase', 'dark', 'flat'}:
            if not value and key.rsplit('.', 1)[-1] in {'dark', 'flat'}:
                return value
            if not isinstance(value, str) or not value:
                raise ValueError(f'{key} 必须是文件路径。')
            p = (base / value).resolve()
            if not p.is_file():
                raise ValueError(f'找不到输入文件：{p}')
            return str(p)
        return value
    return visit(config)

class JobStore:
    def __init__(self, workspace):
        self.workspace = Path(workspace).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.jobs = {}
        self.lock = threading.RLock()
        self.active = None
        for folder in sorted(self.workspace.iterdir()):
            if not folder.is_dir() or not re.fullmatch('[a-f0-9]{16}', folder.name):
                continue
            record = folder/'job.json'
            if not record.is_file():
                continue
            try:
                job = json.loads(record.read_text(encoding='utf-8'))
                if job['status'] not in {'succeeded', 'failed', 'cancelled'}:
                    continue
                job.update(id=folder.name, output_dir=str(folder), process=None)
                job['phase_output'] = phase_result(job)
                self.jobs[folder.name] = job
            except (ValueError, KeyError, TypeError):
                continue

    def start(self, payload):
        if not isinstance(payload, dict):
            raise ValueError('任务需要是 JSON 对象。')
        action, mode = payload.get('action'), payload.get('mode')
        if action not in {'demo', 'run'} or mode not in MODES:
            raise ValueError('无效的任务或方法。')
        config = None
        if action == 'run':
            config = prepare_config(payload.get('config'), payload.get('base_dir') or '')
            if config['mode'] != mode:
                raise ValueError('配置 mode 与所选方法不一致。')
        with self.lock:
            if self.active:
                raise RuntimeError('已有任务在运行，请等待完成或停止当前任务。')
            ident = secrets.token_hex(8)
            folder = self.workspace / ident
            folder.mkdir(exist_ok=False)
            job = dict(id=ident, mode=mode, action=action, status='queued',
                       started=time.time(), finished=None, output_dir=str(folder),
                       cancel_requested=False, process=None)
            if config is not None:
                (folder/'config.json').write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
            self.jobs[ident] = job
            self.active = ident
            threading.Thread(target=self._run, args=(job,), daemon=True).start()
            return ident

    def _run(self, job):
        folder = Path(job['output_dir'])
        args = [sys.executable, '-B', '-m', 'wfs_starter']
        if job['action'] == 'demo':
            args += ['demo', '--case', job['mode'], '--output', str(folder/'demo')]
        else:
            args += ['run', str(folder/'config.json'), '--output', str(folder/'results')]
        try:
            env = os.environ.copy()
            env.update(PYTHONIOENCODING='utf-8', MPLBACKEND='Agg')
            with (folder/'run.log').open('wb') as log:
                with self.lock:
                    if job['cancel_requested']:
                        job['status'] = 'cancelled'
                        return
                    job['process'] = subprocess.Popen(args, cwd=self.workspace,
                        stdout=log, stderr=subprocess.STDOUT, env=env,
                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                    job['status'] = 'running'
                code = job['process'].wait()
            if code == 0 and not job['cancel_requested']:
                from .ui_plots import add_previews
                add_previews(folder)
            with self.lock:
                job['status'] = 'cancelled' if job['cancel_requested'] else 'succeeded' if code == 0 else 'failed'
                job['exit_code'] = code
                job['phase_output'] = phase_result(job)
        except Exception as exc:
            job['status'] = 'failed'
            job['error'] = str(exc)
        finally:
            with self.lock:
                job['finished'] = time.time()
                job['process'] = None
                self.active = None
                (folder/'job.json').write_text(json.dumps(self.snapshot(job['id']), ensure_ascii=False, indent=2), encoding='utf-8')

    def cancel(self, ident):
        with self.lock:
            job = self.jobs[ident]
            if job['status'] not in {'queued', 'running'}:
                return
            job['cancel_requested'] = True
            process = job['process']
            if process is not None:
                process.terminate()

    def snapshot(self, ident):
        with self.lock:
            job = self.jobs[ident]
            out = {k: v for k, v in job.items() if k != 'process'}
            folder = Path(job['output_dir'])
            log = folder/'run.log'
            out['log'] = log.read_bytes()[-24000:].decode('utf-8', errors='replace') if log.exists() else ''
            out['elapsed_s'] = round((job['finished'] or time.time()) - job['started'], 1)
            out['files'] = [p.relative_to(folder).as_posix() for p in sorted(folder.rglob('*'))
                            if p.is_file() and p.suffix.lower() in {'.png', '.json', '.npz', '.log'}]
            return out

    def asset(self, ident, name):
        folder = Path(self.jobs[ident]['output_dir'])
        path = (folder / name).resolve()
        if not path.is_relative_to(folder) or not path.is_file():
            raise FileNotFoundError('找不到该任务文件。')
        if path.suffix.lower() not in {'.png', '.json', '.npz', '.npy', '.log'}:
            raise FileNotFoundError('不可预览的文件类型。')
        return path

    def phase_input(self, ident):
        """Copy a completed phase into an explicit, traceable analysis input."""
        import numpy as np
        with self.lock:
            job = self.jobs[ident]
            candidate = phase_result(job)
            if candidate is None:
                raise ValueError('该结果没有可供分解的相位 rad；条纹相位和光斑位移需先完成波前恢复。')
            source = self.asset(ident, candidate['file'])
            with np.load(source, allow_pickle=False) as arrays:
                phase = arrays['phase_rad']
                if phase.ndim != 2 or min(phase.shape) < 8 or not np.isrealobj(phase) or not np.isfinite(phase).all():
                    raise ValueError('相位必须是至少 8×8 的有限实数二维数组。')
                destination = source.parent/'analysis-input'
                destination.mkdir(exist_ok=True)
                target = destination/'phase_rad.npy'
                if target.exists():
                    if not np.array_equal(np.load(target, allow_pickle=False), phase):
                        raise ValueError('已有相位接续文件与本次结果不同，请检查原输出。')
                else:
                    np.save(target, phase, allow_pickle=False)
                provenance = {'source_job':ident, 'source_mode':job['mode'],
                              'source_result':candidate['file'], 'field':'phase_rad',
                              'unit':'rad', 'shape_rc':list(phase.shape)}
                (destination/'source.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'config':{'mode':'zernike', 'phase':str(target), 'phase_unit':'rad',
                          'center_xy_px':None, 'radius_px':None, 'terms':15,
                          'phase_source':provenance}, 'shape_rc':provenance['shape_rc']}

def make_server(workspace, port=0):
    store = JobStore(workspace)
    token = secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send(self, value, status=200, content_type='application/json; charset=utf-8'):
            raw = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            try:
                # Do not accept DNS rebinding requests from external hostnames.
                if self.headers.get('Host') not in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}:
                    self.send({'error':'无效的本地地址。'}, 403); return
                path = unquote(urlparse(self.path).path)
                if path == '/':
                    self.send((ASSETS/'index.html').read_bytes(), content_type='text/html; charset=utf-8')
                elif path in {'/app.js', '/style.css'}:
                    self.send((ASSETS/path[1:]).read_bytes(), content_type='text/javascript; charset=utf-8' if path.endswith('.js') else 'text/css; charset=utf-8')
                elif path == '/api/session':
                    with store.lock:
                        jobs = [store.snapshot(i) for i in sorted(store.jobs, key=lambda ident: store.jobs[ident]['started'])]
                    self.send({'token':token, 'workspace':str(store.workspace), 'base_dir':str(Path.cwd()),
                               'templates':json.loads((ASSETS/'templates.json').read_text(encoding='utf-8')),
                               'jobs':jobs})
                elif path.startswith('/api/job/'):
                    self.send(store.snapshot(path.rsplit('/', 1)[-1]))
                elif re.fullmatch(r'/assets/[a-f0-9]{16}/.+', path):
                    _, _, ident, name = path.split('/', 3)
                    file = store.asset(ident, name)
                    self.send(file.read_bytes(), content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
                else:
                    self.send({'error':'没有这个页面。'},404)
            except (KeyError, FileNotFoundError):
                self.send({'error':'找不到任务或文件。'},404)

        def do_POST(self):
            try:
                if self.headers.get('X-WFS-Token') != token:
                    self.send({'error':'页面会话已失效，请刷新。'},403);return
                origin = self.headers.get('Origin')
                if origin and origin != f'http://{self.headers.get("Host")}':
                    self.send({'error':'请求来源不符。'},403);return
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 1024*1024:
                    raise ValueError('配置必须小于 1 MiB。')
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError('请求需要是 JSON 对象。')
                if urlparse(self.path).path == '/api/start':
                    self.send({'id':store.start(data)},202)
                elif urlparse(self.path).path == '/api/cancel':
                    store.cancel(data['id']);self.send({'ok':True})
                elif urlparse(self.path).path == '/api/phase-input':
                    self.send(store.phase_input(data['id']))
                else:
                    self.send({'error':'没有这个操作。'},404)
            except RuntimeError as exc:
                self.send({'error':str(exc)},409)
            except (ValueError, TypeError, KeyError, OSError) as exc:
                self.send({'error':str(exc)},400)
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.store = store
    return server

def serve(workspace='wavefront-runs', port=8790, open_browser=True):
    try:
        server = make_server(workspace, port)
    except OSError as exc:
        raise ValueError(f'无法启动本地工作台：{exc}；端口占用时请用 --port 8791。') from exc
    url = f'http://127.0.0.1:{server.server_port}/'
    print(f'Wavefront UI: {url}\nOutputs: {server.store.workspace}', flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        if server.store.active:
            server.store.cancel(server.store.active)
            # Give the owned child and bookkeeping thread time to finish.
            end = time.monotonic()+5
            while server.store.active and time.monotonic()<end:
                time.sleep(.05)
    finally:
        server.server_close()
