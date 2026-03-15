"""Tests for multi-trust CLI and compute_schedule_g cap fix.

TDD RED phase: These tests verify:
1. --trust flag is required (omitting exits with error)
2. --trust trent loads config/2025_trent.json
3. --trust chris loads config/2025_chris.json
4. compute_schedule_g with Chris's numbers produces tax=$779.35 (not $824.41)
5. compute_schedule_g with Trent's numbers is unchanged (regression)
"""

import json
import subprocess
import sys
import unittest


class TestTrustCLI(unittest.TestCase):
    """Test --trust flag behavior."""

    def test_missing_trust_flag_exits_with_error(self):
        """Omitting --trust should print error and exit non-zero."""
        result = subprocess.run(
            [sys.executable, "fill_1041.py", "--dry-run"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0,
                            "Should exit non-zero when --trust is omitted")

    def test_trust_trent_loads_correct_config(self):
        """--trust trent should load config and produce output."""
        result = subprocess.run(
            [sys.executable, "fill_1041.py", "--trust", "trent", "--dry-run"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0,
                         f"--trust trent dry-run failed: {result.stderr}")
        self.assertIn("Trent Foley", result.stdout,
                       "Output should reference Trent's trust name")

    def test_trust_chris_loads_correct_config(self):
        """--trust chris should load config and produce output."""
        result = subprocess.run(
            [sys.executable, "fill_1041.py", "--trust", "chris", "--dry-run"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0,
                         f"--trust chris dry-run failed: {result.stderr}")
        self.assertIn("Christopher Foley", result.stdout,
                       "Output should reference Chris's trust name")


class TestScheduleGCapBug(unittest.TestCase):
    """Test compute_schedule_g handles QD > taxable_income correctly."""

    def _load_cfg(self):
        with open("config/2025_chris.json") as f:
            return json.load(f)

    def test_chris_schedule_g_tax(self):
        """Chris: QD=$8671 > taxable=$8445.68. Tax should be $779.35, not $824.41."""
        from fill_1041 import compute_schedule_g
        cfg = self._load_cfg()
        result = compute_schedule_g(
            taxable_income=8445.68,
            qual_div=8671.00,
            lt_net_gain=0.0,
            cfg=cfg,
        )
        self.assertAlmostEqual(result["tax_on_taxable_income"], 779.35, places=2,
                               msg=f"Chris tax should be 779.35, got {result['tax_on_taxable_income']}")
        # twenty_bucket should be 0 (no overflow into 20% bracket)
        self.assertAlmostEqual(result["twenty_bucket"], 0.0, places=2,
                               msg=f"twenty_bucket should be 0, got {result['twenty_bucket']}")

    def test_trent_schedule_g_regression(self):
        """Trent's numbers should be unchanged after the cap fix."""
        from fill_1041 import compute_schedule_g
        with open("config/2025_trent.json") as f:
            cfg = json.load(f)
        result = compute_schedule_g(
            taxable_income=103790.67,
            qual_div=903.82,
            lt_net_gain=104109.76,
            cfg=cfg,
        )
        # Trent's Schedule G tax was $19,720.22 before the fix
        self.assertAlmostEqual(result["tax_on_taxable_income"], 19720.22, places=2,
                               msg=f"Trent tax should be 19720.22, got {result['tax_on_taxable_income']}")


if __name__ == "__main__":
    unittest.main()
