"""Deterministic synthetic-case prototype of full turnaround rescheduling.
No real-port performance or flight-validation claim is made.
Only standard-library modules are required.
"""
from __future__ import annotations
import copy, itertools, json, math, hashlib
from pathlib import Path
TOL = 1e-07

class Infeasible(ValueError):
    pass

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def emit(trace, event, **fields):
    if trace is not None:
        trace.append({'event': event, **fields})

def post_charge_delay(cfg, b):
    value = cfg.get('post_charge', 0.0)
    delay = value.get(b, 0.0) if isinstance(value, dict) else value
    if delay < 0:
        raise Infeasible('POST_CHARGE_DELAY_NEGATIVE')
    return delay

def example():
    nodes = {'O': [0, 0, 0], 'V1': [2000, 0, 20], 'V2': [4000, 0, 20], 'V3': [0, 3000, 20], 'V4': [1000, 1000, 20], 'V5': [-3000, 0, 20]}
    models = {'A': {'m0': 70, 'capacity': 25, 'volume': 0.06, 'speed': 12, 'L0': 25000, 'LF': 20000, 'energy': 4.5, 'full_charge': 1800}, 'B': {'m0': 65, 'capacity': 30, 'volume': 0.073, 'speed': 15, 'L0': 28000, 'LF': 16000, 'energy': 4.0, 'full_charge': 2400}}
    boxes = {f'K{i}': {'ship': f'V{i}', 'mass': mass, 'volume': 0.01, 'ready': 0, 'due': end + 60, 'hard': end + 60, 'weight': 1} for i, (mass, end) in enumerate([(8, 400), (6, 700), (10, 350), (5, 1800), (12, 600)], 1)}
    windows = {f'V{i}': [[60, end + 60]] for i, end in enumerate([400, 700, 350, 1800, 600], 1)}
    return {'nodes': nodes, 'models': models, 'boxes': boxes, 'windows': windows, 'handover': 60.0, 'handover_power': 4.0, 'height': 60.0, 'up_speed': 3.0, 'down_speed': 3.0, 'efficiency': 0.72, 'gravity': 9.81, 'reserve': 0.2, 'prepare': 60.0, 'turn': 60.0, 'cool': 0.0, 'time_origin': 0.0, 'max_visits': 3, 'drones': {'A-U1': 'A', 'A-U2': 'A', 'B-U1': 'B'}, 'batteries': {'A-B1': 'A', 'A-B2': 'A', 'B-B1': 'B'}, 'stations': {'A-C1': ['A'], 'B-C1': ['B']}, 'initial_u': {}, 'initial_b': {}, 'initial_c': {}}

def charge_time(model, soc):
    if not -TOL <= soc <= 1 + TOL:
        raise Infeasible('SOC_RANGE')
    soc = max(0.0, min(1.0, soc))
    T = model['full_charge']
    return T * (0.65 * (0.9 - soc) / 0.9 + 0.35) if soc < 0.9 else T * 0.35 * (1 - soc) / 0.1

def station_charge_time(cfg, g, c, soc):
    model = dict(cfg['models'][g])
    model['full_charge'] = cfg.get('charge_seconds', {}).get(c, {}).get(g, model['full_charge'])
    return charge_time(model, soc)

