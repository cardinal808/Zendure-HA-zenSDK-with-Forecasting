"""Scenario-simulatie voor de Forecasting-planner (gesloten lus + optimum).

Bouwt op een echte diagnose-export (alleen als basis voor alle entiteiten) een synthetisch
scenario: vaste prijzen per uur, vast verbruik per uur, geen zon, eigen accu. Daarna:

1. gesloten lus: elk kwartier de planner draaien (tools/planner_sim.py) en uitvoeren wat de
   automation zou doen: *Laden* = laden met vol vermogen uit het net; ontladen_vasthouden = huis
   uit het net; anders nul op de meter (accu levert het verbruik tot de minimale laadstand);
2. optimum met dynamisch programmeren over dezelfde acties (laden / vasthouden / NOM);
3. beide met dezelfde eindwaarde voor de lading die overblijft (goedkoopste prijs / laadrendement);
   daarom eindigen de scenario's om middernacht, vlak voor de goedkope nacht.

Gebruik (vanuit de root van de repo):
    python3 tools/scenario_sim.py <export.json> [scenario ...]      # zonder scenario: alle
    python3 tools/scenario_sim.py <export.json> --lijst

Scenario's staan in SCENARIOS hieronder; eigen scenario's kun je daar toevoegen.
"""
import copy
import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import planner_sim as ps  # noqa: E402

YAML_NL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'Dutch (NL) Integration', 'packages', 'zendure_forecasting.yaml')
TZ = ps.TZ


def prijs_twee(h):
    """Omni-scenario: nacht 0,22, ochtend 07-09 0,48, middag 0,30, avond 17-21 0,45."""
    if h < 7:
        return 0.22
    if h < 9:
        return 0.48
    if h < 17:
        return 0.30
    if h < 21:
        return 0.45
    return 0.30


def last_twee(h):
    if 17 <= h < 23:
        return 1.2
    if 7 <= h < 9:
        return 1.0
    return 0.3


def prijs_drie(h):
    """Drie tarieven: nacht 0,22 tot 07, dag 0,32 tot 17, avond 0,48 tot 22, dan 0,32."""
    if h < 7:
        return 0.22
    if h < 17:
        return 0.32
    if h < 22:
        return 0.48
    return 0.32


def last_drie(h):
    if 17 <= h < 22:
        return 1.5
    if 7 <= h < 17:
        return 0.6
    return 0.3


def prijs_vlak(h):
    return 0.30 + (0.01 if 17 <= h < 21 else 0)


BASIS = dict(cap=5.76, soc_min=10, soc_max=100, rte=85.0, p_max_w=2400,
             slim=True, dal=True, start='2026-11-18T14:30', eind='2026-11-20T00:00')
SCENARIOS = {
    'omni1_60': dict(BASIS, soc=60, prijs=prijs_twee, last=last_twee),
    'omni1_20': dict(BASIS, soc=20, prijs=prijs_twee, last=last_twee),
    'omni1_95': dict(BASIS, soc=95, prijs=prijs_twee, last=last_twee),
    'omni2_slim': dict(BASIS, soc=20, prijs=prijs_drie, last=last_drie,
                       start='2026-11-18T07:00', eind='2026-11-20T00:00'),
    'omni2_zonder_slim': dict(BASIS, soc=20, prijs=prijs_drie, last=last_drie, slim=False,
                              start='2026-11-18T07:00', eind='2026-11-20T00:00'),
    'vlak': dict(BASIS, soc=50, prijs=prijs_vlak, last=last_twee),
}


def iso(dt):
    return dt.isoformat()


