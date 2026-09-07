#!/usr/bin/env python3
"""Calculate and rank prefiltered property candidates; no network or persistence."""
import argparse
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import json
from statistics import median
import sys


HELP = """Read JSON from stdin; write results to stdout. Python standard library only.
Input: {run_date: YYYY-MM-DD, mode: strict|relaxed (default relaxed),
limit: 1..5, candidates: [...]}.
Candidate: id (numeric string), asking_price, sqft, zestimate (may be null),
matched_sales: [{id, sale_price, sqft, distance_miles, sold_date}],
review_reasons: [source-backed concerns], preference_misses: [explicit soft misses].
For relaxed mode, optional matched_asks: [{id, asking_price, sqft, distance_miles,
ask_date, sold_date, source_event: pending|contingent}]. These are historical
asking prices from the same sale episode, NOT closed prices.
Optional latest_cut: {previous_ask, current_ask, date} from verified current
listing history. All subjects must pass saved hard filters; all comparisons must
pass references/scanning.md matching rules before this helper. Distances come
from source coordinates. Amounts accept JSON numbers or decimal strings.
Output separates sale-backed results, indicative leads, below-threshold results,
and unassessed records. Join selected IDs to original property facts/photos.
"""

def number(value, minimum=Decimal('0'), inclusive=False):
    result = Decimal(str(value))
    if not result.is_finite() or (result < minimum if inclusive else result <= minimum):
        raise ValueError('invalid numeric value')
    return result


def property_id(value):
    value = str(value)
    if not value.isdigit() or int(value) <= 0:
        raise ValueError('invalid property ID')
    return str(int(value))


def comparisons(items, identity, size, today, radius, size_tolerance, basis):
    records = {}
    for item in items:
        try:
            sid = property_id(item['id'])
            closed = date.fromisoformat(item['sold_date'])
            price_key = 'sale_price' if basis == 'closed_sales' else 'asking_price'
            price, area = number(item[price_key]), number(item['sqft'])
            distance = number(item['distance_miles'], inclusive=True)
            if sid == identity or not 0 <= (today - closed).days <= 180:
                continue
            if distance > radius or abs(area / size - 1) > size_tolerance:
                continue
            observed = closed
            if basis == 'pending_asks':
                observed = date.fromisoformat(item['ask_date'])
                if str(item['source_event']).lower() not in ('pending', 'contingent'):
                    continue
                if observed > closed or not 0 <= (today - observed).days <= 120:
                    continue
            record = dict(id=sid, price=price, basis=basis, sqft=area,
                          distance_miles=distance, sold_date=closed,
                          price_date=observed, ppsf=price / area)
        except (ValueError, KeyError, ArithmeticError, TypeError):
            continue
        previous = records.get(sid)
        if previous and previous['sold_date'] == closed and previous != record:
            raise ValueError('conflicting duplicate comparison')
        if not previous or previous['sold_date'] < closed:
            records[sid] = record
    return sorted(records.values(), key=lambda r: (
        r['distance_miles'], abs(r['sqft'] / size - 1),
        -r['sold_date'].toordinal(), int(r['id'])))