def profile(cfg, job, order):
    m = cfg['models'][job['type']]
    boxes = job['boxes']
    shipset = {cfg['boxes'][k]['ship'] for k in boxes}
    if len(order) != len(set(order)) or set(order) != shipset:
        raise Infeasible('VISIT_COVERAGE')
    if len(order) > cfg['max_visits']:
        raise Infeasible('VISIT_CAP')
    q = sum((cfg['boxes'][k]['mass'] for k in boxes))
    vol = sum((cfg['boxes'][k]['volume'] for k in boxes))
    if q > m['capacity'] + TOL or vol > m['volume'] + TOL:
        raise Infeasible('CAPACITY')
    t = 0.0
    energy = 0.0
    start = {}
    end = {}
    legs = []
    distance = 0.0
    route = ['O', *order, 'O']
    for a, b in zip(route, route[1:]):
        x, y, z = cfg['nodes'][a]
        xx, yy, zz = cfg['nodes'][b]
        d = math.hypot(xx - x, yy - y)
        up = max(0.0, cfg['height'] - z)
        down = max(0.0, cfg['height'] - zz)
        dt = up / cfg['up_speed'] + d / m['speed'] + down / cfg['down_speed']
        L = m['L0'] - (m['L0'] - m['LF']) * (q / m['capacity']) ** 1.5
        de = d * m['energy'] / L + (m['m0'] + q) * cfg['gravity'] * up / (3600000.0 * cfg['efficiency'])
        legs.append({'from': a, 'to': b, 'load': q, 'seconds': dt, 'energy': de})
        distance += d
        t += dt
        energy += de
        if b != 'O':
            start[b] = t
            t += cfg['handover']
            end[b] = t
            energy += cfg['handover_power'] * cfg['handover'] / 3600
            q -= sum((cfg['boxes'][k]['mass'] for k in boxes if cfg['boxes'][k]['ship'] == b))
    soc = 1 - energy / m['energy']
    if soc < cfg['reserve'] - TOL:
        raise Infeasible('RETURN_RESERVE')
    intervals = []
    for combo in itertools.product(*(cfg['windows'][v] for v in order)):
        L = max((alpha - start[v] for v, (alpha, beta) in zip(order, combo)))
        U = min([beta - end[v] for v, (alpha, beta) in zip(order, combo)] + [cfg['boxes'][k]['hard'] - end[cfg['boxes'][k]['ship']] for k in boxes])
        if L <= U + TOL:
            intervals.append({'lower': L, 'upper': U, 'selected_windows': dict(zip(order, combo))})
    if not intervals:
        raise Infeasible('WINDOW_INTERSECTION')
    return {'duration': t, 'energy': energy, 'soc': soc, 'charge': charge_time(m, soc), 'arrival': start, 'completion': end, 'intervals': intervals, 'legs': legs, 'distance': distance}

def objective(cfg, records):
    delivered = {k: r['takeoff'] + r['completion'][cfg['boxes'][k]['ship']] for r in records for k in r['boxes']}
    W = sum((cfg['boxes'][k]['weight'] * max(0, t - cfg['boxes'][k]['due']) for k, t in delivered.items()))
    return [W, max((r['return'] for r in records), default=0.0), sum((r['energy'] for r in records)), len(records)]

