"""Tests for common/ delay utilities."""
import os
import tempfile
import unittest

import numpy as np

from common.delay import delay_len, load_params, load_presets


class TestDelayLen(unittest.TestCase):
    def test_identity_at_44100(self):
        self.assertEqual(delay_len(44100, 100), 100)

    def test_scaling(self):
        self.assertEqual(delay_len(48000, 100), int(round(48000 / 44100 * 100)))

    def test_minimum(self):
        self.assertEqual(delay_len(1, 0), 1)

    def test_rounding(self):
        self.assertEqual(delay_len(44100, 1), 1)


class TestLoadParams(unittest.TestCase):
    def setUp(self):
        fd, self.yaml = tempfile.mkstemp(suffix=".yaml", dir=os.path.dirname(__file__))
        os.close(fd)

    def tearDown(self):
        if os.path.exists(self.yaml):
            os.unlink(self.yaml)

    def _write(self, text):
        with open(self.yaml, "w", encoding="utf-8") as f:
            f.write(text)

    def test_float(self):
        self._write("decay: 0.85\n")
        p = load_params(self.yaml)
        self.assertAlmostEqual(p["decay"], 0.85)

    def test_bool(self):
        self._write("flag: true\n")
        p = load_params(self.yaml)
        self.assertIs(p["flag"], True)

    def test_bool_false(self):
        self._write("flag: false\n")
        p = load_params(self.yaml)
        self.assertIs(p["flag"], False)

    def test_none(self):
        self._write("x: null\n")
        p = load_params(self.yaml)
        self.assertIsNone(p["x"])

    def test_int(self):
        self._write("n: 5\n")
        p = load_params(self.yaml)
        self.assertEqual(p["n"], 5)

    def test_missing_file(self):
        p = load_params("nonexistent.yaml")
        self.assertEqual(p, {})

    def test_default_fallback(self):
        p = load_params("nonexistent.yaml", {"decay": 0.5})
        self.assertEqual(p["decay"], 0.5)

    def test_skips_presets(self):
        self._write("decay: 0.75\npresets:\n  plate:\n    decay: 0.5\n")
        p = load_params(self.yaml)
        self.assertEqual(p["decay"], 0.75)
        self.assertNotIn("presets", p)

    def test_comments(self):
        self._write("decay: 0.75  # reverb tail\n")
        p = load_params(self.yaml)
        self.assertAlmostEqual(p["decay"], 0.75)


class TestLoadPresets(unittest.TestCase):
    def setUp(self):
        fd, self.yaml = tempfile.mkstemp(suffix=".yaml", dir=os.path.dirname(__file__))
        os.close(fd)

    def tearDown(self):
        if os.path.exists(self.yaml):
            os.unlink(self.yaml)

    def _write(self, text):
        with open(self.yaml, "w", encoding="utf-8") as f:
            f.write(text)

    def test_presets(self):
        self._write("presets:\n  plate:\n    decay: 0.5\n    damping: 0.7\n")
        presets = load_presets(self.yaml)
        self.assertIn("plate", presets)
        self.assertAlmostEqual(presets["plate"]["decay"], 0.5)
        self.assertAlmostEqual(presets["plate"]["damping"], 0.7)

    def test_no_presets(self):
        self._write("decay: 0.75\n")
        presets = load_presets(self.yaml)
        self.assertEqual(presets, {})

    def test_missing_file(self):
        presets = load_presets("nonexistent.yaml")
        self.assertEqual(presets, {})


if __name__ == "__main__":
    unittest.main()