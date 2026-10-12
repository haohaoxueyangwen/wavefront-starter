from pathlib import Path
import json, tempfile, unittest
from unittest.mock import patch
from wfs_starter.runtime_backends import executable, probe
from wfs_starter.native_examples import example
import numpy as np

class RuntimeBackends(unittest.TestCase):
    def test_relocated_bundle_is_found_without_machine_environment(self):
        with tempfile.TemporaryDirectory(prefix='教学 空格 ') as temp:
            root=Path(temp);path=root/'runtime/native/windows/cpu/wsvt_cli.exe'
            path.parent.mkdir(parents=True);path.write_bytes(b'example')
            with patch('wfs_starter.runtime_backends.ROOT',root),patch.dict('os.environ',{'WFS_CPP_EXE':''}):
                self.assertEqual(Path(executable('cpp')),path)

    def test_no_compatible_gpu_is_reported_unavailable(self):
        probe.cache_clear()
        response=type('Response',(),{'returncode':0,'stdout':json.dumps({'devices':[{'index':0,'name':'Old GPU','available':False}]}),'stderr':''})()
        with patch('wfs_starter.runtime_backends.subprocess.run',return_value=response):
            data=probe('mock.exe',1)
        self.assertFalse(data['available']);self.assertIn('CPU',data['reason'])

    def test_example_uses_real_dataset_pair_order_and_recorded_calibration(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            manifest={'calibration':{'energy_ev':12400,'pixel_size_m':1.625e-6,'distance_m':.4845},'crop_y0_y1_x0_x1':[686,1198,714,1226]}
            with patch('wfs_starter.native_examples.dataset',return_value=(folder,manifest)):
                a=example(temp,'wsvt','cpp');pairs=a['config']['pairs']
                b=example(temp,'wxst','python')
            self.assertEqual(len(pairs),100)
            self.assertEqual(Path(pairs[0]['reference']).name,'reference_001.npy')
            self.assertEqual(Path(pairs[-1]['sample']).name,'sample_100.npy')
            self.assertEqual(b['config']['sample'],pairs[0]['sample'])
            self.assertEqual(a['config']['energy_ev'],12400)
            self.assertEqual(a['config']['example_crop_y0_y1_x0_x1'],[686,1198,714,1226])
            self.assertIn('BB11',a['config']['metadata_note'])
            self.assertEqual(b['config']['backend'],'python')

    def test_invalid_crl_cache_never_generates_random_replacement(self):
        from wfs_starter.native_examples import dataset
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=root/'example-data/crl-bb11-v1';folder.mkdir(parents=True)
            (folder/'manifest.json').write_text('{"dataset_id":"other-data"}')
            with patch('wfs_starter.native_examples.ROOT',root),patch('wfs_starter.native_examples.urllib.request.urlopen') as download:
                with self.assertRaises(ValueError):dataset(root/'workspace')
                download.assert_not_called()
            self.assertEqual(len(list(folder.iterdir())),1)

    def test_crl_pixel_changes_are_detected(self):
        from wfs_starter.native_examples import verify,DATASET_ID
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);files=[{'file':f'{role}_{i:03}.npy','sha256':'0'*64} for role in ('reference','sample') for i in range(1,101)]
            manifest={'dataset_id':DATASET_ID,'frames':100,'shape_yx':[512,512],'files':files}
            (root/'manifest.json').write_text(json.dumps(manifest))
            (root/files[0]['file']).write_bytes(b'changed pixels')
            with self.assertRaisesRegex(ValueError,'reference_001'):verify(root)

if __name__=='__main__':unittest.main()
