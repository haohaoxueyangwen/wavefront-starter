from pathlib import Path
import hashlib
import json
import tempfile
import time
import unittest
from unittest.mock import patch

import numpy as np
from wfs_starter.advanced_zernike import noll_to_nm,wavelength_um,run_full,run_name
from wfs_starter.config_templates import load_templates
from wfs_starter.local_files import preview
from wfs_starter.ui import JobStore

def control():
    y,x=np.indices((64,64));X=(x-31.5)/28;Y=(y-31.5)/28;r2=X*X+Y*Y
    # Independent Cartesian formulas, not the fitted implementation.
    coma=.07*np.sqrt(8)*(3*r2-2)*Y
    spherical=.05*np.sqrt(5)*(6*r2*r2-6*r2+1)
    phase=2+.12*2*X+.08*2*Y+.3*np.sqrt(3)*(2*r2-1)+.04*np.sqrt(6)*(X*X-Y*Y)+coma+spherical
    phase[r2>1]=np.nan
    return phase,coma+spherical,r2<=1

class AdvancedZernike(unittest.TestCase):
    def test_noll_reference_and_valid_unique_modes_through_50(self):
        expected=[(0,0),(1,1),(1,-1),(2,0),(2,-2),(2,2),(3,-1),(3,1),(3,-3),(3,3),(4,0),(4,2),(4,-2),(4,4),(4,-4)]
        self.assertEqual([noll_to_nm(j) for j in range(1,16)],expected)
        modes=[noll_to_nm(j) for j in range(1,51)]
        self.assertEqual(len(set(modes)),50)
        self.assertTrue(all(abs(m)<=n and (n-abs(m))%2==0 for n,m in modes))

    def test_energy_units_and_invalid_parameters(self):
        self.assertAlmostEqual(wavelength_um(15),.0000826561322888,places=15)
        for value in (0,-1,float('nan'),101):
            with self.assertRaises(ValueError):wavelength_um(value)
        for value in ('../bad','CON','a/b','foo:bar'):
            with self.assertRaises(ValueError):run_name(value)

    def test_complete_cli_resolves_paths_relative_to_config(self):
        from wfs_starter.cli import run_config
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config=load_templates()['zernike_full'];config.update(phase='phase_rad.npy',center_xy_px=[10,10],radius_px=8)
            path=root/'config.json';path.write_text(json.dumps(config))
            with patch('wfs_starter.advanced_zernike.run_full') as worker:
                run_config(path,root/'results')
            self.assertEqual(worker.call_args.args[0]['phase'],str(root/'phase_rad.npy'))

    def test_complete_original_worker_50_terms_and_radial_order_subtraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);phase,high,mask=control();p=root/'phase.npy';np.save(p,phase)
            before=hashlib.sha256(p.read_bytes()).hexdigest()
            config=load_templates()['zernike_full'];config.update(phase=str(p),center_xy_px=[31.5,31.5],radius_px=28,terms=50,export_tiff=False,run_name='control')
            # Exercise original plotting code, but avoid large rendered files in unit tests.
            with patch('matplotlib.figure.Figure.savefig',lambda self,path,*a,**k:Path(path).write_bytes(b'test-figure')):
                run_full(config,root/'results')
            expected=np.zeros(50);expected[[0,1,2,3,5,6,10]]=[2,.12,.08,.3,.04,.07,.05]
            with np.load(root/'results/results.npz') as r:
                np.testing.assert_allclose(r['coefficients_rad'],expected,atol=2e-8)
                np.testing.assert_allclose(r['higher_order_phase_rad'][mask],high[mask],atol=2e-8)
                np.testing.assert_allclose(r['fitting_residual_rad'][mask],0,atol=2e-8)
                self.assertTrue(np.isnan(r['fitted_phase_rad'][~mask]).all())
            result=json.loads((root/'results/summary.json').read_text())
            self.assertEqual(len(result['coefficients']),50)
            self.assertAlmostEqual(result['rms_higher_order_rad'],np.std(high[mask]),places=8)
            expected_roc=np.pi*(28*.65e-6)**2/(wavelength_um(15)*1e-6*2*np.sqrt(3)*.3)*1000
            self.assertAlmostEqual(result['roc_mean_mm'],expected_roc,places=7)
            self.assertEqual(before,hashlib.sha256(p.read_bytes()).hexdigest())
            with self.assertRaises(FileExistsError):run_full(config,root/'results')

    def test_five_terms_maximum_removal_and_plane_infinite_curvature(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);y,x=np.indices((32,32));phase=.7+.12*2*(x-15.5)/14;np.save(root/'p.npy',phase)
            config=load_templates()['zernike_full'];config.update(phase=str(root/'p.npy'),center_xy_px=[15.5,15.5],radius_px=14,terms=5,max_order_remove=10,export_tiff=False)
            with patch('matplotlib.figure.Figure.savefig',lambda self,path,*a,**k:Path(path).write_bytes(b'test-figure')):run_full(config,root/'results')
            result=json.loads((root/'results/summary.json').read_text())
            self.assertLess(result['rms_higher_order_rad'],1e-8)
            self.assertEqual(result['roc_mean_mm'],'Infinity')

    def test_masked_preview_and_invalid_pupil_fail_without_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);phase,_,_=control();np.save(root/'p.npy',phase)
            result=preview('p.npy',root,allow_masked=True)
            self.assertLess(result['stats']['finite_points'],result['stats']['total_points'])
            config=load_templates()['zernike_full'];config.update(phase=str(root/'p.npy'),center_xy_px=[31.5,31.5],radius_px=35)
            with self.assertRaisesRegex(ValueError,'有限相位'):run_full(config,root/'results')
            self.assertFalse((root/'results').exists())

    def test_selected_output_folder_and_restored_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);out=root/'selected';out.mkdir();np.save(root/'p.npy',np.ones((16,16)))
            config=load_templates()['zernike_full'];config.update(phase='p.npy',center_xy_px=[8,8],radius_px=6,output_root=str(out),run_name='chosen')
            store=JobStore(root/'history')
            with patch.object(store,'_run',lambda job:None):
                ident=store.start(dict(action='run',mode='zernike_full',config=config,base_dir=str(root)))
            job=store.jobs[ident];folder=Path(job['output_dir']);self.assertEqual(folder.parent,out)
            job.update(status='succeeded',finished=time.time());(root/'history'/ident/'job.json').write_text(json.dumps(store.snapshot(ident)))
            self.assertEqual(JobStore(root/'history').jobs[ident]['output_dir'],str(folder))

    def test_original_worker_failure_is_not_reported_as_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);phase,_,_=control();np.save(root/'p.npy',phase)
            config=load_templates()['zernike_full'];config.update(phase=str(root/'p.npy'),center_xy_px=[31.5,31.5],radius_px=28,export_tiff=False)
            with patch('scipy.optimize.least_squares',side_effect=RuntimeError('fitting failed')):
                with self.assertRaisesRegex(ValueError,'fitting failed'):run_full(config,root/'results')
            self.assertFalse((root/'results/summary.json').exists())
