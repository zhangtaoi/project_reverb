"""Tests for common/ delay utilities."""
import os
import tempfile
import unittest

import numpy as np

from common.delay import delay_len, load_params


class TestDelayLen(unittest.TestCase):
    def test_identity_at_44100(self):
        self.assertEqual(delay_len(44100, 100), 100)

    def test_scaling(self):
        self.assertEqual(delay_len(48000, 100), int(round(48000 / 44100 * 100)))

    def test_minimum(self):
        self.assertEqual(delay_len(1, 0), 1)

    def test_rounding(self):
        self.assertEqual(delay_len(44100, 1), 1)  # small stays correct


class TestLoadParams(unittest.TestCase):
    def setUp(self):
        fd, self.md = tempfile.mkstemp(suffix=".md", dir=os.path.dirname(__file__))
        os.close(fd)

    def tearDown(self):
        if os.path.exists(self.md):
            os.unlink(self.md)

    def _write(self, text):
        with open(self.md, "w", encoding="utf-8") as f:
            f.write(text)

    def test_bool(self):
        self._write("| name | range | default | meaning |\n|---|---|---|---|\n| flag | 0-1 | true | debug |\n")
        p = load_params(self.md)
        self.assertIs(p["flag"], True)

    def test_bool_false(self):
        self._write("| name | range | default | meaning |\n|---|---|---|---|\n| flag | 0-1 | false | debug |\n")
        p = load_params(self.md)
        self.assertIs(p["flag"], False)

    def test_none(self):
        self._write("| name | range | default | meaning |\n|---|---|---|---|\n| x | 0-1 | none | quiet |\n")
        p = load_params(self.md)
        self.assertIsNone(p["x"])

    def test_float(self):
        self._write("| name | range | default | meaning |\n|---|---|---|---|\n| decay | 0-1 | 0.85 | fb |\n")
        p = load_params(self.md)
        self.assertAlmostEqual(p["decay"], 0.85)

    def test_int_becomes_float(self):
        self._write("| name | range | default | meaning |\n|---|---|---|---|\n| n | 0-10 | 5 | count |\n")
        p = load_params(self.md)
        self.assertAlmostEqual(p["n"], 5.0)

    def test_missing_file(self):
        p = load_params("nonexistent.md")
        self.assertEqual(p, {})

    def test_default_fallback(self):
        p = load_params("nonexistent.md", {"decay": 0.5})
        self.assertEqual(p["decay"], 0.5)

    def test_skips_header_row(self):
        self._write("| name | range | default | meaning |\n|---|---|---|---|\n| x | 0-1 | 0.3 | val |\n")
        p = load_params(self.md)
        self.assertEqual(len(p), 1)

    def test_skips_separator_and_header(self):
        self._write("| name | range | default | meaning |\n|---|---|---|---|\n| name2 | 0-1 | 0.3 | note |\n|---|---|---|---|\n| y | 0-1 | 0.5 | v |\n")
        p = load_params(self.md)
        # name2 starts with "name" → skipped together with separator → only y remains
        self.assertEqual(len(p), 1)
        self.assertAlmostEqual(p["y"], 0.5)


if __name__ == "__main__":
    unittest.main()