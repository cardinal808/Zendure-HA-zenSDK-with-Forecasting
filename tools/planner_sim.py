"""Planner-simulatie: draait sensor.zendure_forecast_plan uit zendure_forecasting.yaml (NL) of
zendure_forecasting_global.yaml (EN) buiten Home Assistant, met de standen uit een diagnose-export
(optioneel pakket zendure_export.yaml). Zie tools/README.md.

  python3 tools/planner_sim.py <forecasting.yaml> <export.json> [entity=waarde ...] [--tijd 2026-11-08T15:06]

Benadering: HA-functies zijn nagebootst (states, state_attr, has_value, now, today_at, as_timestamp,
timestamp_custom, regex-filters, ...). sun.sun wordt grof geschat als hij niet in de export staat
(Amsterdam, begin november). Variabelen worden net als in HA na het renderen omgezet naar getallen,
lijsten en dicts. Afwijkingen ten opzichte van HA zijn mogelijk; vergelijk daarom vooral oud met nieuw.
"""
import sys, json, ast, math, re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import yaml, jinja2

TZ = ZoneInfo('Europe/Amsterdam')


class L(yaml.SafeLoader):
    pass


L.add_multi_constructor('!', lambda l, s, n: None)


class State:
    def __init__(self, eid, state, attrs):
        self.entity_id = eid
        self.domain, self.object_id = eid.split('.', 1)
        self.state = str(state)
        self.attributes = attrs or {}
        self.name = self.attributes.get('friendly_name', eid)
        self.last_changed = NOW

    def __getattr__(self, k):
        raise AttributeError(k)


def load_states(export, overrides):
    e = export.get('export', export)
    st = {}
    for k, v in (e.get('instellingen') or e.get('settings') or {}).items():
        st[k] = (v, {})
    for k, v in (e.get('sensoren') or e.get('sensors') or {}).items():
        val = str(v)
        # "12.3 kWh" -> "12.3"
        m = re.match(r'^(-?[0-9.]+(?:e-?[0-9]+)?) [^ ]+$', val)
        st[k] = (m.group(1) if m else val, {})
    for k, v in list(e['details'].items()) + list((e.get('extern') or e.get('external') or {}).items()):
        a = v.get('attributes') or {}
        a = {k: w for k, w in a.items() if k not in ('(te groot, alleen namen)', '(too large, names only)')}
        st[k] = (v.get('state'), a)
    # Nord Pool-sensor met alleen namen in de export: de lijsten opnieuw opbouwen uit Gielz' sensor, in de
    # vorm die de export meldt (raw_voorbeeld / raw_sample: start als datetime bij de HACS-integratie).
    # Zo rekent de simulatie met dezelfde invoer als Home Assistant (zie 2026.11.10).
    for k, v in (e.get('extern') or e.get('external') or {}).items():
        a = st[k][1]
        vb = a.get('raw_voorbeeld') or a.get('raw_sample') or {}
        if not vb or 'raw_today' in a:
            continue
        g = (st.get('sensor.dynamisch_nordpool') or st.get('sensor.dynamic_nordpool') or (None, {}))[1]
        eerste = vb.get('raw_today_eerste') or vb.get('raw_today_first') or {}
        als_dt = (eerste.get('type_start') or eerste.get('start_type')) == 'datetime'
        def vorm(lst):
            out = []
            for p in lst or []:
                if als_dt:
                    out.append({'start': datetime.fromisoformat(str(p['start'])), 'end': datetime.fromisoformat(str(p['end'])), 'value': p['value']})
                else:
                    out.append(dict(p))
            return out
        st[k] = (st[k][0], dict(a, raw_today=vorm(g.get('raw_today')), raw_tomorrow=vorm(g.get('raw_tomorrow'))))
    for k, v in overrides.items():
        old = st.get(k, (None, {}))
        st[k] = (v, old[1])
    return st


