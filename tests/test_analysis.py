"""Regression tests for consequential counting and missingness defects."""
import unittest
import pandas as pd

from src.analysis import DAMAGE, prepare, group_metrics, pareto


def sample():
    return pd.DataFrame({
        'Dis No': ['2020-0001-AAA', '2020-0001-BBB', '2021-0002-AAA'],
        'Year': [2020, 2020, 2021], 'Country': ['A', 'B', 'A'],
        'ISO': ['AAA', 'BBB', 'AAA'], 'Continent': ['X'] * 3,
        'Disaster Type': ['Storm ', 'Storm', 'Storm'],
        'Event Name': [None, 'Named', None], 'Start Month': [None, 13, 6],
        'Total Deaths': [None, 0, 1], 'Total Affected': [None, 4, 3],
        DAMAGE: [None, 80, 20]})


class MetricsTests(unittest.TestCase):
    def test_window_grain_and_unknowns(self):
        df = prepare(sample())
        self.assertEqual(len(df), 2)
        self.assertEqual(df['Event_ID'].nunique(), 1)
        self.assertEqual(df['Disaster Type'].nunique(), 1)
        self.assertTrue(pd.isna(df.loc[0, 'Total Deaths']))
        self.assertEqual(df['Start Month'].isna().sum(), 2)
        self.assertEqual(df['Month_Invalid'].sum(), 1)

    def test_unnamed_records_count_and_unknown_sum(self):
        df = prepare(sample())
        result = group_metrics(df, ['Disaster Type'])
        self.assertEqual(result.loc[0, 'records'], 2)
        self.assertEqual(result.loc[0, 'damage_coverage_pct'], 50)
        result = group_metrics(df, ['Country'])
        self.assertTrue(pd.isna(result.loc[result.Country == 'A', 'reported_damage_thousand_usd'].iloc[0]))

    def test_duplicate_ids_rejected(self):
        raw = sample()
        raw.loc[1, 'Dis No'] = raw.loc[0, 'Dis No']
        with self.assertRaises(ValueError):
            prepare(raw)

    def test_pareto_unknown_excluded_zero_included(self):
        _, p = pareto(pd.DataFrame({DAMAGE: [80, 20, 0, None]}))
        self.assertEqual(p['observed_records'], 3)
        self.assertEqual(p['top_records'], 1)
        self.assertAlmostEqual(p['top_share_pct'], 100 / 3)

    def test_no_losses_has_no_threshold(self):
        for values in [[None, None], [0, 0]]:
            curve, p = pareto(pd.DataFrame({DAMAGE: values}))
            self.assertTrue(curve.empty)
            self.assertIsNone(p['top_records'])


if __name__ == '__main__':
    unittest.main()
