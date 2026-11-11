# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# MV2 of Munim, Inc. Made with AI agents working in his name.
"""Offline tests for score_tradeoff.py (standard library only)."""
import unittest

import score_tradeoff as st


class TokenEfficiencyTests(unittest.TestCase):
    def test_default_baseline_is_850(self):
        self.assertEqual(st.BASELINE_TOKENS_PER_QUESTION, 850)

    def test_zero_tokens_is_100(self):
        self.assertEqual(st.token_efficiency(0), 100.0)

    def test_baseline_length_is_50(self):
        self.assertEqual(st.token_efficiency(850), 50.0)

    def test_300_tokens(self):
        # 85000 / 1150
        self.assertAlmostEqual(st.token_efficiency(300), 73.91304347826087, places=9)

    def test_earlier_baseline_still_available(self):
        self.assertEqual(st.token_efficiency(2000, baseline=2000), 50.0)
        self.assertAlmostEqual(st.token_efficiency(300, baseline=2000), 86.95652173913044, places=9)

    def test_totals_equal_mean_form(self):
        # organisers' form: 100 * 850N / (850N + sum); [100, 500] has mean 300
        self.assertAlmostEqual(st.token_efficiency_from_counts([100, 500]),
                               st.token_efficiency(300), places=9)

    def test_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            st.token_efficiency(-1)
        with self.assertRaises(ValueError):
            st.token_efficiency(10, baseline=0)
        with self.assertRaises(ValueError):
            st.token_efficiency_from_counts([])
        with self.assertRaises(ValueError):
            st.token_efficiency_from_counts([5000])


class OverallTests(unittest.TestCase):
    def test_80_at_300(self):
        # 56 + 0.3 * 73.913043... = 78.173913...
        self.assertAlmostEqual(st.overall(80, 300), 78.17391304, places=6)

    def test_90_at_2000(self):
        # 63 + 0.3 * 29.824561... = 71.947368...
        self.assertAlmostEqual(st.overall(90, 2000), 71.94736842, places=6)

    def test_earlier_90_at_2000(self):
        self.assertAlmostEqual(st.overall(90, 2000, baseline=2000), 78.0, places=9)

    def test_short_80_beats_long_95(self):
        # 78.17 (80% at 300 tokens) vs 75.45 (95% at 2000 tokens)
        self.assertGreater(st.overall(80, 300), st.overall(95, 2000))

    def test_95_at_1000_beats_80_at_300(self):
        # 80.28 vs 78.17: with B = 850 a 1,000-token prompt can still pay if it buys 15 points
        self.assertGreater(st.overall(95, 1000), st.overall(80, 300))

    def test_accuracy_must_be_percentage(self):
        with self.assertRaises(ValueError):
            st.overall(101, 0)


class BreakevenTests(unittest.TestCase):
    def test_300_to_2000(self):
        self.assertAlmostEqual(st.breakeven_accuracy_gain(300, 2000), 18.8951, places=3)

    def test_earlier_300_to_2000(self):
        self.assertAlmostEqual(st.breakeven_accuracy_gain(300, 2000, baseline=2000), 15.8385, places=3)

    def test_1000_to_2000(self):
        self.assertAlmostEqual(st.breakeven_accuracy_gain(1000, 2000), 6.909165, places=5)

    def test_marginal_cost_at_300(self):
        # (3/7) * (85000/1150 - 85000/1250) = (3/7) * 5.9130435
        self.assertAlmostEqual(st.marginal_cost_per_100_tokens(300), 2.53416, places=4)

    def test_marginal_cost_falls_with_length(self):
        self.assertGreater(st.marginal_cost_per_100_tokens(100), st.marginal_cost_per_100_tokens(3000))

    def test_report_shape(self):
        rep = st.report()
        self.assertEqual(len(rep["overall_grid"]), 24)
        self.assertEqual(rep["weights"], [0.7, 0.3])
        self.assertEqual(rep["baseline_tokens_per_question"], 850)
        self.assertEqual(st.report(2000)["baseline_tokens_per_question"], 2000)


class CliTests(unittest.TestCase):
    def test_parse_baseline(self):
        self.assertEqual(st.parse_baseline([]), 850)
        self.assertEqual(st.parse_baseline(["--baseline", "2000"]), 2000.0)
        with self.assertRaises(ValueError):
            st.parse_baseline(["--baseline"])
        with self.assertRaises(ValueError):
            st.parse_baseline(["--baseline", "0"])


if __name__ == "__main__":
    unittest.main()