def build_env(st):
    env = jinja2.Environment(extensions=['jinja2.ext.loopcontrols', 'jinja2.ext.do'])

    def states(eid=None, *a, **k):
        if eid is None:
            return None
        s = st.get(eid)
        return 'unknown' if s is None or s[0] is None else str(s[0])

    def state_attr(eid, attr):
        s = st.get(eid)
        return None if s is None else s[1].get(attr)

    def is_state(eid, v):
        x = states(eid)
        return x in v if isinstance(v, (list, tuple)) else x == v

    def is_state_attr(eid, a, v):
        return state_attr(eid, a) == v

    def has_value(eid):
        return eid in st and states(eid) not in ('unknown', 'unavailable', 'None', '')

    def as_timestamp(v, default=None):
        try:
            if isinstance(v, datetime):
                return v.timestamp()
            if isinstance(v, (int, float)):
                return float(v)
            return datetime.fromisoformat(str(v)).timestamp()
        except Exception:
            if default is not None:
                return default
            return None

    def today_at(t='00:00'):
        h, m = [int(x) for x in t.split(':')[:2]]
        return NOW.replace(hour=h, minute=m, second=0, microsecond=0)

    def timestamp_custom(ts, fmt='%Y-%m-%d %H:%M:%S', local=True, default=None):
        try:
            return datetime.fromtimestamp(float(ts), TZ if local else timezone.utc).strftime(fmt)
        except Exception:
            return default if default is not None else ts

    _NO = object()

    def ffloat(v, default=_NO):
        try:
            return float(v)
        except Exception:
            if default is _NO:
                raise ValueError('float: %r' % (v,))
            return default

    def fint(v, default=_NO, base=10):
        try:
            return int(float(v)) if not isinstance(v, str) or re.match(r'^-?[0-9.]+$', v.strip()) else int(v, base)
        except Exception:
            if default is _NO:
                raise ValueError('int: %r' % (v,))
            return default

    def fround(v, precision=0, method='common', default=None):
        try:
            v = float(v)
        except Exception:
            if default is None:
                raise
            return default
        if method == 'ceil':
            r = math.ceil(v * 10 ** precision) / 10 ** precision
        elif method == 'floor':
            r = math.floor(v * 10 ** precision) / 10 ** precision
        else:
            r = round(v, precision)
        return int(r) if precision == 0 and method != 'common' else r

    def regex_match(v, pat, ignorecase=False):
        return bool(re.match(pat, str(v), re.I if ignorecase else 0))

    def regex_search(v, pat, ignorecase=False):
        return bool(re.search(pat, str(v), re.I if ignorecase else 0))

    def regex_replace(v, find='', replace='', ignorecase=False):
        return re.sub(find, replace, str(v), flags=re.I if ignorecase else 0)

    def multiply(v, n):
        return float(v) * n

    def fmin(*a):
        return min(a[0]) if len(a) == 1 else min(a)

    def fmax(*a):
        return max(a[0]) if len(a) == 1 else max(a)

    def expand(*ids):
        out = []
        for i in ids:
            for j in (i if isinstance(i, (list, tuple)) else [i]):
                if j in st:
                    out.append(State(j, st[j][0], st[j][1]))
        return out

    class Dom:
        def __init__(self, d):
            self.d = d

        def __iter__(self):
            return iter([State(k, v[0], v[1]) for k, v in st.items() if k.startswith(self.d + '.')])

        def __getattr__(self, k):
            e = self.d + '.' + k
            return State(e, st[e][0], st[e][1]) if e in st else None

    class States:
        def __getattr__(self, d):
            return Dom(d)

        def __getitem__(self, e):
            if '.' in e:
                return State(e, st[e][0], st[e][1]) if e in st else None
            return Dom(e)

        def __call__(self, e):
            return states(e)

    # Integraties staan niet in de export: benadering via de entity_id (bv. 'solcast' in de naam)
    INT_HINT = {'solcast_solar': 'solcast', 'helios_forecast': 'helios', 'helios': 'helios',
                'forecast_solar': 'energy_production', 'nordpool': 'nordpool', 'homewizard': 'p1_meter'}

    def integration_entities(name):
        hint = INT_HINT.get(name)
        return sorted(k for k in st if hint and hint in k) if hint else []

    def iif(c, t=True, f=False, n=None):
        return n if c is None else (t if c else f)

    g = env.globals
    g.update(integration_entities=integration_entities, device_id=lambda *a, **k: None,
             device_attr=lambda *a, **k: None, area_name=lambda *a, **k: None, iif=iif,
             zip=lambda *a: list(zip(*a)), bool=lambda v, d=None: str(v).lower() in ('1', 'true', 'on', 'yes'))
    g.update(states=States(), state_attr=state_attr, is_state=is_state, is_state_attr=is_state_attr,
             has_value=has_value, as_timestamp=as_timestamp, now=lambda: NOW, today_at=today_at,
             timedelta=timedelta, expand=expand, min=fmin, max=fmax, float=ffloat, int=fint,
             as_datetime=lambda v, d=None: datetime.fromisoformat(str(v)) if v else d,
             as_local=lambda d: d.astimezone(TZ))
    def timestamp_local(ts, default=None):
        try:
            return datetime.fromtimestamp(float(ts), TZ).isoformat()
        except Exception:
            return default if default is not None else ts

    env.filters.update(timestamp_local=timestamp_local)
    env.filters.update(iif=iif, float=ffloat, int=fint, round=fround, timestamp_custom=timestamp_custom,
                       regex_match=regex_match, regex_search=regex_search, regex_replace=regex_replace,
                       multiply=multiply, as_timestamp=as_timestamp, states=states, has_value=has_value,
                       to_json=lambda v, **k: json.dumps(v, default=str),
                       from_json=lambda v: json.loads(v), state_attr=state_attr, is_state=is_state,
                       as_datetime=lambda v, d=None: datetime.fromisoformat(str(v)) if v else d,
                       min=lambda v, attribute=None: min(v), max=lambda v, attribute=None: max(v))
    env.tests.update(match=regex_match, search=regex_search, has_value=has_value,
                     is_state=is_state)
    return env


