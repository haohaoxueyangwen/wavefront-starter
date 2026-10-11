from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from wfs_starter.native_gpu import arguments, input_arrays, policies, NAMES
from wfs_starter.speckle_backends import native_speckle, cpp_arguments
from wfs_starter.ui import prepare_config
from wfs_starter.local_files import browse

def config(mode='wsvt'):
    return dict(mode=mode,backend='gpu',energy_ev=12400,pixel_size_m=1e-6,distance_m=.5,
                search_half_window=10,template_half_window=3,extended_half_window=4,
                pyramid_level=1,wavelet_level_cut=1,n_iter=1,use_wavelet=True,
                gpu_platform='desktop',gpu_workspace='speed',gpu_input_policy='auto')

class NativeBridge(unittest.TestCase):
    def test_host_defaults_and_invalid_memory_policies(self):
        c=config();self.assertEqual(policies(c),('desktop','speed','copy',16))
        c['gpu_platform']='jetson';self.assertEqual(policies(c)[2],'mapped')
        c['mode']='wxst';self.assertEqual(policies(c)[2],'copy')
        c['gpu_workspace']='low-memory'
        with self.assertRaises(ValueError):policies(c)
        with self.assertRaises(ValueError):policies(dict(config(),gpu_input_policy='mapped'))

    def test_dtype_preservation_and_no_lossy_uint16_conversion(self):
        a=np.arange(100*32*32,dtype=np.uint16).reshape(100,32,32)
        s,r=input_arrays(a,a,config());self.assertEqual(s.dtype,np.uint16);np.testing.assert_array_equal(s,a)
        with self.assertRaisesRegex(ValueError,'不量化'):
            input_arrays(a.astype(float),a.astype(float),dict(config(),gpu_input_dtype='uint16'))
        with self.assertRaisesRegex(ValueError,'100'):
            input_arrays(a[:32],a[:32],config())

    def test_cli_execution_and_seven_output_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            exe=Path(temp)/'speckle_gpu';exe.write_bytes(b'mock-binary-for-contract-test')
            c=dict(config(),gpu_executable=str(exe))
            a=np.arange(100*32*32,dtype=np.uint16).reshape(100,32,32)
            def run(args,**kwargs):
                opt=dict(zip(args[1::2],args[2::2]))
                self.assertEqual(opt['--workspace'],'speed');self.assertEqual(opt['--input-policy'],'copy')
                self.assertEqual(opt['--warmup'],'0');self.assertEqual(opt['--repeats'],'1')
                self.assertEqual(opt['--reference-policy'],'each-pair')
                np.testing.assert_array_equal(np.load(opt['--sample']),a)
                folder=Path(opt['--out']);folder.mkdir()
                for n in NAMES:np.save(folder/(n+'.npy'),np.zeros((32,32) if n=='transmission' else (12,12),np.float32))
                (folder/'timing.csv').write_text('repeat,solver_s,api_s\n0,0.1,0.2\n')
                (folder/'report.json').write_text(json.dumps(dict(implementation='native C++/CUDA/cuFFT',mode='wsvt',height=32,width=32,frames=100,reference_policy='each-pair',warmup=0,repeats=1)))
            with patch('wfs_starter.native_gpu.subprocess.run',side_effect=run):fields,meta=native_speckle(a,a,c)
            self.assertEqual(len(fields),7);self.assertEqual(fields['ux_px'].shape,(12,12))
            self.assertEqual(fields['transmission'].shape,(32,32));self.assertEqual(meta['input_dtype'],'uint16')
            self.assertEqual(meta['backend'],'native_cpp_cuda_cufft')

    def test_native_missing_does_not_use_legacy_or_cpu(self):
        from wfs_starter.native_gpu import solve
        with patch.dict('os.environ',{'WFS_GPU_EXE':''}):
            with self.assertRaisesRegex(ValueError,'speckle_gpu'):solve(np.zeros((32,32)),np.zeros((32,32)),config('wxst'))

    def test_native_picker_and_relative_executable_resolution(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'speckle_gpu').write_bytes(b'mock');np.save(root/'a.npy',np.ones((32,32)))
            c=dict(config('wxst'),sample='a.npy',reference='a.npy',gpu_executable='speckle_gpu')
            checked=prepare_config(c,root)
            self.assertEqual(checked['gpu_executable'],str(root/'speckle_gpu'))
            self.assertIn('speckle_gpu',[e['name'] for e in browse('',base=root)['entries']])

    def test_cpu_wsvt_does_not_silently_crop_512_or_enable_darkfield(self):
        c=dict(config(),backend='cpp')
        args=cpp_arguments('exe','inputs.h5','output',c);opts=dict(zip(args[7::2],args[8::2]))
        self.assertEqual(opts['--crop'],'0');self.assertEqual(opts['--n_template'],'0')
        self.assertEqual(opts['--calc_darkfield'],'false');self.assertNotIn('--m_image',opts)

if __name__=='__main__':unittest.main()
