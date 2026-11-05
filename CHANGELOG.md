# Changelog – Forecasting (EN)

Versions follow `year.month.sequence`; the sequence restarts at 1 every month. Each version states which Gielz version it is based on. [Nederlands](CHANGELOG.nl.md)

## 2026.11.3 — based on Gielz v20261007

**New: electric car** (optional)
- New package `packages/zendure_ev_global.yaml` and a **Configuration (EV)** block on the Settings tab. For a charger without its own control (granny charger, or a wallbox behind a smart switch) with a power measurement, e.g. a Shelly 1PM or Pro 1PM in the charger's circuit.
- **No battery discharge into the car:** the Smart Matching discharge blocks subtract the car's charging power (`sensor.ev_discharge_correction`, above a threshold of 300 W by default) from the grid meter. The battery then only supplies the house; the car charges from the grid or the sun. Always applies, also without a charging session.
- **Planner:** the car's charging no longer counts in the usage profile (per hour and per quarter), the average daily usage and the solar self-consumption. A charging day does not skew the battery forecast.
- **Charging session** (with a configured switch): choose the charge moment and the required kWh. *Night (cheapest hours)* only turns the charger on in the cheapest price slots until *Ready by* (tomorrow's prices unknown: today's pattern, replanned around 14:00). *Daytime (solar)* charges while the sun is up; the planner subtracts those kWh from the solar surplus for the battery and charges the shortfall from the grid at the cheapest moment. Done or time passed: charge moment back to Off and the charger on again.

**HVAC now in the public set** (optional)
- `packages/zendure_hvac_global.yaml` (and `zendure_hvac.yaml`) is now part of the public set: no discharging while the AC runs. There is no separate complete set any more.
- The automation checks the AC with a template, so everything keeps working without the HVAC package.

**Dashboard**
- **Optional packages show themselves:** Configuration (EV), (HVAC), (Negative Price) and (Savings) are only on the Settings tab when the package is loaded.
- **Plan Timeline** back in the first column below PV, as one card (`custom:mod-card`, needs card-mod), without the separate colour line below it.
- Plan for today: a line about the kWh the car still asks from the sun during the day.
- `sensor.forecasting_version`: attribute `packages` (which optional packages are active) replaces `set`.

**Upgrading**
- Replace all files and **restart** Home Assistant.
- Optional: put `zendure_ev_global.yaml` and/or `zendure_hvac_global.yaml` (Global) or `zendure_ev.yaml` and/or `zendure_hvac.yaml` (NL) in the `packages` folder.
- First test whether your car resumes charging when power returns, before letting the charger be switched.

## 2026.11.2 — based on Gielz v20261007

**New: no export at a negative price** (optional)
- New package `packages/zendure_negative_price_global.yaml` and a **Configuration (Negative Price)** block on the Settings tab. Feed-in price per quarter hour = market price + bonus % (only when the market price is positive) + feed-in markup, using the tariffs from Configuration (Savings) (`sensor.zendure_feedin_price_now`).
- When it is negative, the module turns on Gielz' **PV Export Disabled** and back off afterwards. Charging from solar and discharging to the house keep working.
- **External inverters (0, 1 or 2):** *Production limit* (SolarEdge, OpenDTU/Hoymiles, APsystems, Fronius) regulates every 10 s on the grid meter, only when the Zendure cannot absorb the surplus; *Export limit* (GoodWe, Growatt) goes to 0; a `switch.*` is turned off, a `script.*` gets `block: true/false`. A second inverter goes fully to its minimum. Everything is restored as it was.

**Planner**
- **Usage per quarter hour:** the usage profile now also learns how usage is spread over the four quarters within each hour (workday and weekend separately, learning slowly). The planner uses that shape for solar coverage, *battery empty*, the path check, smart hold, tomorrow's estimate and the timeline; the total per hour and the energy balance do not change. While the shape has few measurements, it calculates evenly spread as before. New attributes `usage_per_quarter_source` and `shape_quarter_share_pct`; the profile sensor now measures every quarter hour.
- **Smart hold:** if the battery will not last until the end of the gap and no charge moment is left, it keeps its charge for the most expensive quarter hours (via *Hold discharging in a cheap dip*).
- **Charge margin in the path check:** the battery counts as empty once only the margin is left, and if the battery holds less than the margin, the shortfall is charged before the expensive quarter hours (when worthwhile).
- **Usage profile while learning:** hours with too few measurements blend the measurements there are with the day average, so a clear evening peak already counts.

**Dashboard**
- *Tomorrow's grid charge estimate* mentions that the charge margin is not included yet.
- *Collected data*: line *Usage per quarter*.
- Savings tab: *work-in-progress* notice.

**Upgrading**
- Replace all files and **restart** Home Assistant (new input fields and a sensor that now measures every quarter hour).
- Optional: put `zendure_negative_price_global.yaml` (Global) or `zendure_negatieve_prijs.yaml` (NL) in the `packages` folder and turn on the switch in **Configuration (Negative Price)**. The block is below Configuration (PV) and shows when *Show PV on dashboard* is on.
- The usage per quarter learns by itself; during the first weeks the planner calculates as before.

## 2026.11.1 — based on Gielz v20261007

