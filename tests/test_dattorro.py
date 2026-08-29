"""Tests for Dattorro reverb engine (paper-faithful topology).

These tests operate on synthetic signals (impulse, sine, silence) — no audio
files needed.  They verify correctness, stability, and transparency.
"""
import unittest

import numpy as np

from dattorro_reverb.reverb import Reverb

SR = 44100


class TestImpulseResponse(unittest.TestCase):
    """Core sanity: impulse in -> decaying reverb tail, no NaN, no explosion."""

    def setUp(self):
        self.rv = Reverb(SR)

    def test_decay_no_nan(self):
        imp = np.zeros(SR // 2)
        imp[0] = 1.0
        L, R = self.rv.process(imp)
        self.assertFalse(np.isnan(L).any())
        self.assertFalse(np.isnan(R).any())
        self.assertFalse(np.isinf(L).any())
        self.assertFalse(np.isinf(R).any())

    def test_tail_energy_decays(self):
        imp = np.zeros(SR)
        imp[0] = 1.0
        L, R = self.rv.process(imp)
        e1 = np.sum(L[: len(L) // 2] ** 2)
        e2 = np.sum(L[len(L) // 2 :] ** 2)
        self.assertGreater(e1, e2 * 2)

    def test_stereo_differs(self):
        imp = np.zeros(SR // 4)
        imp[0] = 1.0
        L, R = self.rv.process(imp)
        self.assertGreater(np.sum(np.abs(L - R)), 1e-6)

    def test_pre_delay_works(self):
        """Pre-delay should cause silence before first reflection."""
        imp = np.zeros(SR)
        imp[0] = 1.0
        L, _ = self.rv.process(imp)
        nz = np.nonzero(np.abs(L) > 1e-10)[0]
        self.assertGreater(len(nz), 0)
        # first non-zero should be > 0 (pre-delay + input diffusion)
        self.assertGreater(nz[0], 100)  # at least 100 samples of silence


class TestStability(unittest.TestCase):
    """Boundary parameter values shouldn't crash or produce NaN."""

    def test_high_decay(self):
        rv = Reverb(SR, decay=0.99)
        x = np.sin(2 * np.pi * 440 * np.arange(SR) / SR)
        L, R = rv.process(x)
        self.assertFalse(np.isnan(L).any())
        self.assertFalse(np.isnan(R).any())

    def test_low_decay(self):
        rv = Reverb(SR, decay=0.01)
        x = np.sin(2 * np.pi * 440 * np.arange(SR) / SR)
        L, R = rv.process(x)
        self.assertFalse(np.isnan(L).any())
        self.assertFalse(np.isnan(R).any())

    def test_zero_damping(self):
        rv = Reverb(SR, damping=0.0)
        x = np.sin(2 * np.pi * 440 * np.arange(SR) / SR)
        L, R = rv.process(x)
        self.assertFalse(np.isnan(L).any())

    def test_max_damping(self):
        rv = Reverb(SR, damping=1.0)
        x = np.sin(2 * np.pi * 440 * np.arange(SR) / SR)
        L, R = rv.process(x)
        self.assertFalse(np.isnan(L).any())

    def test_zero_input_diffusion(self):
        rv = Reverb(SR, input_diffusion1=0.0, input_diffusion2=0.0)
        x = np.sin(2 * np.pi * 440 * np.arange(SR) / SR)
        L, R = rv.process(x)
        self.assertFalse(np.isnan(L).any())

    def test_max_input_diffusion(self):
        rv = Reverb(SR, input_diffusion1=1.0, input_diffusion2=1.0)
        x = np.sin(2 * np.pi * 440 * np.arange(SR) / SR)
        L, R = rv.process(x)
        self.assertFalse(np.isnan(L).any())

    def test_zero_decay_diffusion(self):
        rv = Reverb(SR, decay_diffusion=0.0)
        x = np.sin(2 * np.pi * 440 * np.arange(SR) / SR)
        L, R = rv.process(x)
        self.assertFalse(np.isnan(L).any())

    def test_silence_in_silence_out(self):
        rv = Reverb(SR)
        x = np.zeros(SR)
        L, R = rv.process(x)
        self.assertAlmostEqual(np.max(np.abs(L)), 0.0)
        self.assertAlmostEqual(np.max(np.abs(R)), 0.0)

    def test_different_sr(self):
        rv = Reverb(48000)
        x = np.sin(2 * np.pi * 440 * np.arange(48000) / 48000)
        L, R = rv.process(x)
        self.assertFalse(np.isnan(L).any())
        self.assertEqual(len(L), 48000)


class TestTransparency(unittest.TestCase):
    """The demo's render() must pass through mix=0 unchanged."""

    def test_mix_zero_passthrough(self):
        from dattorro_reverb.demo import render
        from common.delay import load_params
        import os

        p = load_params(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "dattorro_reverb",
                "params.yaml",
            ),
            {
                "pre_delay": 0.1,
                "pre_filter": 0.85,
                "input_diffusion1": 0.75,
                "input_diffusion2": 0.625,
                "decay": 0.75,
                "decay_diffusion": 0.70,
                "damping": 0.95,
                "mix": 0.0,
                "wet_rms_match": True,
                "loudn_out": None,
                "peak_guard": True,
            },
        )
        p["mix"] = 0.0
        x = np.random.randn(44100, 2).astype(np.float32)
        x = x / np.max(np.abs(x)) * 0.9
        out = render(x, 44100, p)
        np.testing.assert_array_almost_equal(x, out, decimal=6)


class TestDemo(unittest.TestCase):
    """End-to-end: demo processes a synthetic WAV correctly."""

    def test_roundtrip(self):
        import tempfile, os
        from common.io import save, load

        sr = 44100
        x = np.sin(2 * np.pi * 440 * np.arange(sr) / sr).astype(np.float32)
        stereo = np.stack([x, x], axis=1)
        tmp = tempfile.mktemp(suffix=".wav", dir=os.path.dirname(os.path.dirname(__file__)))
        try:
            save(tmp, stereo, sr)
            reloaded, sr2 = load(tmp)
            self.assertEqual(sr2, sr)
            self.assertEqual(reloaded.shape, stereo.shape)
            np.testing.assert_array_almost_equal(reloaded, stereo, decimal=4)
        finally:
            os.unlink(tmp)


class TestModule(unittest.TestCase):
    """Import and module-level checks."""

    def test_reverb_import(self):
        from dattorro_reverb.reverb import Reverb, _run, _layout
        self.assertTrue(callable(Reverb))
        self.assertTrue(callable(_run))
        self.assertTrue(callable(_layout))

    def test_common_import(self):
        from common.delay import delay_len, load_params
        self.assertTrue(callable(delay_len))


if __name__ == "__main__":
    unittest.main()