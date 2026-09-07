"""Synthetic cases for price evidence and ranking; no property/API requests."""
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'skills/property-scanner/scripts/rank_properties.py'
spec = importlib.util.spec_from_file_location('rank_properties', HELPER)
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)
TODAY = date(2026, 9, 7)


def home(identity='1', ask=485000, estimate=500000):
    return dict(id=identity, asking_price=ask, sqft=2000, zestimate=estimate,
                matched_sales=[dict(id='11', sale_price=500000, sqft=2000,
                                    distance_miles=2.5, sold_date='2026-08-01')])


def with_proxy(candidate, age=60):
    candidate['matched_asks'] = [dict(id='12', asking_price=520000, sqft=2000,
        distance_miles=1, ask_date=str(TODAY - timedelta(days=age)),
        sold_date='2026-08-01', source_event='pending')]
    return candidate


def run(*candidates, mode='relaxed', limit=5):
    return scanner.rank(dict(run_date=str(TODAY), mode=mode,
                             candidates=list(candidates), limit=limit))


class RankingTests(unittest.TestCase):
    def test_relaxed_threshold_uses_unrounded_value(self):
        result = run(home())['selected'][0]
        self.assertEqual(result['gap_percent'], 3)
        self.assertEqual(result['comparison_count'], 1)
        self.assertTrue(result['review_reasons'])
        self.assertFalse(run(home(ask=485001))['selected'])

    def test_strict_requires_three_sales_and_five_percent(self):
        self.assertEqual(run(home(), mode='strict')['assessment_status'], 'insufficient_evidence')
        candidate = home(ask=475000)
        candidate['matched_sales'] = [dict(candidate['matched_sales'][0],
            id=str(i), distance_miles=.2) for i in (21, 22, 23)]
        self.assertEqual(run(candidate, mode='strict')['selected'][0]['gap_percent'], 5)
        candidate['asking_price'] = 475001
        result = run(candidate, mode='strict')
        self.assertFalse(result['selected'])
        self.assertEqual(result['assessed_count'], 1)

    def test_missing_estimate_has_mode_specific_behavior(self):
        candidate = home(estimate=None)
        self.assertTrue(run(candidate)['selected'][0]['review_reasons'])
        self.assertEqual(run(candidate, mode='strict')['assessment_status'], 'insufficient_evidence')

    def test_lower_reference_controls_gap(self):
        candidate = home(ask=485000, estimate=1000000)
        self.assertEqual(run(candidate)['selected'][0]['reference'], 500000)
        self.assertFalse(run(home(estimate=480000))['selected'])

    def test_radius_and_size_boundaries(self):
        for field, passing, failing in [('distance_miles', 2.5, 2.50001), ('sqft', 2600, 2601)]:
            with self.subTest(field=field):
                candidate = home(ask=350000, estimate=None)
                candidate['matched_sales'][0][field] = passing
                self.assertTrue(run(candidate)['selected'])
                candidate['matched_sales'][0][field] = failing
                self.assertFalse(run(candidate)['selected'])

    def test_proxy_age_and_event_order(self):
        candidate = with_proxy(home(estimate=None), age=120)
        candidate['matched_sales'] = []
        self.assertEqual(run(candidate)['selected'][0]['comparison_basis'], 'pending_asks')
        for change in [dict(ask_date=str(TODAY - timedelta(days=121))),
                       dict(ask_date='2026-08-02'), dict(source_event='listed')]:
            with self.subTest(change=change):
                modified = deepcopy(candidate)
                modified['matched_asks'][0].update(change)
                self.assertFalse(run(modified)['selected'])

    def test_mixed_prices_are_identified(self):
        result = run(with_proxy(home(estimate=None)))['selected'][0]
        self.assertEqual(result['comparison_basis'], 'mixed')
        self.assertEqual((result['actual_sale_count'], result['proxy_count']), (1, 1))
        self.assertEqual(result['comparison_reference'], 510000)
        self.assertTrue(result['review_reasons'])

    def test_actual_price_wins_for_same_sale(self):
        candidate = with_proxy(home(estimate=None))
        candidate['matched_asks'][0].update(id='11', asking_price=900000)
        result = run(candidate)['selected'][0]
        self.assertEqual(result['proxy_count'], 0)
        self.assertEqual(result['reference'], 500000)

    def test_prefer_two_comparisons_and_preserve_id_tiebreak(self):
        one, two = home(), home('2')
        two['matched_sales'].append(dict(two['matched_sales'][0], id='12'))
        self.assertEqual([r['id'] for r in run(one, two)['selected']], ['2', '1'])
        self.assertEqual([r['id'] for r in run(home('2'), home())['selected']], ['1', '2'])

    def test_spread_boundary(self):
        candidate = home(ask=350000)
        candidate['matched_sales'] = [dict(candidate['matched_sales'][0], id=str(i),
            sale_price=price, distance_miles=.2) for i, price in enumerate([400000, 500000, 600000], 20)]
        self.assertFalse(any('spread' in r for r in run(candidate)['selected'][0]['review_reasons']))
        candidate['matched_sales'][-1]['sale_price'] = 600001
        self.assertTrue(any('spread' in r for r in run(candidate)['selected'][0]['review_reasons']))

    def test_comparisons_are_unique_and_exclude_subject(self):
        candidate = home()
        candidate['matched_sales'] *= 3
        self.assertEqual(run(candidate)['selected'][0]['comparison_count'], 1)
        candidate['matched_sales'][0]['id'] = '1'
        self.assertFalse(run(candidate)['selected'])

    def test_cut_must_end_at_current_ask(self):
        candidate = home(ask=450000)
        candidate['latest_cut'] = dict(previous_ask=475000, current_ask=450000, date='2026-09-01')
        self.assertGreater(run(candidate)['selected'][0]['recent_cut_percent'], 3)
        candidate['latest_cut']['current_ask'] = 440000
        self.assertEqual(run(candidate)['selected'][0]['recent_cut_percent'], 0)

    def test_same_evidence_gives_same_result(self):
        candidate = with_proxy(home())
        other = deepcopy(candidate)
        other['matched_sales'].reverse()
        other['matched_asks'].reverse()
        self.assertEqual(run(candidate), run(other))

    def test_cli_emits_readable_json(self):
        result = subprocess.run([sys.executable, str(HELPER)],
            input=json.dumps(dict(run_date=str(TODAY), candidates=[home()])),
            text=True, capture_output=True, check=True)
        selected = json.loads(result.stdout)['selected'][0]
        self.assertEqual(Decimal(selected['gap_percent']), 3)


if __name__ == '__main__':
    unittest.main()
