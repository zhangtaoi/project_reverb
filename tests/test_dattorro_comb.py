"""Tests for Dattorro Comb reverb engine."""
import unittest
import numpy as np
from dattorro_comb.reverb import Reverb

SR = 44100


class TestCombImpulseResponse(unittest.TestCase):
    def setUp(self):
        self.rv = Reverb(SR)

    def test_decay_no_nan(self):
        imp = np.zeros(SR // 2); imp[0] = 1.0
        L, R = self.rv.process(imp)
        self.assertFalse(np.isnan(L).any())
        self.assertFalse(np.isnan(R).any())
        self.assertFalse(np.isinf(L).any())

    def test_tail_decays(self):
        imp = np.zeros(SR); imp[0] = 1.0
        L, _ = self.rv.process(imp)
        e1 = np.sum(L[:len(L)//2]**2)
        e2 = np.sum(L[len(L)//2:]**2)
        self.assertGreater(e1, e2 * 2)


class TestCombStability(unittest.TestCase):
    def test_extreme_params(self):
        for decay in (0.01, 0.99):
            for damp in (0.0, 1.0):
                for diffuse in (0.0, 1.0):
                    rv = Reverb(SR, decay=decay, damp=damp, diffuse=diffuse)
                    x = np.sin(2 * np.pi * 440 * np.arange(SR) / SR)
                    L, R = rv.process(x)
                    self.assertFalse(np.isnan(L).any(), f"NaN at decay={decay} damp={damp} diffuse={diffuse}")

    def test_silence(self):
        rv = Reverb(SR)
        x = np.zeros(SR)
        L, R = rv.process(x)
        self.assertAlmostEqual(np.max(np.abs(L)), 0.0)


if __name__ == "__main__":
    unittest.main()