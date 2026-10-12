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

    def test_example_pairs_are_raw_u16_and_can_be_loaded_again(self):
        with tempfile.TemporaryDirectory() as temp:
            a=example(temp,'wsvt','cpp');pairs=a['config']['pairs'];self.assertEqual(len(pairs),100)
            frame=np.load(pairs[0]['reference']);self.assertEqual(frame.dtype,np.uint16);self.assertEqual(frame.shape,(64,64))
            b=example(temp,'wxst','cpp');self.assertEqual(b['config']['sample'],pairs[0]['sample'])
            self.assertEqual(a['config']['backend'],'cpp')

if __name__=='__main__':unittest.main()