def evaluate(candidate, today, mode):
    identity = property_id(candidate['id'])
    ask, size = (number(candidate[k]) for k in ('asking_price', 'sqft'))
    try:
        estimate = number(candidate.get('zestimate'))
    except (ValueError, ArithmeticError, TypeError):
        estimate = None
    if mode == 'strict' and estimate is None:
        raise ValueError('Zestimate missing; strict comparison cannot be assessed')
    radius = Decimal('1') if mode == 'strict' else Decimal('2.5')
    size_tolerance = Decimal('.15') if mode == 'strict' else Decimal('.30')
    minimum = 3 if mode == 'strict' else 1
    threshold = Decimal(5) if mode == 'strict' else Decimal(3)
    spread_limit = Decimal('.30') if mode == 'strict' else Decimal('.40')
    sales = comparisons(candidate.get('matched_sales', []), identity, size, today,
                        radius, size_tolerance, 'closed_sales')
    pool = {c['id']: c for c in sales}
    if mode == 'relaxed':
        for comp in comparisons(candidate.get('matched_asks', []), identity, size, today,
                                radius, size_tolerance, 'pending_asks'):
            previous = pool.get(comp['id'])
            if previous is None or previous['sold_date'] < comp['sold_date']:
                pool[comp['id']] = comp
    comps = sorted(pool.values(), key=lambda c: (
        c['distance_miles'], abs(c['sqft'] / size - 1),
        -c['sold_date'].toordinal(), int(c['id'])))[:5]
    if len(comps) < minimum:
        raise ValueError(f'fewer than {minimum} usable comparisons')
    actual_count = sum(c['basis'] == 'closed_sales' for c in comps)
    proxy_count = len(comps) - actual_count
    basis = 'closed_sales' if proxy_count == 0 else 'pending_asks' if actual_count == 0 else 'mixed'
    ppsf = [c['ppsf'] for c in comps]
    typical = median(ppsf)
    comparison_reference = typical * size
    reference = min(comparison_reference, estimate) if estimate is not None else comparison_reference
    gap = reference - ask
    percent = 100 * gap / reference
    review = list(candidate.get('review_reasons', []))
    if proxy_count:
        review.append(f'Uses {proxy_count} pending asking price(s); Needs review')
    if len(comps) == 1:
        review.append('Only one comparison; prefer 2+')
    if estimate is None:
        review.append('Zestimate unavailable; comparison reference alone; Needs review')
    if (max(ppsf) - min(ppsf)) / typical > spread_limit:
        review.append(f'Comparison-price spread exceeds {spread_limit * 100}%; Needs review')
    cut_percent = Decimal(0)
    cut = candidate.get('latest_cut')
    if cut:
        try:
            prior, current = number(cut['previous_ask']), number(cut['current_ask'])
            age = (today - date.fromisoformat(cut['date'])).days
            reduction = 100 * (prior - current) / prior
            if current == ask and 0 <= age <= 30 and reduction >= 3:
                cut_percent = reduction
        except (ValueError, KeyError, ArithmeticError, TypeError):
            pass
    return dict(id=identity, comparison_basis=basis, comparison_reference=comparison_reference,
                zestimate=estimate, reference=reference, gap_dollars=gap, gap_percent=percent,
                meets_threshold=percent >= threshold, threshold_percent=threshold,
                comparison_count=len(comps), actual_sale_count=actual_count, proxy_count=proxy_count,
                display_gap_percent=percent.quantize(Decimal('.1'), rounding=ROUND_HALF_UP),
                recent_cut_percent=cut_percent, review_reasons=review,
                preference_misses=list(candidate.get('preference_misses', [])), comparisons=comps)


def rank(payload):
    today = date.fromisoformat(payload['run_date'])
    mode = payload.get('mode', 'relaxed')
    if mode not in ('strict', 'relaxed'):
        raise ValueError('mode must be strict or relaxed')
    limit = payload.get('limit', 5)
    if type(limit) is not int or not 1 <= limit <= 5:
        raise ValueError('limit must be an integer from 1 to 5')
    ranked, below, unassessed, seen = [], [], [], set()
    for candidate in payload['candidates']:
        identity = property_id(candidate['id'])
        if identity in seen:
            raise ValueError('duplicate subject ID; deduplicate before ranking')
        seen.add(identity)
        try:
            result = evaluate(candidate, today, mode)
        except (ValueError, KeyError, ArithmeticError, TypeError) as exc:
            unassessed.append(dict(id=identity, reason=str(exc)))
            continue
        (ranked if result['meets_threshold'] else below).append(result)
    ranked.sort(key=lambda r: (r['proxy_count'] > 0,
                              bool(r['review_reasons']), r['comparison_count'] < 2, len(r['preference_misses']),
                              -r['gap_percent'], -r['gap_dollars'],
                              -r['recent_cut_percent'], int(r['id'])))
    assessed = len(ranked) + len(below)
    status = 'insufficient_evidence' if unassessed and not assessed else 'partial' if unassessed else 'complete'
    return dict(mode=mode, assessment_status=status, assessed_count=assessed,
                selected=ranked[:limit],
                sale_backed_count=sum(r['comparison_basis'] == 'closed_sales' for r in ranked),
                indicative_count=sum(r['proxy_count'] > 0 for r in ranked),
                below_threshold=below, unassessed=unassessed)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=HELP, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args()
    json.dump(rank(json.load(sys.stdin)), sys.stdout, default=str, indent=2)
    print()