def schedule(cfg, jobs, priority, trace=None):
    ids = [j['id'] for j in jobs]
    if len(ids) != len(set(ids)) or sorted(priority) != sorted(ids):
        raise Infeasible('JOB_IDS')
    assigned = [k for j in jobs for k in j['boxes']]
    if len(assigned) != len(set(assigned)) or set(assigned) != set(cfg['boxes']):
        raise Infeasible('BOX_COVERAGE')
    Au = {u: cfg['initial_u'].get(u, 0.0) for u in cfg['drones']}
    Ab = {b: cfg['initial_b'].get(b, 0.0) for b in cfg['batteries']}
    Ac = {c: cfg['initial_c'].get(c, 0.0) for c in cfg['stations']}
    records = []
    snapshot_hash = digest(cfg)
    attempt = 1 + sum((x['event'] == 'ORDER_START' for x in trace)) if trace is not None else 0
    emit(trace, 'ORDER_START', attempt=attempt, priority=list(priority), snapshot_sha256=snapshot_hash, initial_u=dict(Au), initial_b=dict(Ab), initial_c=dict(Ac))
    for id in priority:
        job = next((j for j in jobs if j['id'] == id))
        candidates = []
        errors = []
        orderlist = [job['order']] if job.get('order') else list(itertools.permutations(sorted({cfg['boxes'][k]['ship'] for k in job['boxes']})))
        for order in orderlist:
            try:
                p = profile(cfg, job, order)
            except Infeasible as e:
                errors.append(str(e))
                continue
            for window_index, interval in enumerate(p['intervals']):
                for u in sorted(cfg['drones']):
                    if cfg['drones'][u] != job['type']:
                        continue
                    for b in sorted(cfg['batteries']):
                        if cfg['batteries'][b] != job['type']:
                            continue
                        ready = max(Au[u], Ab[b], cfg['time_origin'], *(cfg['boxes'][k]['ready'] for k in job['boxes']))
                        s = max(interval['lower'], ready + cfg['prepare'])
                        if s > interval['upper'] + TOL:
                            errors.append(f"READINESS_WINDOW: earliest={s:.6f} upper={interval['upper']:.6f} battery={b}")
                            continue
                        f = s + p['duration']
                        stations = [c for c in sorted(cfg['stations']) if job['type'] in cfg['stations'][c]]
                        if p['charge'] <= TOL:
                            stations = [None]
                        for c in stations:
                            cs = max(f + cfg['cool'], Ac[c]) if c else f + cfg['cool']
                            ce = cs + station_charge_time(cfg, job['type'], c, p['soc'])
                            battery_ready = ce + post_charge_delay(cfg, b)
                            row = {'job': id, 'type': job['type'], 'boxes': list(job['boxes']), 'order': list(order), 'drone': u, 'battery': b, 'station': c, 'prepare_start': s - cfg['prepare'], 'takeoff': s, 'return': f, 'energy': p['energy'], 'soc': p['soc'], 'charge_start': cs, 'charge_end': ce, 'battery_full_ready': battery_ready, 'post_charge_delay': post_charge_delay(cfg, b), 'window_choice_index': window_index, 'completion': p['completion'], 'arrival': p['arrival'], 'selected_windows': interval['selected_windows'], 'window_interval': [interval['lower'], interval['upper']], 'u_interval': [s - cfg['prepare'], f + cfg['turn']], 'b_interval': [s - cfg['prepare'], battery_ready], 'c_interval': [cs, ce] if c else None, 'queue': cs - (f + cfg['cool'])}
                            W = sum((cfg['boxes'][k]['weight'] * max(0, s + p['completion'][cfg['boxes'][k]['ship']] - cfg['boxes'][k]['due']) for k in job['boxes']))
                            candidates.append(((W, f, battery_ready, p['energy'], ce, u, b, c or '', tuple(order), window_index), row))
        emit(trace, 'CANDIDATES_ENUMERATED', attempt=attempt, job=id, valid_bindings=len(candidates))
        if not candidates:
            emit(trace, 'ORDER_ROLLBACK', attempt=attempt, failed_job=id, discarded_jobs=len(records), reasons=sorted(set(errors)), input_unchanged=digest(cfg) == snapshot_hash)
            return {'feasible': False, 'failure_kind': 'THIS_ORDER_FOUND_NO_COMPLETE_SCHEDULE', 'failed_job': id, 'reasons': sorted(set(errors)), 'partial': records}
        selected_key, row = min(candidates, key=lambda x: x[0])
        records.append(row)
        emit(trace, 'BINDING_SELECTED', attempt=attempt, job=id, comparison_key=selected_key, selected_record=copy.deepcopy(row))
        Au[row['drone']] = row['return'] + cfg['turn']
        Ab[row['battery']] = row['battery_full_ready']
        if row['station']:
            Ac[row['station']] = row['charge_end']
        emit(trace, 'SELECTED_BINDING_COMMITTED', attempt=attempt, job=id, drone=row['drone'], battery=row['battery'], station=row['station'], u_available=Au[row['drone']], b_available=Ab[row['battery']], c_available=Ac[row['station']] if row['station'] else None)
    result = {'feasible': True, 'records': records, 'objective': objective(cfg, records), 'priority': list(priority)}
    audit(cfg, result)
    emit(trace, 'ORDER_COMPLETE', attempt=attempt, objective=result['objective'], input_unchanged=digest(cfg) == snapshot_hash)
    return result