**New: Savings**
- New package `packages/zendure_savings_global.yaml` and a **Savings** tab. Every quarter hour your usage is settled at a fixed tariff and at the dynamic price of that moment, in six situations (no solar or battery, solar only, solar + battery; each fixed and dynamic).
- Tiles *Today, This month, This year, Total*, an overview of where the savings come from (solar, dynamic tariff, battery and smart charging), cost per situation, charts per day and per month, and the **battery payback time**.
- Input fields in **Configuration (Savings)**: fixed tariffs, markup and bonus for dynamic, the battery purchase price and what it had already earned back.
- The tables are styled with [card-mod](https://github.com/thomasloven/lovelace-card-mod) if installed; without card-mod everything works, just with simpler styling.

**Planner**
- **Path check** stopped at the first planned charge slot, so expensive quarter hours later in the evening were missed. It now looks from *battery empty* until solar covers usage or until the end of the bridge.
- **Dip hold in the path check:** with *hold discharging in a cheap dip* on, the path check assumes the battery supplies nothing in those dips (dip determined per day).
- **Tomorrow's estimate** follows the same rules as the path check: which expensive quarter hours the battery covers, what the house buys directly from the grid and which charge slots that needs. New attributes `tomorrow_from_battery_kwh`, `tomorrow_direct_grid_kwh`, `tomorrow_grid_charge_balance_kwh`, `tomorrow_expensive_quarters_kwh`; `tomorrow_charge_moments` now also has `minutes` and `kwh`.
- **Charge blocks:** new attribute `charge_blocks` (day, start, end, minutes, kWh, average price) and `planned_grid_charge_kwh`.
- The counters for import, export, solar and battery now freeze every quarter hour (was every hour), needed for the savings per quarter hour.

**Dashboard**
- Plain-language plan and the *Today* and *Tomorrow* blocks rewritten: per charge block when, how long, how many kWh and at what price; clear what comes from the battery and what directly from the grid; *Bridge until* is now *Today's plan runs until*.
- **Plan Timeline:** price colours as in Gielz (green = planned charging, red = Gielz's most expensive periods, grey = other).
- *Forecast Settings* tiles removed; *Usage Profile* moved to section 2 (Import | Export); *Collected data* is its own card.

**Upgrading**
- Replace all files and add `zendure_savings_global.yaml` (Global) or `zendure_besparing.yaml` (NL) to the `packages` folder. **Restart** Home Assistant (new input fields).
- Then enter your tariffs and the battery price under **Configuration (Savings)**. Savings are counted from that moment.

## 2026.10.2 — based on Gielz v20261007

**Planner**
- **Usage profile:** workdays remember longer (weight per new measurement 0.2 → 0.1, memory about 2 weeks), so a single unusual day has less effect; weekend unchanged (weight 0.2, about 2.5 weeks).
- **Tomorrow's charging moments** as new attribute `tomorrow_charge_moments`: the indicative charge slots of tomorrow, adjacent quarters merged into blocks with their average price.

**Dashboard**
- *Tomorrow* block: the charging moments are shown after *Estimated grid charge tomorrow*.
- *Today* block: *Charge margin* line removed (it is a setting, see Forecast Settings).
- *Collected data (last 7 days)*: *Charge power: configured … measured …* line removed.

**Upgrading**
- Replace all files (only `zendure_forecasting_global.yaml` and the dashboard changed in content, the others only in version number); then reload **Automations** and **Template entities** (Developer tools → YAML). No restart needed.

## 2026.10.1 — based on Gielz v20261007

First numbered version. Replaces reference `FC-20261027` and contains all changes since then.

**Planner**
- **Path check:** calculates when the battery runs empty and until when (first charge slot, solar covering usage from the Solcast detailed forecast, or end of the bridge). Charge slots are only planned before the expensive slot they replace, and only if they are cheaper after round-trip loss. Also works when nothing else needs to be charged.
- **Usage profile per hour**, separately for workdays and weekends (`sensor.forecast_usage_profile`), used for the bridge, battery empty, solar coverage and the path check.
- **Efficiency from the total RTE** (energy balance of the battery), split equally over charging and discharging. The 24-hour point measurements came out too low.
- **Grid import and export from the P1 meter** (detected automatically: SlimmeLezer/ESPHome DSMR, HomeWizard P1, DSMR integration), just like the energy dashboard. Without a meter calculated from power. All integration sensors from `trapezoidal` to `left`.
- **Solar self-consumption and daily usage from day 1** calculated from your own measurements; input fields *Solar self-consumption (override)* and *Default daily usage* removed.

**Dashboard**
- **Plain-language plan** at the top of the plan, and a clearer path check line.
- **Plan Timeline:** 36 hours ahead per price slot in four rows (price, solar and usage, battery and state of charge, grid), with a compact tooltip.
- Configuration (Forecasting) cleaned up (measured grid charge power and the dip status row removed); source of grid data and efficiency under Collected data.
- **Versioning:** `sensor.forecasting_version`, `sensor.forecasting_release_check` and the release notes of this extension in the dashboard.

**Upgrading**
- Replace all files and **restart** Home Assistant (the new integration method, removed input fields and the GitHub sensor need a restart).
- The 7-day figures move over to the new P1 meter source within a week.
