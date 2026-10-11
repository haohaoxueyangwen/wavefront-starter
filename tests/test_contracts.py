"""Input failures and independent analytic controls; CPU only."""
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from wfs_starter.core import corrected, image, speckle, grating, hartmann, zernike_fit, save_results


class Contracts(unittest.TestCase):
    def test_dark_flat_known_value(self):
        a=np.full((8,8),12.); dark=np.full_like(a,2.); flat=np.full_like(a,22.)
        np.testing.assert_allclose(corrected(a,dark,flat),.5)

    def test_invalid_flat_rejected(self):
        a=np.ones((8,8))
        with self.assertRaises(ValueError): corrected(a,a,a)

    def test_color_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'color.npy'; np.save(p,np.zeros((8,8,3)))
            with self.assertRaises(ValueError): image(p)

    def test_nonfinite_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.npy'; np.save(p,np.full((8,8),np.nan))
            with self.assertRaises(ValueError): image(p)

    def test_wsvt_identical_frames_rejected(self):
        frame=np.arange(32*32).reshape(32,32).astype(float)
        stack=np.stack([frame]*8)
        with self.assertRaisesRegex(ValueError,'temporal variation'):
            speckle(stack,stack,{'mode':'wsvt'})

    def test_speckle_rectangular_roi_rejected(self):
        a=np.ones((32,40))
        with self.assertRaisesRegex(ValueError,'square ROI'):
            speckle(a,a,{'mode':'wxst'})

    def test_mismatched_frames_rejected(self):
        with self.assertRaises(ValueError): speckle(np.zeros((3,32,32)),np.zeros((4,32,32)),{'mode':'wsvt'})

    def test_hartmann_empty_cells_rejected(self):
        a=np.zeros((16,16))
        with self.assertRaisesRegex(ValueError,'Empty spot cell'): hartmann(a,a,{'grid_rows':2,'grid_cols':2})

    def test_grating_dc_rejected(self):
        a=np.ones((32,32))
        c=dict(band_x_center_rc=[16,16],band_x_size_rc=[3,3])
        with self.assertRaisesRegex(ValueError,'DC'): grating(a,a,c)

    def test_grating_uncalibrated_stays_fringe_phase(self):
        y,x=np.indices((64,64));a=3+np.cos(2*np.pi*8*x/64)+np.cos(2*np.pi*8*y/64)
        c=dict(band_x_center_rc=[32,40],band_y_center_rc=[40,32],band_x_size_rc=[3,3],band_y_size_rc=[3,3])
        result,_=grating(a,a,c)
        self.assertNotIn('phase_rad',result)
        np.testing.assert_allclose(result['fringe_phase_x_rad'],0,atol=1e-12)

    def test_zernike_independent_piston_and_x_tilt(self):
        y,x=np.indices((64,64));a=.7+.12*2*(x-31.5)/28
        result,_=zernike_fit(a,[31.5,31.5],28,3)
        np.testing.assert_allclose(result['coefficients'],[.7,.12,0],atol=1e-12)

    def test_zernike_nan_outside_pupil_supported_by_api(self):
        y,x=np.indices((64,64));a=np.full((64,64),.3);a[np.hypot(x-31.5,y-31.5)>28]=np.nan
        result,_=zernike_fit(a,[31.5,31.5],28,1)
        self.assertAlmostEqual(result['coefficients'][0],.3)

    def test_results_never_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            save_results(d,{'scalar':np.array([1.])},{'unit':'rad'})
            before=(Path(d)/'results.npz').read_bytes()
            with self.assertRaises(FileExistsError): save_results(d,{'scalar':np.array([2.])},{})
            self.assertEqual(before,(Path(d)/'results.npz').read_bytes())


if __name__=='__main__': unittest.main()
