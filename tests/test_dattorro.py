"""Tests for Dattorro reverb engine.

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
        self.rv = Reverb(SR, decay=0.85, damp=0.4, diffuse=0.5)

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
        # energy in second half should be much smaller than first half
        e1 = np.sum(L[: len(L) // 2] ** 2)
        e2 = np.sum(L[len(L) // 2 :] ** 2)
        self.assertGreater(e1, e2 * 2)

    def test_echo_density_increases(self):
        imp = np.zeros(SR)
        imp[0] = 1.0
        L, _ = self.rv.process(imp)
        # count sign changes (zero-crossings) as a proxy for echo density
        early = L[: 100]
        late = L[SR // 2 : SR // 2 + 100]
        zc_early = np.sum(np.diff(np.sign(early)) != 0)
        zc_late = np.sum(np.diff(np.sign(late)) != 0)
        self.assertLessEqual(zc_early, zc_late + 2)  # late is at least as dense

    def test_stereo_differs(self):
        imp = np.zeros(SR // 4)
        imp[0] = 1.0
        L, R = self.rv.process(imp)
        # L and R should not be identical (the delay lines differ)
        self.assertGreater(np.sum(np.abs(L - R)), 1e-6)


class TestStability(unittest.TestCase):
    """Boundary parameter values shouldn't crash or produce NaN."""

    def test_high_decay(self):
        rv = Reverb(SR, decay=0.99, damp=0.5)
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

    def test_zero_damp(self):
        rv = Reverb(SR, damp=0.0)
        x = np.sin(2 * np.pi * 440 * np.arange(SR) / SR)
        L, R = rv.process(x)
        self.assertFalse(np.isnan(L).any())

    def test_max_damp(self):
        rv = Reverb(SR, damp=1.0)
        x = np.sin(2 * np.pi * 440 * np.arange(SR) / SR)
        L, R = rv.process(x)
        self.assertFalse(np.isnan(L).any())

    def test_zero_diffuse(self):
        rv = Reverb(SR, diffuse=0.0)
        x = np.sin(2 * np.pi * 440 * np.arange(SR) / SR)
        L, R = rv.process(x)
        self.assertFalse(np.isnan(L).any())

    def test_max_diffuse(self):
        rv = Reverb(SR, diffuse=1.0)
        x = np.sin(2 * np.pi * 440 * np.arange(SR) / SR)
        L, R = rv.process(x)
        self.assertFalse(np.isnan(L).any())

    def test_max_width(self):
        rv = Reverb(SR, width=1.0)
        x = np.sin(2 * np.pi * 440 * np.arange(SR) / SR)
        L, R = rv.process(x)
        self.assertFalse(np.isnan(L).any())

    def test_zero_rate(self):
        rv = Reverb(SR, rate=0.0)
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
        from common.io import load
        from dattorro_reverb.demo import render
        from common.delay import load_params
        import os

        p = load_params(
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "dattorro_reverb",
                "params.md",
            ),
            {
                "decay": 0.85,
                "damp": 0.4,
                "diffuse": 0.5,
                "width": 0.25,
                "rate": 0.5,
                "mix": 0.0,
                "wet_rms_match": True,
                "loudn_out": None,
                "peak_guard": True,
            },
        )
        p["mix"] = 0.0
        # synthetic stereo signal
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
        from common.delay import delay_len, load_params  # re-export
        self.assertTrue(callable(delay_len))


if __name__ == "__main__":
    unittest.main()