def parse(r):
    s = r.strip()
    try:
        v = ast.literal_eval(s)
        if isinstance(v, (int, float, list, dict, bool, tuple)) or v is None:
            if isinstance(v, (int, float)) and not isinstance(v, bool) and re.match(r'^0[0-9]', s):
                return s
            return v
    except Exception:
        pass
    return s


class This:
    def __init__(self, state, attrs):
        self.state = state
        self.attributes = attrs


def run(yaml_path, export, overrides, tijd=None):
    global NOW
    e = export.get('export', export)
    NOW = datetime.fromisoformat(tijd).replace(tzinfo=TZ) if tijd else datetime.fromisoformat(e['meta']['export']).astimezone(TZ)
    st = load_states(export, overrides)
    if 'sun.sun' not in st:
        # Amsterdam begin november: op ~07:50, onder ~16:55 (alleen grof, voor de zonsopkomst-terugval)
        d0 = NOW.replace(hour=0, minute=0, second=0, microsecond=0)
        rise = d0.replace(hour=7, minute=52)
        sett = d0.replace(hour=16, minute=55)
        nr = rise if NOW < rise else rise + timedelta(days=1)
        ns_ = sett if NOW < sett else sett + timedelta(days=1)
        st['sun.sun'] = ('above_horizon' if rise <= NOW < sett else 'below_horizon',
                         {'next_rising': nr.isoformat(), 'next_setting': ns_.isoformat()})
    env = build_env(st)
    d = yaml.load(open(yaml_path, encoding='utf-8'), Loader=L)
    # Eerst de prijzensensor (Forecast Prijzen / Forecast Prices) uit de export-invoer opnieuw opbouwen,
    # zoals Home Assistant dat elke minuut doet; daarna de planner. Overrides op die sensor winnen.
    for naam, eid in (('Forecast Prijzen', 'sensor.forecast_prijzen'), ('Forecast Prices', 'sensor.forecast_prices')):
        pb = next((t for t in d['template'] if any(x.get('name') == naam for x in t.get('sensor', []))), None)
        if pb is None or eid in overrides:
            continue
        pc = {}
        for k, v in pb['variables'].items():
            pc[k] = parse(env.from_string(v).render(**pc)) if isinstance(v, str) else v
        ps = next(x for x in pb['sensor'] if x.get('name') == naam)
        st[eid] = (env.from_string(ps['state']).render(**pc).strip(),
                   {k: parse(env.from_string(v).render(**pc)) for k, v in ps['attributes'].items()})
    blok = next(t for t in d['template'] if any(s.get('name') == 'Zendure Forecast Plan' for s in t.get('sensor', [])))
    plan_oud = e['details'].get('sensor.zendure_forecast_plan', {})
    this = This(plan_oud.get('state'), plan_oud.get('attributes', {}))
    ctx = {'this': this}
    for k, v in blok['variables'].items():
        if isinstance(v, str):
            try:
                ctx[k] = parse(env.from_string(v).render(**ctx))
            except Exception as ex:
                raise RuntimeError('variabele %s: %s' % (k, ex))
        else:
            ctx[k] = v
    sensor = next(s for s in blok['sensor'] if s.get('name') == 'Zendure Forecast Plan')
    out = {'state': env.from_string(sensor['state']).render(**ctx).strip()}
    for k, v in sensor.get('attributes', {}).items():
        try:
            out[k] = parse(env.from_string(v).render(**ctx)) if isinstance(v, str) else v
        except Exception as ex:
            out[k] = 'FOUT: %s' % ex
    return out, ctx


if __name__ == '__main__':
    args = [a for a in sys.argv[1:]]
    tijd = None
    if '--tijd' in args:
        i = args.index('--tijd'); tijd = args[i + 1]; del args[i:i + 2]
    y, ex = args[:2]
    ov = dict(a.split('=', 1) for a in args[2:])
    out, ctx = run(y, json.load(open(ex)), ov, tijd)
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str))
