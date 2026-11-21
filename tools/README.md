# Tools – planner-simulatie

Hulpmiddelen om de planner (`sensor.zendure_forecast_plan`) buiten Home Assistant door te rekenen met de standen uit een **diagnose-export** (optioneel pakket `zendure_export.yaml` / `zendure_export_global.yaml`). Bedoeld voor ontwikkeling en foutzoeken, niet voor gebruik in Home Assistant. [English below](#english)

Nodig: Python 3.11+ met `jinja2` en `pyyaml` (`pip install jinja2 pyyaml`).

## planner_sim.py

Rekent het plan uit met de YAML van de planner en een export. Met `entity=waarde` overschrijf je een stand, met `--tijd` reken je op een ander moment van de dag. Eerst bouwt hij `sensor.forecast_prijzen` opnieuw op uit de prijzen in de export (zoals Home Assistant elke minuut doet), tenzij je die sensor overschrijft.

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

## scenario_sim.py

Test de planner in een **gesloten lus** op een synthetisch scenario (vaste prijzen per uur, vast verbruik, geen zon, eigen accu) en vergelijkt de uitkomst met het **optimum** (dynamisch programmeren over dezelfde acties: laden / vasthouden / nul op de meter). Een echte export dient alleen als basis voor alle entiteiten. Elk kwartier draait de planner en voert de simulatie uit wat de automation zou doen. Beide krijgen dezelfde eindwaarde voor de lading die overblijft. Scenario's staan in `SCENARIOS` in het script.

```bash
python3 tools/scenario_sim.py export.json                  # alle scenario's
python3 tools/scenario_sim.py export.json omni1_60 --log   # één scenario, met elk kwartier
git show HEAD~1:"Dutch (NL) Integration/packages/zendure_forecasting.yaml" > /tmp/oud.yaml
python3 tools/scenario_sim.py export.json --yaml /tmp/oud.yaml   # oude planner
python3 tools/scenario_sim.py export.json --regels               # regeltests over 54 situaties
```

Kolommen: netto kosten van het plan, van het optimum, het verschil, het aantal laadstarts, kWh uit het net geladen, de lading aan het eind en het aantal kwartieren *Laden* met een volle accu. De lading die overblijft telt mee tegen wat hij minstens uitspaart (goedkoopste prijs × ontlaadrendement).

Met `--regels` draait de planner los over 54 situaties (accu 5,76 / 11,52 kWh, laadstand 10 / 50 / 90%, drie prijsvormen, 07:00 / 14:30 / 22:00) en toetst: (A) 25% meer verbruik boekt nooit minder netladen, (B) geen gekozen laadslot is na verlies duurder dan elke latere prijs, (C) een kwartier later opnieuw plannen met de verwachte laadstand geeft dezelfde laadslots. Daarna (E) 18 situaties om 00:05 met een verouderde prijslijst (Nord Pool nog op gisteren, geen reserve): altijd *Geen prijzen*, nooit laden, terugleveren of vasthouden. Alleen afwijkingen worden getoond. Alleen de NL-planner (de scenario's zetten NL-entiteiten).

## Beperkingen

- De functies van Home Assistant zijn nagebootst. Kleine verschillen met HA zijn mogelijk; vergelijk daarom vooral oud met nieuw.
- `sun.sun` staat niet in de export en wordt grof geschat (Amsterdam, begin november).
- `integration_entities()` en `device_attr()` kunnen niet uit een export: integraties worden herkend aan de naam van de entiteit (bv. `solcast` in de entity_id). Bijgewerkt voor de planner van 2026.11.7.
- Een export van de NL-set werkt alleen met de NL-planner, en een EN-export met de EN-planner (andere entiteitnamen).
- De zon-detailvoorspelling (Solcast) staat pas vanaf Forecasting 2026.11.3 in de export. Zonder die voorspelling rekent de planner met *zonsopkomst + 3 uur* als zon-dekking.
- Een export bevat IP-adressen en serienummers niet, maar wel je instellingen en verbruik: deel hem alleen met wie je vertrouwt.

---

## English

Tools to run the planner (`sensor.zendure_forecast_plan`) outside Home Assistant with the states from a **diagnostics export** (optional package `zendure_export_global.yaml` / `zendure_export.yaml`). Meant for development and troubleshooting, not for use inside Home Assistant.

Requires Python 3.11+ with `jinja2` and `pyyaml`.

- `planner_sim.py <forecasting.yaml> <export.json> [entity=value ...] [--tijd YYYY-MM-DDTHH:MM]` calculates the plan; `entity=value` overrides a state, `--tijd` sets the time of day. It first rebuilds `sensor.forecast_prices` / `sensor.forecast_prijzen` from the prices in the export.
- `vergelijk.py <old.yaml> <new.yaml> <export.json> [entity=value ...] [--varieer entity=v1,v2,...]` compares two planner versions on the same export, optionally for a range of values of one setting.
- `scenario_sim.py <export.json> [scenario ...] [--yaml planner.yaml] [--log]` runs the planner in a closed loop on synthetic scenarios (fixed prices and usage, no solar) and compares the cost with the optimum (dynamic programming over charge / hold / zero on the meter). The export only provides the entities; scenarios are in `SCENARIOS`. NL planner only.

Limitations: Home Assistant functions are emulated (compare old against new rather than trusting absolute values); `sun.sun` is estimated roughly; `integration_entities()` is approximated from entity names; the detailed solar forecast (Solcast) is only in exports from Forecasting 2026.11.3 on; an NL export only works with the NL planner and an EN export with the EN planner.
