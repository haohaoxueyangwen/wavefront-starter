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
            self.assertEqual(len(session['templates']),7)
            for asset,content_type in [('/app.js','text/javascript'),('/style.css','text/css')]:
                with urllib.request.urlopen(url+asset) as response:
                    self.assertIn(content_type,response.headers['Content-Type'])
                    self.assertGreater(len(response.read()),100)
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

    def test_phase_handoff_preserves_values_units_and_source(self):
        import numpy as np
        store=JobStore(self.root)
        folder=self.root/'aabbccddeeff0011'
        (folder/'results').mkdir(parents=True)
        phase=np.arange(64,dtype=float).reshape(8,8)/64
        source=folder/'results/results.npz'
        np.savez(source,phase_rad=phase,fringe_phase_x_rad=phase*2)
        before=hashlib.sha256(source.read_bytes()).hexdigest()
        store.jobs[folder.name]={'id':folder.name,'mode':'grating','action':'run','status':'succeeded','output_dir':str(folder)}
        handoff=store.phase_input(folder.name)
        c=handoff['config']
        self.assertTrue(np.array_equal(np.load(c['phase'],allow_pickle=False),phase))
        self.assertEqual(c['phase_unit'],'rad')
        self.assertIsNone(c['center_xy_px'])
        self.assertIsNone(c['radius_px'])
        self.assertEqual(c['phase_source']['source_job'],folder.name)
        self.assertEqual(handoff['shape_rc'],[8,8])
        self.assertEqual(before,hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertEqual(store.phase_input(folder.name),handoff)

    def test_fringe_phase_and_incomplete_job_cannot_enter_zernike(self):
        import numpy as np
        store=JobStore(self.root)
        folder=self.root/'aabbccddeeff0011'
        (folder/'results').mkdir(parents=True)
        np.savez(folder/'results/results.npz',fringe_phase_x_rad=np.ones((8,8)))
        job={'id':folder.name,'mode':'grating','action':'run','status':'succeeded','output_dir':str(folder)}
        store.jobs[folder.name]=job
        with self.assertRaisesRegex(ValueError,'条纹相位'):store.phase_input(folder.name)
        np.savez(folder/'results/results.npz',phase_rad=np.ones((8,8)))
        job['status']='cancelled'
        with self.assertRaises(ValueError):store.phase_input(folder.name)

    def test_phase_handoff_rejects_nonfinite_and_protects_existing_file(self):
        import numpy as np
        store=JobStore(self.root)
        folder=self.root/'aabbccddeeff0011'
        (folder/'results').mkdir(parents=True)
        source=folder/'results/results.npz'
        store.jobs[folder.name]={'id':folder.name,'mode':'wxst','action':'run','status':'succeeded','output_dir':str(folder)}
        np.savez(source,phase_rad=np.full((8,8),np.nan))
        with self.assertRaisesRegex(ValueError,'有限实数'):store.phase_input(folder.name)
        np.savez(source,phase_rad=np.ones((8,8)))
        handoff=store.phase_input(folder.name)
        np.save(handoff['config']['phase'],np.zeros((8,8)))
        with self.assertRaisesRegex(ValueError,'不同'):store.phase_input(folder.name)

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