def raw_dag(dag, prijs):
    d0 = datetime(dag.year, dag.month, dag.day, tzinfo=TZ)
    return [{'start': iso(d0 + timedelta(minutes=15 * i)), 'end': iso(d0 + timedelta(minutes=15 * (i + 1))),
             'value': prijs(i // 4)} for i in range(96)]


def bouw_export(basis, sc, t, soc, vorig_plan, laden_loopt):
    ex = copy.deepcopy(basis)
    e = ex.get('export', ex)
    inst = e.setdefault('instellingen', {})
    sens = e.setdefault('sensoren', {})
    det = e['details']

    def zet(ent, state, attrs=None):
        det[ent] = {'state': str(state), 'attributes': attrs or {}}
        inst.pop(ent, None)
        sens.pop(ent, None)

    zet('sensor.zendure_2400_ac_totale_capaciteit', sc['cap'])
    zet('sensor.zendure_2400_ac_laadpercentage', round(soc, 2))
    zet('sensor.zendure_2400_ac_minimale_laadpercentage', sc['soc_min'])
    zet('sensor.zendure_2400_ac_maximale_laadpercentage', sc['soc_max'])
    zet('sensor.zendure_2400_ac_rte_totaal', sc['rte'])
    zet('input_number.zendure_2400_ac_max_oplaadvermogen', sc['p_max_w'])
    zet('sensor.zendure_2400_ac_laatste_kalibratie_dagen', 0)
    zet('input_boolean.forecast_slim_vasthouden', 'on' if sc['slim'] else 'off')
    zet('input_boolean.forecast_dal_ontladen_blokkeren', 'on' if sc['dal'] else 'off')
    zet('input_boolean.dynamisch_laden_loopt', 'on' if laden_loopt else 'off')
    zet('input_boolean.zonoverschot_ontladen', 'off')
    zet('input_boolean.negatieve_prijs_vooraf_ontladen', 'off')
    # Geen zon
    for k in list(det) + list((e.get('extern') or {})):
        if 'solcast' in k or 'helios' in k or 'forecast_solar' in k or k.startswith('sensor.energy_'):
            zet(k, 0, {})
    for k in ('input_text.forecast_zon_resterend_vandaag_sensor', 'input_text.forecast_zon_morgen_sensor'):
        zet(k, 'sensor.scenario_zon')
    zet('sensor.scenario_zon', 0, {'unit_of_measurement': 'kWh'})
    # Prijzen
    vandaag = t.date()
    zet('sensor.dynamisch_nordpool', sc['prijs'](t.hour), {
        'raw_today': raw_dag(vandaag, sc['prijs']),
        'raw_tomorrow': raw_dag(vandaag + timedelta(days=1), sc['prijs']) if t.hour >= 13 else [],
    })
    # Verbruiksprofiel: zelfde voor werkdag en weekend, volledig geleerd, geen weekdag-mix
    prof = [sc['last'](h) for h in range(24)]
    oud = det.get('sensor.forecast_verbruiksprofiel', {}).get('attributes', {})
    a = dict(oud)
    a.update({'werkdag': prof, 'weekend': prof, 'n_werkdag': [10] * 24, 'n_weekend': [10] * 24,
              'per_dag': [prof] * 7, 'n_per_dag': [[0] * 24 for _ in range(7)],
              'vorm_werkdag': [], 'vorm_weekend': [], 'n_vorm_werkdag': [], 'n_vorm_weekend': []})
    zet('sensor.forecast_verbruiksprofiel', 'ok', a)
    if vorig_plan is not None:
        det['sensor.zendure_forecast_plan'] = vorig_plan
    e['meta']['export'] = iso(t)
    return ex


def gesloten_lus(basis, sc, yaml_path=YAML_NL, uitvoer=False):
    t = datetime.fromisoformat(sc['start']).replace(tzinfo=TZ)
    eind = datetime.fromisoformat(sc['eind']).replace(tzinfo=TZ)
    eff = (sc['rte'] / 100) ** 0.5
    e_max = sc['cap'] * (sc['soc_max'] - sc['soc_min']) / 100
    E = sc['cap'] * (sc['soc'] - sc['soc_min']) / 100
    kosten, vorig, loopt, starts, laden_kwh = 0.0, None, False, 0, 0.0
    log = []
    while t < eind:
        soc = sc['soc_min'] + E / sc['cap'] * 100
        ex = bouw_export(basis, sc, t, soc, vorig, loopt)
        out, ctx = ps.run(yaml_path, ex, {}, t.strftime('%Y-%m-%dT%H:%M'))
        vorig = {'state': out['state'], 'attributes': {k: v for k, v in out.items() if k != 'state'}}
        p = sc['prijs'](t.hour)
        last = sc['last'](t.hour) / 4
        actie = 'NOM'
        if out['state'] == 'Laden' and E < e_max - 0.001:
            ac = min(sc['p_max_w'] / 1000 / 4, (e_max - E) / eff)
            E += ac * eff
            net = last + ac
            laden_kwh += ac
            if not loopt:
                starts += 1
            loopt, actie = True, 'laden'
        else:
            loopt = False
            if out.get('ontladen_vasthouden') is True:
                net, actie = last, 'vast'
            else:
                dc = min(last / eff, E)
                E -= dc
                net = last - dc * eff
        kosten += net * p
        log.append((t.strftime('%d %H:%M'), round(p, 3), actie, round(soc, 1), round(net, 3)))
        t += timedelta(minutes=15)
    p_eind = min(sc['prijs'](h) for h in range(24)) / eff
    netto = kosten - E * p_eind
    if uitvoer:
        for r in log:
            print(*r)
    return {'kosten': round(kosten, 3), 'eind_kwh': round(E, 3), 'netto': round(netto, 3),
            'laadstarts': starts, 'netladen_kwh': round(laden_kwh, 2), 'log': log}


def optimum(sc, stap=0.005):
    """Dynamisch programmeren over de bruikbare DC-energie; acties laden / vasthouden / NOM.
    Tussen de rasterpunten wordt lineair geïnterpoleerd (anders stapelen afrondingen op)."""
    t0 = datetime.fromisoformat(sc['start']).replace(tzinfo=TZ)
    eind = datetime.fromisoformat(sc['eind']).replace(tzinfo=TZ)
    n = int((eind - t0).total_seconds() // 900)
    eff = (sc['rte'] / 100) ** 0.5
    e_max = sc['cap'] * (sc['soc_max'] - sc['soc_min']) / 100
    N = int(round(e_max / stap))
    stap = e_max / N
    p_eind = min(sc['prijs'](h) for h in range(24)) / eff
    V = [-(i * stap) * p_eind for i in range(N + 1)]

    def waarde(W, E):
        x = min(max(E / stap, 0), N)
        i = min(int(x), N - 1)
        f = x - i
        return W[i] * (1 - f) + W[i + 1] * f

    ac_max = sc['p_max_w'] / 1000 / 4
    for k in range(n - 1, -1, -1):
        t = t0 + timedelta(minutes=15 * k)
        p = sc['prijs'](t.hour)
        last = sc['last'](t.hour) / 4
        W = [0.0] * (N + 1)
        for i in range(N + 1):
            E = i * stap
            best = last * p + V[i]                                   # vasthouden
            dc = min(last / eff, E)
            best = min(best, (last - dc * eff) * p + waarde(V, E - dc))  # nul op de meter
            ac = min(ac_max, (e_max - E) / eff)
            if ac > 1e-6:
                best = min(best, (last + ac) * p + waarde(V, E + ac * eff))  # laden
            W[i] = best
        V = W
    E0 = sc['cap'] * (sc['soc'] - sc['soc_min']) / 100
    return round(waarde(V, E0), 3)


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    if '--lijst' in args:
        print('\n'.join(SCENARIOS))
        return
    basis = json.load(open(args[0], encoding='utf-8'))
    yaml_path = YAML_NL
    if '--yaml' in args:
        i = args.index('--yaml'); yaml_path = args[i + 1]; del args[i:i + 2]
    uitvoer = '--log' in args
    namen = [a for a in args[1:] if not a.startswith('--')] or list(SCENARIOS)
    print('%-20s %8s %8s %8s %7s %7s %7s' % ('scenario', 'plan €', 'optimum', 'verschil', 'starts', 'net kWh', 'eind kWh'))
    for nm in namen:
        sc = SCENARIOS[nm]
        r = gesloten_lus(basis, sc, yaml_path, uitvoer)
        o = optimum(sc)
        print('%-20s %8.3f %8.3f %8.3f %7d %7.2f %7.2f' % (nm, r['netto'], o, r['netto'] - o, r['laadstarts'], r['netladen_kwh'], r['eind_kwh']))


if __name__ == '__main__':
    main()
