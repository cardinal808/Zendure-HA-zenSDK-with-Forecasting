# Gebruik: [ZONFOUT=0.3] [BETR=0.85] python3 tools/terugrekenen.py <jeroen.nl-prijzen.csv> <HA-history zon-teller.csv> <van> <tot> <accu kWh> <2026|2027> <varianten, bv. A,P,C,AE,AX>
"""Terugrekenen met zon (SolarEdge-teller) en terugleverprijs. Varianten:
  A  = nieuwe planner zoals nu (patroon van vandaag vóór 13:00, zon-overschot zonder waarde in de afweging)
  P  = A met perfecte prijskennis
  B/C = afgezwakt patroon / alleen tot middernacht
  AE = A, maar de afweging kent de terugleverprijs (overschot dat niet past, levert iets op)
  AX = AE + actief terugleveren uit de accu (actie X)
Afrekening altijd: import x all-in - export x terugleverprijs (negatief: niet terugleveren)."""
import sys, csv, numpy as np, datetime as dt, collections
from zoneinfo import ZoneInfo
Z = ZoneInfo('Europe/Amsterdam'); U = dt.timezone.utc
PF, SF, D0, D1, CAP, REGIME = sys.argv[1:7]; CAP = float(CAP)
EB, OPSL, BTW, EB_IN, OPSL_TL = 0.09161, 0.0165, 1.21, 0.11085, 0.022
EFF = 0.921; PMAX = 2.4; PDIS = 2.4; MARGE = 1.10; START = 0.02; K = 41
WD = [0.406,0.556,0.345,0.359,0.25,0.243,0.248,0.491,0.508,0.752,0.709,0.743,0.775,0.75,0.81,0.836,0.621,0.763,0.694,0.719,0.62,0.507,0.616,0.583]
WE = [0.528,0.34,0.509,0.372,0.233,0.23,0.267,0.478,0.512,0.463,0.474,0.641,0.458,0.541,1.007,0.855,0.711,0.816,0.937,0.687,0.601,0.456,0.582,0.573]
buy, feed = {}, {}
for r in csv.reader(open(PF), delimiter=';'):
    if r[0] == 'datum_nl': continue
    t = dt.datetime.fromisoformat(r[1]).replace(tzinfo=U); m = float(r[2].replace(',', '.'))
    buy[t] = (m + EB + OPSL) * BTW
    feed[t] = (m * BTW + EB_IN + OPSL_TL) if REGIME == '2026' else (m + OPSL_TL)
# zon per uur uit de teller
rows = []
for r in csv.DictReader(open(SF)):
    try: rows.append((dt.datetime.fromisoformat(r['last_changed'].replace('Z', '+00:00')), float(r['state'])))
    except ValueError: pass
rows.sort(); pv_h = collections.defaultdict(float)
for (ta, va), (tb, vb) in zip(rows, rows[1:]):
    d = vb - va
    if d <= 0 or d > 40: continue
    hrs = []; h = ta.replace(minute=0, second=0, microsecond=0)
    while h < tb:
        hrs.append(h); h += dt.timedelta(hours=1)
    if (tb - ta).total_seconds() > 3 * 3600 and d > 0.5:
        hrs = [h for h in hrs if 7 <= h.astimezone(Z).hour < 19] or hrs
        for h in hrs: pv_h[h] += d / len(hrs)
    else:  # naar rato van de overlap
        tot = (tb - ta).total_seconds()
        for h in hrs:
            ov = (min(tb, h + dt.timedelta(hours=1)) - max(ta, h)).total_seconds()
            pv_h[h] += d * ov / tot
def pv(t): return pv_h.get(t.replace(minute=0), 0) / 4
import os, random
NOISE = float(os.environ.get('ZONFOUT', '0')); RELIAB = float(os.environ.get('BETR', '1'))
_fac = {}
def fac(t):
    d = t.astimezone(Z).date()
    if d not in _fac:
        r = random.Random(d.toordinal()); _fac[d] = max(0.0, r.gauss(1.0, NOISE)) if NOISE > 0 else 1.0
    return _fac[d]
def pvf(t): return pv(t) * fac(t) * RELIAB
def load(t):
    tl = t.astimezone(Z); return (WE if tl.weekday() >= 5 else WD)[tl.hour] / 4
grid = np.linspace(0, CAP, K)
def ip(x, V): return np.interp(np.clip(x, 0, CAP), grid, V)

