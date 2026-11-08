# Tools – planner-simulatie

Hulpmiddelen om de planner (`sensor.zendure_forecast_plan`) buiten Home Assistant door te rekenen met de standen uit een **diagnose-export** (optioneel pakket `zendure_export.yaml` / `zendure_export_global.yaml`). Bedoeld voor ontwikkeling en foutzoeken, niet voor gebruik in Home Assistant. [English below](#english)

Nodig: Python 3.11+ met `jinja2` en `pyyaml` (`pip install jinja2 pyyaml`).

## planner_sim.py

Rekent het plan uit met de YAML van de planner en een export. Met `entity=waarde` overschrijf je een stand, met `--tijd` reken je op een ander moment van de dag.

```bash
python3 tools/planner_sim.py "Dutch (NL) Integration/packages/zendure_forecasting.yaml" export.json
python3 tools/planner_sim.py "Dutch (NL) Integration/packages/zendure_forecasting.yaml" export.json \
    sensor.zendure_2400_ac_laadpercentage=10 input_number.dynamisch_minimale_spread=25 --tijd 2026-11-08T13:30
```

## vergelijk.py

Zet twee versies van de planner naast elkaar op dezelfde export, eventueel voor een reeks waarden van één instelling. Handig om na een wijziging te zien wat er verandert.

```bash
git show HEAD~1:"Dutch (NL) Integration/packages/zendure_forecasting.yaml" > /tmp/oud.yaml
python3 tools/vergelijk.py /tmp/oud.yaml "Dutch (NL) Integration/packages/zendure_forecasting.yaml" export.json \
    sensor.zendure_2400_ac_laadpercentage=10 --varieer input_number.dynamisch_minimale_spread=0,3,25
```

## Beperkingen

- De functies van Home Assistant zijn nagebootst. Kleine verschillen met HA zijn mogelijk; vergelijk daarom vooral oud met nieuw.
- `sun.sun` staat niet in de export en wordt grof geschat (Amsterdam, begin november).
- De zon-detailvoorspelling (Solcast) staat pas vanaf Forecasting 2026.11.3 in de export. Zonder die voorspelling rekent de planner met *zonsopkomst + 3 uur* als zon-dekking.
- Een export bevat IP-adressen en serienummers niet, maar wel je instellingen en verbruik: deel hem alleen met wie je vertrouwt.

---

## English

Tools to run the planner (`sensor.zendure_forecast_plan`) outside Home Assistant with the states from a **diagnostics export** (optional package `zendure_export_global.yaml` / `zendure_export.yaml`). Meant for development and troubleshooting, not for use inside Home Assistant.

Requires Python 3.11+ with `jinja2` and `pyyaml`.

- `planner_sim.py <forecasting.yaml> <export.json> [entity=value ...] [--tijd YYYY-MM-DDTHH:MM]` calculates the plan; `entity=value` overrides a state, `--tijd` sets the time of day.
- `vergelijk.py <old.yaml> <new.yaml> <export.json> [entity=value ...] [--varieer entity=v1,v2,...]` compares two planner versions on the same export, optionally for a range of values of one setting.

Limitations: Home Assistant functions are emulated (compare old against new rather than trusting absolute values); `sun.sun` is estimated roughly; the detailed solar forecast (Solcast) is only in exports from Forecasting 2026.11.3 on.
