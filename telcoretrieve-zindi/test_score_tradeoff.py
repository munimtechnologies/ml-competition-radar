# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# MV2 of Munim, Inc. Made with AI agents working in his name.
"""Offline tests for score_tradeoff.py (standard library only)."""
import unittest

import score_tradeoff as st


class TokenEfficiencyTests(unittest.TestCase):
    def test_zero_tokens_is_100(self):
        self.assertEqual(st.token_efficiency(0), 100.0)

    def test_baseline_length_is_50(self):
        self.assertEqual(st.token_efficiency(2000), 50.0)

    def test_300_tokens(self):
        self.assertAlmostEqual(st.token_efficiency(300), 86.95652173913044, places=9)

    def test_totals_equal_mean_form(self):
        # organisers' form: 100 * 2000N / (2000N + sum); [100, 500] has mean 300
        self.assertAlmostEqual(st.token_efficiency_from_counts([100, 500]),
                               st.token_efficiency(300), places=9)

    def test_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            st.token_efficiency(-1)
        with self.assertRaises(ValueError):
            st.token_efficiency_from_counts([])
        with self.assertRaises(ValueError):
            st.token_efficiency_from_counts([5000])


class OverallTests(unittest.TestCase):
    def test_80_at_300(self):
        self.assertAlmostEqual(st.overall(80, 300), 82.08695652, places=6)

    def test_90_at_2000(self):
        self.assertAlmostEqual(st.overall(90, 2000), 78.0, places=9)

    def test_short_80_beats_long_95(self):
        # 82.087 (80% at 300 tokens) vs 81.5 (95% at 2000 tokens)
        self.assertGreater(st.overall(80, 300), st.overall(95, 2000))

    def test_accuracy_must_be_percentage(self):
        with self.assertRaises(ValueError):
            st.overall(101, 0)


class BreakevenTests(unittest.TestCase):
    def test_300_to_2000(self):
        self.assertAlmostEqual(st.breakeven_accuracy_gain(300, 2000), 15.8385, places=3)

    def test_1000_to_2000(self):
        self.assertAlmostEqual(st.breakeven_accuracy_gain(1000, 2000), 7.142857, places=5)

    def test_marginal_cost_at_300(self):
        self.assertAlmostEqual(st.marginal_cost_per_100_tokens(300), 1.5528, places=4)

    def test_marginal_cost_falls_with_length(self):
        self.assertGreater(st.marginal_cost_per_100_tokens(100), st.marginal_cost_per_100_tokens(3000))

    def test_report_shape(self):
        rep = st.report()
        self.assertEqual(len(rep["overall_grid"]), 24)
        self.assertEqual(rep["weights"], [0.7, 0.3])


if __name__ == "__main__":
    unittest.main()
