"""Vergelijkt de planner van twee versies (bv. vóór en na een wijziging) op dezelfde diagnose-export.

  python3 tools/vergelijk.py <oud.yaml> <nieuw.yaml> <export.json> [--tijd ...] [entity=waarde ...]
      [--varieer entity=w1,w2,...]

Voorbeeld (minimale spread 0, 3, 25% en een lege accu):
  git show HEAD~1:"Dutch (NL) Integration/packages/zendure_forecasting.yaml" > /tmp/oud.yaml
  python3 tools/vergelijk.py /tmp/oud.yaml "Dutch (NL) Integration/packages/zendure_forecasting.yaml" export.json \\
      sensor.zendure_2400_ac_laadpercentage=10 --varieer input_number.dynamisch_minimale_spread=0,3,25
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import planner_sim

SLEUTELS = {
    'NL': ['netladen_vandaag_kwh', 'gepland_netladen_kwh', 'padcheck_tekort_dure_slots_kwh',
           'padcheck_netladen_kwh', 'morgen_netladen_indicatie_kwh', 'geplande_slots', 'morgen_laadmomenten', 'plan_uitleg'],
    'EN': ['grid_charge_today_kwh', 'planned_grid_charge_kwh', 'pathcheck_shortfall_expensive_slots_kwh',
           'pathcheck_grid_charge_kwh', 'tomorrow_grid_charge_estimate_kwh', 'planned_slots', 'tomorrow_charge_moments', 'plan_explanation'],
}


def kort(o, taal):
    r = {'state': o['state']}
    for k in SLEUTELS[taal]:
        v = o.get(k)
        if isinstance(v, list):
            v = [x.get('start') if isinstance(x, dict) else x for x in v]
        r[k] = v
    return r


def main():
    a = sys.argv[1:]
    tijd, varieer = None, None
    if '--tijd' in a:
        i = a.index('--tijd'); tijd = a[i + 1]; del a[i:i + 2]
    if '--varieer' in a:
        i = a.index('--varieer'); e_, w = a[i + 1].split('=', 1); varieer = (e_, w.split(',')); del a[i:i + 2]
    oud, nieuw, exp = a[:3]
    ov = dict(x.split('=', 1) for x in a[3:])
    export = json.load(open(exp, encoding='utf-8'))
    taal = (export.get('meta') or {}).get('taal') or (export.get('meta') or {}).get('language') or 'NL'
    for w in (varieer[1] if varieer else [None]):
        o2 = dict(ov)
        if varieer:
            o2[varieer[0]] = w
        r = {n: kort(planner_sim.run(p, export, o2, tijd)[0], taal) for n, p in (('oud', oud), ('nieuw', nieuw))}
        kop = (varieer[0] + ' = ' + w) if varieer else 'standen uit de export'
        print('\n== %s %s' % (kop, '(gelijk)' if r['oud'] == r['nieuw'] else '(VERSCHILLEND)'))
        for n in ('oud', 'nieuw'):
            print('  %-5s %s' % (n, json.dumps(r[n], ensure_ascii=False)))


if __name__ == '__main__':
    main()