def audit(cfg, result):
    if not result.get('feasible'):
        raise Infeasible('NOT_COMPLETE')
    records = result['records']
    assigned = [k for r in records for k in r['boxes']]
    if len(assigned) != len(set(assigned)) or set(assigned) != set(cfg['boxes']):
        raise Infeasible('AUDIT_COVERAGE')
    Au = {u: cfg['initial_u'].get(u, 0.0) for u in cfg['drones']}
    Ab = {b: cfg['initial_b'].get(b, 0.0) for b in cfg['batteries']}
    Ac = {c: cfg['initial_c'].get(c, 0.0) for c in cfg['stations']}
    for r in records:
        g = r['type']
        u = r['drone']
        b = r['battery']
        c = r['station']
        if cfg['drones'].get(u) != g or cfg['batteries'].get(b) != g or (c and g not in cfg['stations'].get(c, [])):
            raise Infeasible('AUDIT_COMPATIBILITY')
        p = profile(cfg, {'boxes': r['boxes'], 'type': g}, r['order'])
        s = r['takeoff']
        ready = max(Au[u], Ab[b], cfg['time_origin'], *(cfg['boxes'][k]['ready'] for k in r['boxes']))
        if s - cfg['prepare'] < ready - TOL:
            raise Infeasible('AUDIT_NOT_READY')
        if not any((L['lower'] - TOL <= s <= L['upper'] + TOL for L in p['intervals'])):
            raise Infeasible('AUDIT_WINDOW')
        for ship in r['order']:
            window = r['selected_windows'].get(ship)
            if window not in cfg['windows'][ship] or s + p['arrival'][ship] < window[0] - TOL or s + p['completion'][ship] > window[1] + TOL:
                raise Infeasible('AUDIT_SELECTED_WINDOW')
        f = s + p['duration']
        cs = max(f + cfg['cool'], Ac[c]) if p['charge'] > TOL and c else f + cfg['cool']
        ce = cs + station_charge_time(cfg, g, c, p['soc'])
        battery_ready = ce + post_charge_delay(cfg, b)
        if p['charge'] > TOL and (not c):
            raise Infeasible('AUDIT_MISSING_CHARGER')
        expected = {'prepare_start': s - cfg['prepare'], 'return': f, 'energy': p['energy'], 'soc': p['soc'], 'charge_start': cs, 'charge_end': ce, 'battery_full_ready': battery_ready, 'post_charge_delay': post_charge_delay(cfg, b)}
        for key, value in expected.items():
            if abs(r[key] - value) > TOL:
                raise Infeasible('AUDIT_RECOMPUTATION:' + key)
        for key, value in {'completion': p['completion'], 'arrival': p['arrival']}.items():
            if any((abs(r[key][k] - v) > TOL for k, v in value.items())):
                raise Infeasible('AUDIT_OFFSETS')
        expected_intervals = {'u_interval': [s - cfg['prepare'], f + cfg['turn']], 'b_interval': [s - cfg['prepare'], battery_ready], 'c_interval': [cs, ce] if c else None}
        for key, value in expected_intervals.items():
            if value is None and r[key] is not None or (value is not None and (r[key] is None or any((abs(a - b) > TOL for a, b in zip(value, r[key]))))):
                raise Infeasible('AUDIT_INTERVALS')
        Au[u] = f + cfg['turn']
        Ab[b] = battery_ready
        if c:
            Ac[c] = ce
    for resource, key, field in [('drone', 'u_interval', 'u'), ('battery', 'b_interval', 'b'), ('station', 'c_interval', 'c')]:
        for a, b in itertools.combinations(records, 2):
            if a[resource] and a[resource] == b[resource] and (max(a[key][0], b[key][0]) < min(a[key][1], b[key][1]) - TOL):
                raise Infeasible('AUDIT_OVERLAP:' + field)
    return True

def evaluate(cfg, jobs, trace=None):
    distance = lambda j: sum((math.hypot(cfg['nodes'][cfg['boxes'][k]['ship']][0], cfg['nodes'][cfg['boxes'][k]['ship']][1]) for k in j['boxes']))
    orders = [[j['id'] for j in sorted(jobs, key=key)] for key in [lambda j: (min((cfg['boxes'][k]['due'] for k in j['boxes'])), j['id']), lambda j: (min((cfg['boxes'][k]['hard'] for k in j['boxes'])), j['id']), lambda j: (-distance(j), j['id'])]]
    emit(trace, 'PRIORITY_ORDERS_GENERATED', orders=orders)
    results = [schedule(cfg, jobs, o, trace=trace) for o in orders]
    feasible = [r for r in results if r['feasible']]
    if not feasible:
        emit(trace, 'ALL_ATTEMPTED_ORDERS_FAILED', attempted=len(results))
        return {'feasible': False, 'failure_kind': 'THIS_EVALUATION_FOUND_NO_COMPLETE_SCHEDULE', 'failures': results}
    return min(feasible, key=lambda r: r['objective'])

def initial_jobs():
    return [{'id': 'P1', 'type': 'A', 'boxes': ['K1', 'K2'], 'order': ['V1', 'V2']}, {'id': 'P2', 'type': 'A', 'boxes': ['K3'], 'order': ['V3']}, {'id': 'P4', 'type': 'B', 'boxes': ['K5'], 'order': ['V5']}, {'id': 'P3', 'type': 'A', 'boxes': ['K4'], 'order': ['V4']}]