def step(s, a, ll, pvq, p, f, fdec, charging):
    """Eén kwartier: geeft (nieuwe stand, kosten afrekening, kosten afweging)."""
    d = np.minimum(pvq, ll); r = ll - d; o = pvq - d
    s1 = np.minimum(s + o * EFF, CAP); spill = o - (s1 - s) / EFF
    imp, exp, xexp = r, spill, 0
    if a == 'N':
        out = np.minimum(np.minimum(r, s1 * EFF), PDIS / 4); s2 = s1 - out / EFF; imp = r - out
    elif a == 'L':
        add = np.minimum(PMAX / 4 * EFF, CAP - s1); s2 = s1 + add; imp = r + add / EFF
    elif a == 'X':
        out = np.minimum(s1 * EFF, PDIS / 4); h = np.minimum(r, out); s2 = s1 - out / EFF; imp = r - h; xexp = out - h
    else:
        s2 = s1
    fpos = max(f, 0)
    # zon-overschot wordt bij een negatieve terugleverprijs afgeregeld (0); terugleveren uit de accu kost dan geld
    real = imp * p - exp * fpos - xexp * f
    dec = imp * p - exp * (max(fdec, 0)) - xexp * fdec
    return s2, real, dec

def plan(ts, ps, fs, s0, charging, mode):
    n = len(ps); endv = max(min(ps), 0) * EFF
    acts = ['H', 'N', 'L'] + (['X'] if mode == 'AX' else [])
    V0 = -grid * endv; V1 = V0.copy(); W = [None] * (n + 1); W[n] = (V0, V1)
    for i in range(n - 1, -1, -1):
        ll = load(ts[i]) * MARGE; pq = pvf(ts[i]); fdec = fs[i] if mode in ('AE', 'AX') else 0
        best0 = np.full(K, np.inf); best1 = np.full(K, np.inf)
        for a in acts:
            s2, _, c = step(grid, a, ll, pq, ps[i], fs[i], fdec, False)
            if a == 'L':
                valid = s2 > grid + 0.001
                c1 = np.where(valid, c + ip(s2, V1), np.inf)
                best0 = np.minimum(best0, c1 + START); best1 = np.minimum(best1, c1)
            else:
                c0 = c + ip(s2, V0); best0 = np.minimum(best0, c0); best1 = np.minimum(best1, c0)
        V0, V1 = best0, best1; W[i] = (V0, V1)
    v0, v1 = W[1]; ll = load(ts[0]) * MARGE; pq = pvf(ts[0]); fdec = fs[0] if mode in ('AE', 'AX') else 0
    best = (None, np.inf)
    for a in acts:
        s2, _, c = step(np.array([s0]), a, ll, pq, ps[0], fs[0], fdec, charging)
        if a == 'L':
            if s2[0] <= s0 + 0.001: continue
            c = c + ip(s2, v1) + (0 if charging else START)
        else:
            c = c + ip(s2, v0)
        if c[0] < best[1] - 1e-5: best = (a, c[0])
    return best[0]

def horizon(t, variant):
    tl = t.astimezone(Z); dl = tl.replace(hour=0, minute=0)
    day = dl.astimezone(U); tom = (dl + dt.timedelta(days=1)).replace(hour=0).astimezone(U); end = (dl + dt.timedelta(days=2)).replace(hour=0).astimezone(U)
    known = tl.hour >= 13 or variant == 'P'
    ts, ps, fs = [], [], []; u = t
    td = [buy[x] for x in buy if day <= x < tom]; mu = sum(td) / len(td)
    while u < end:
        if u < tom or known:
            if u not in buy: break
            ts.append(u); ps.append(buy[u]); fs.append(feed[u])
        elif variant in ('A', 'B', 'AE', 'AX'):
            same = u - dt.timedelta(days=1)
            if same not in buy: break
            pb, pf = buy[same], feed[same]
            if variant == 'B': pb = mu + 0.5 * (pb - mu)
            ts.append(u); ps.append(pb); fs.append(pf)
        else: break
        u += dt.timedelta(minutes=15)
    return ts, ps, fs

def run(variant):
    t = dt.datetime.fromisoformat(D0).replace(tzinfo=Z).astimezone(U); tend = dt.datetime.fromisoformat(D1).replace(tzinfo=Z).astimezone(U)
    s = CAP * 0.5; cost = 0; charging = False; starts = 0; imp_e = exp_e = 0
    mode = variant if variant in ('AE', 'AX') else 'A'
    while t < tend:
        ts, ps, fs = horizon(t, variant)
        a = plan(ts, ps, fs, s, charging, mode)
        s2, real, _ = step(np.array([s]), a, load(t), pv(t), buy[t], feed[t], 0, charging)
        if a == 'L' and not charging: starts += 1
        charging = a == 'L'; s = float(s2[0]); cost += float(real[0])
        t += dt.timedelta(minutes=15)
    return cost, s, starts

for v in sys.argv[7].split(','):
    c, s, st = run(v)
    print('%-3s cap %.1f regime %s %s..%s: netto €%.2f, eindstand %.2f kWh, gecorrigeerd €%.2f, laadstarts %d' % (v, CAP, REGIME, D0, D1, c, s, c - s * EFF * 0.22, st), flush=True)
