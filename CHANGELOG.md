# Changelog – Forecasting (EN)

Versions follow `year.month.sequence`; the sequence restarts at 1 every month. Each version states which Gielz version it is based on. [Nederlands](CHANGELOG.nl.md)

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
