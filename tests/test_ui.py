import json
import hashlib
from pathlib import Path
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from wfs_starter.ui import JobStore, make_server, prepare_config

class UITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_paths_resolve_from_declared_base(self):
        (self.root/'phase.npy').write_bytes(b'fixture')
        c=prepare_config({'mode':'zernike','phase':'phase.npy','phase_unit':'rad'},self.root)
        self.assertEqual(c['phase'],str(self.root/'phase.npy'))

    def test_missing_calibration_is_reported_before_job(self):
        with self.assertRaisesRegex(ValueError,'energy_ev'):
            prepare_config({'mode':'wxst','energy_ev':None},self.root)
        with self.assertRaises(ValueError):
            prepare_config({'mode':'wxst','energy_ev':float('nan')},self.root)

    def test_http_session_and_write_access(self):
        server=make_server(self.root,0)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        url=f'http://127.0.0.1:{server.server_port}'
        try:
            session=json.load(urllib.request.urlopen(url+'/api/session'))
            self.assertEqual(len(session['templates']),5)
            req=urllib.request.Request(url+'/api/start',data=b'{"action":"demo","mode":"grating"}',headers={'Content-Type':'application/json'})
            with self.assertRaises(urllib.error.HTTPError) as caught:urllib.request.urlopen(req)
            self.assertEqual(caught.exception.code,403)
            req=urllib.request.Request(url+'/api/start',data=b'[]',headers={'Content-Type':'application/json','X-WFS-Token':session['token']})
            with self.assertRaises(urllib.error.HTTPError) as caught:urllib.request.urlopen(req)
            self.assertEqual(caught.exception.code,400)
        finally:
            server.shutdown();server.server_close();thread.join()

    def test_grating_job_real_cli_and_history(self):
        store=JobStore(self.root)
        ident=store.start({'action':'demo','mode':'grating'})
        with self.assertRaises(RuntimeError):store.start({'action':'demo','mode':'hartmann'})
        end=time.monotonic()+30
        while store.active and time.monotonic()<end:time.sleep(.05)
        snapshot=store.snapshot(ident)
        self.assertEqual(snapshot['status'],'succeeded',snapshot['log'])
        self.assertTrue(any(f.endswith('phase_rad.png') for f in snapshot['files']))
        with self.assertRaises(FileNotFoundError):store.asset(ident,'../outside.json')
        self.assertIn(ident,JobStore(self.root).jobs)

    def test_cancel_owned_job_leaves_receipt(self):
        store=JobStore(self.root)
        ident=store.start({'action':'demo','mode':'wsvt'})
        store.cancel(ident)
        end=time.monotonic()+10
        while store.active and time.monotonic()<end:time.sleep(.05)
        self.assertEqual(store.snapshot(ident)['status'],'cancelled')
        self.assertTrue((self.root/ident/'job.json').exists())

    def test_zernike_plots_do_not_change_numerical_results(self):
        import numpy as np
        from wfs_starter.ui_plots import add_previews
        file=self.root/'results.npz'
        np.savez(file,fit=np.ones((8,8)),residual=np.zeros((8,8)),coefficients=np.array([1.]))
        (self.root/'metadata.json').write_text(json.dumps({'coefficient_unit':'m','modes_nm':[[0,0]]}))
        before=hashlib.sha256(file.read_bytes()).hexdigest()
        add_previews(self.root)
        self.assertEqual(before,hashlib.sha256(file.read_bytes()).hexdigest())
        self.assertTrue((self.root/'coefficients.png').exists())

if __name__=='__main__':unittest.main()