def neighbor_checks(cfg, jobs):
    candidates = []

    def add(kind, rows):
        for r in rows:
            r.pop('order', None)
        candidates.append((kind, rows))
    for i, j in itertools.combinations(range(len(jobs)), 2):
        for g in cfg['models']:
            rest = [copy.deepcopy(x) for k, x in enumerate(jobs) if k not in [i, j]]
            rest.append({'id': f'MERGE-{i}-{j}', 'type': g, 'boxes': jobs[i]['boxes'] + jobs[j]['boxes']})
            add('merge', rest)
        for a in jobs[i]['boxes']:
            for b in jobs[j]['boxes']:
                rows = copy.deepcopy(jobs)
                rows[i]['boxes'] = [k for k in rows[i]['boxes'] if k != a] + [b]
                rows[j]['boxes'] = [k for k in rows[j]['boxes'] if k != b] + [a]
                add('swap', rows)
    for i, job in enumerate(jobs):
        if len(job['boxes']) > 1:
            rows = copy.deepcopy(jobs)
            box = rows[i]['boxes'].pop()
            rows.append({'id': f'SPLIT-{i}', 'type': job['type'], 'boxes': [box]})
            add('split', rows)
        for g in cfg['models']:
            if g != job['type']:
                rows = copy.deepcopy(jobs)
                rows[i]['type'] = g
                add('change_type', rows)
        for j in range(len(jobs)):
            if i == j:
                continue
            for box in job['boxes']:
                rows = copy.deepcopy(jobs)
                rows[i]['boxes'].remove(box)
                rows[j]['boxes'].append(box)
                rows = [r for r in rows if r['boxes']]
                add('move', rows)
    count = {}
    feasible = {}
    archive = []
    original = copy.deepcopy(cfg)
    for kind, rows in candidates:
        count[kind] = count.get(kind, 0) + 1
        result = evaluate(cfg, rows)
        if result['feasible']:
            audit(cfg, result)
            feasible[kind] = feasible.get(kind, 0) + 1
            archive.append(result)
    assert cfg == original
    assert candidates and archive
    return {'evaluated_candidates': len(candidates), 'counts': count, 'feasible_counts': feasible, 'best_candidate_objective': min(archive, key=lambda r: r['objective'])['objective'], 'scope': 'one-neighborhood synthetic mechanism check; not global optimization or port-performance study'}

