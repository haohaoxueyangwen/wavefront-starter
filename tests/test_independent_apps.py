from pathlib import Path
import json
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.request
import numpy as np
from wfs_starter.local_files import browse,paired_directories,preview
from wfs_starter.speckle_backends import cpp_arguments,validate_backend
from wfs_starter.ui import make_server

class IndependentApps(unittest.TestCase):
    def test_original_speckle_controls_reach_reference_solver(self):
        from wfs_starter.core import speckle
        seen={}
        class Solver:
            def __init__(self,sample,reference,**kwargs):seen.update(kwargs)
            def run(self,result_path=None):return {k:np.zeros((24,24)) for k in ('displace_x','displace_y','DPC_x','DPC_y','phase')}
        config=dict(mode='wxst',energy_ev=12400,pixel_size_m=1e-6,distance_m=.5,
                    n_cores=3,n_group=2,n_iter=2,pyramid_level=1,wavelet_level_cut=1,
                    extended_half_window=4,search_half_window=3,template_half_window=2,use_wavelet=False)
        rng=np.random.default_rng(3);a=rng.random((32,32))
        with patch('wfs_starter.vendor.speckle.WXST.WXST',Solver):speckle(a,a,config)
        self.assertEqual({k:seen[k] for k in ('n_cores','n_group','n_iter','pyramid_level','wavelet_level_cut','N_s_extend','use_wavelet')},
                         dict(n_cores=3,n_group=2,n_iter=2,pyramid_level=1,wavelet_level_cut=1,N_s_extend=4,use_wavelet=False))

    def test_cpp_bridge_forces_cpu_and_preserves_parameters(self):
        config=dict(mode='wsvt',energy_ev=12400,pixel_size_m=1e-6,distance_m=.5,n_cores=8,phase_cores=4,pyramid_level=1)
        args=cpp_arguments('cli','input.h5','output',config)
        opts=dict(zip(args[7::2],args[8::2]))
        self.assertEqual(opts['--use_gpu'],'false')
        self.assertEqual(opts['--n_cores'],'8');self.assertEqual(opts['--phase_cores'],'4')
        self.assertEqual(opts['--pyramid_level'],'1')

    def test_native_unavailable_never_falls_back(self):
        with self.assertRaisesRegex(ValueError,r'C\+\+ CPU'):
            validate_backend({'mode':'wxst','backend':'cpp','cpp_executable':'/not-a-file'})
        with self.assertRaisesRegex(ValueError,'固定 search_half_window'):
            validate_backend({'mode':'wxst','backend':'gpu','search_half_window':3})
        fixed=dict(mode='wsvt',backend='gpu',search_half_window=10,extended_half_window=4,pyramid_level=1,wavelet_level_cut=1,n_iter=1,use_wavelet=True,gpu_front='reordered')
        with self.assertRaisesRegex(ValueError,'重排'):validate_backend(fixed)

    def test_file_picker_and_natural_pair_order_without_data_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for role in ('reference','sample'):
                (root/role).mkdir()
                for frame in (10,2,1):np.save(root/role/f'frame{frame}.npy',np.ones((8,8))*frame)
            before={str(p):p.read_bytes() for p in root.rglob('*.npy')}
            result=paired_directories(root/'reference',root/'sample')
            self.assertEqual([Path(p['reference']).name for p in result['pairs']],['frame1.npy','frame2.npy','frame10.npy'])
            listed=browse('reference','file',root)
            self.assertEqual(len(listed['entries']),3)
            image=preview('reference/frame1.npy',root,True)
            self.assertEqual(image['shape_rc'],[8,8]);self.assertTrue(image['image'].startswith('data:image/png'))
            self.assertEqual(before,{str(p):p.read_bytes() for p in root.rglob('*.npy')})
            (root/'sample'/'frame10.npy').unlink()
            with self.assertRaisesRegex(ValueError,'相同数量'):paired_directories(root/'reference',root/'sample')

    def test_four_distinct_pages_and_launch_home(self):
        with tempfile.TemporaryDirectory() as temp:
            server=make_server(temp,0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            url=f'http://127.0.0.1:{server.server_port}'
            try:
                home=urllib.request.urlopen(url).read().decode()
                self.assertIn('四个独立前端',home);self.assertNotIn('id="run"',home)
                for app in ('speckle','grating','hartmann','wavefront'):
                    page=urllib.request.urlopen(url+'/'+app).read().decode()
                    self.assertIn(f'data-app="{app}"',page)
                    self.assertNotIn('data-group=',page)
                    self.assertIn('id="picker"',page)
            finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main()