def demonstration():
    trace = []
    cfg = example()
    jobs = initial_jobs()
    baseline = schedule(cfg, jobs, ['P2', 'P1', 'P4', 'P3'], trace=trace)
    assert baseline['feasible']
    assert abs(baseline['objective'][2] - 4.471622571318991) < 1e-08
    reversed_jobs = copy.deepcopy(jobs)
    reversed_jobs[0]['order'] = ['V2', 'V1']
    reverse = schedule(cfg, reversed_jobs, ['P2', 'P1', 'P4', 'P3'], trace=trace)
    assert not reverse['feasible']
    forward = profile(cfg, jobs[0], jobs[0]['order'])
    backward = profile(cfg, reversed_jobs[0], reversed_jobs[0]['order'])
    assert forward['distance'] == backward['distance']
    p2 = next((r for r in baseline['records'] if r['job'] == 'P2'))
    p3 = next((r for r in baseline['records'] if r['job'] == 'P3'))
    assert p3['prepare_start'] >= p2['charge_end'] - TOL
    tampered = copy.deepcopy(baseline)
    tr = next((r for r in tampered['records'] if r['job'] == 'P3'))
    tr['takeoff'] = p2['return'] + cfg['turn'] + cfg['prepare']
    try:
        audit(cfg, tampered)
    except Infeasible as e:
        tamper_error = str(e)
        emit(trace, 'STALE_BATTERY_RECORD_REJECTED', reason=tamper_error)
    else:
        raise AssertionError('independent audit did not reject a stale battery schedule')
    subcfg = copy.deepcopy(cfg)
    subcfg['boxes'] = {k: v for k, v in subcfg['boxes'].items() if k in ['K3', 'K4', 'K5']}
    subcfg['batteries'].pop('A-B2')
    subjobs = [j for j in jobs if j['id'] != 'P1']
    separate = schedule(subcfg, subjobs, ['P4', 'P2', 'P3'], trace=trace)
    assert separate['feasible']
    sharedcfg = copy.deepcopy(subcfg)
    sharedcfg['stations'] = {'SHARED-C1': ['A', 'B']}
    shared = schedule(sharedcfg, subjobs, ['P4', 'P2', 'P3'], trace=trace)
    assert not shared['feasible'] and shared['failed_job'] == 'P3'
    reordered = schedule(sharedcfg, subjobs, ['P2', 'P4', 'P3'], trace=trace)
    assert reordered['feasible']
    again = schedule(cfg, jobs, ['P2', 'P1', 'P4', 'P3'], trace=trace)
    assert again == baseline
    gapcfg = copy.deepcopy(subcfg)
    gapcfg['boxes'] = {'K4': gapcfg['boxes']['K4']}
    gapcfg['drones'] = {'A-U1': 'A'}
    gapcfg['batteries'] = {'A-B1': 'A'}
    gapcfg['stations'] = {'A-C1': ['A']}
    gapcfg['windows'] = {'V4': [[60, 360], [660, 960]]}
    gapjob = {'id': 'GAP', 'type': 'A', 'boxes': ['K4'], 'order': ['V4']}
    offsets = profile(gapcfg, gapjob, ['V4'])
    gapcfg['initial_u'] = {'A-U1': 400}
    gap = schedule(gapcfg, [gapjob], ['GAP'])
    assert gap['feasible'] and gap['records'][0]['takeoff'] >= offsets['intervals'][1]['lower'] - TOL
    fastcfg = copy.deepcopy(gapcfg)
    fastcfg['initial_u'] = {}
    fastcfg['stations'] = {'A-C1': ['A'], 'FAST-C2': ['A']}
    fastcfg['charge_seconds'] = {'FAST-C2': {'A': 900}}
    fast = schedule(fastcfg, [gapjob], ['GAP'])
    assert fast['feasible'] and fast['records'][0]['station'] == 'FAST-C2'
    postcfg = copy.deepcopy(cfg)
    postcfg['boxes'] = {k: v for k, v in postcfg['boxes'].items() if k in ['K3', 'K4']}
    postcfg['boxes']['K4'].update({'hard': 2600, 'due': 2600})
    postcfg['windows']['V4'] = [[60, 2600]]
    postcfg['batteries'] = {'A-B1': 'A'}
    postcfg['drones'] = {'A-U1': 'A', 'A-U2': 'A'}
    postcfg['stations'] = {'A-C1': ['A']}
    postcfg['post_charge'] = {'A-B1': 120.0}
    postjobs = [j for j in jobs if j['id'] in ['P2', 'P3']]
    postres = schedule(postcfg, postjobs, ['P2', 'P3'], trace=trace)
    assert postres['feasible']
    postp2, postp3 = postres['records']
    assert abs(postp2['battery_full_ready'] - postp2['charge_end'] - 120) < TOL
    assert abs(postp3['prepare_start'] - postp2['battery_full_ready']) < TOL
    badcfg = copy.deepcopy(cfg)
    badcfg['initial_b'] = {b: 1000000.0 for b in badcfg['batteries']}
    failed = evaluate(badcfg, jobs, trace=trace)
    assert not failed['feasible'] and failed['failure_kind'] == 'THIS_EVALUATION_FOUND_NO_COMPLETE_SCHEDULE'
    return {'runtime_trace': trace, 'post_charge_handling': postres, 'all_attempts_failed': failed, 'neighbor_checks': neighbor_checks(cfg, jobs), 'station_curve_check': 'passed', 'purpose': 'Synthetic small-case mechanism checks, not real-port performance validation', 'inputs': cfg, 'baseline': baseline, 'route_reversal': {'same_distance': forward['distance'], 'rejected': reverse}, 'battery_reuse': {'drone_ready': p2['return'] + cfg['turn'], 'battery_full': p2['charge_end'], 'next_takeoff': p3['takeoff'], 'audit_rejects_tamper': tamper_error}, 'finite_station': {'separate_stations': separate, 'shared_station_rejected_order': shared, 'shared_station_reordered_feasible': reordered}, 'snapshot_repeatability': 'passed', 'multiple_disjoint_windows': 'passed', 'scope': 'Full candidate timeline and three mechanisms checked; no broad optimization performance claim'}
if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, default=Path(__file__).with_name('port-dispatch_20261012113350-checks.json'))
    ap.add_argument('--trace-output', type=Path)
    args = ap.parse_args()
    result = demonstration()
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    if args.trace_output:
        args.trace_output.write_text('\n'.join((json.dumps({'sequence': i + 1, **e}, ensure_ascii=False) for i, e in enumerate(result['runtime_trace']))) + '\n')
    print(json.dumps({'baseline_objective': result['baseline']['objective'], 'battery_reuse': result['battery_reuse'], 'route_reversal': 'rejected', 'shared_station_order': 'rejected; alternate order feasible', 'repeatability': 'passed', 'disjoint_windows': 'passed', 'neighbor_checks': result['neighbor_checks']}, ensure_ascii=False, indent=2))
