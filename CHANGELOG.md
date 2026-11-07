# Changelog – Forecasting (EN)

Versions follow `year.month.sequence`; the sequence restarts at 1 every month. Each version states which Gielz version it is based on. [Nederlands](CHANGELOG.nl.md)

## 2026.11.3 — based on Gielz v20261007

**New: electric car** *(optional package)*
- New package `packages/zendure_ev_global.yaml` and a **Configuration (EV)** block on the Settings tab. For a charger without its own control (granny charger, or a wallbox behind a smart switch) with a power measurement, e.g. a Shelly 1PM or Pro 1PM in the charger's circuit.
- **No battery discharge into the car:** the Smart Matching discharge blocks subtract the car's charging power (`sensor.ev_discharge_correction`, above a threshold of 300 W by default) from the grid meter. The battery then only supplies the house; the car charges from the grid or the sun. Always applies, also without a charging session.
- **Planner:** the car's charging no longer counts in the usage profile (per hour and per quarter), the average daily usage and the solar self-consumption. A charging day does not skew the battery forecast.
- **Charging session** (with a configured switch): choose the charge moment and the required kWh. *Night (cheapest hours)* only turns the charger on in the cheapest price slots until *Ready by* (tomorrow's prices unknown: today's pattern, replanned around 14:00). *Daytime (solar)* charges while the sun is up; the planner subtracts those kWh from the solar surplus for the battery and charges the shortfall from the grid at the cheapest moment. Done or time passed: charge moment back to Off and the charger on again.

**HVAC now in the public set** *(optional package)*
- `packages/zendure_hvac_global.yaml` (and `zendure_hvac.yaml`) is now part of the public set: no discharging while the AC runs. There is no separate complete set any more.
- The automation checks the AC with a template, so everything keeps working without the HVAC package.
- **Settings per mode instead of per hour:** the *Charge only from/until* times are gone. New `sensor.hvac_mode` (Off, Standby, Heating, Cooling, Drying, Fan, Auto) from the climate entity's mode and `hvac_action`. Per mode you choose whether discharging is still allowed, e.g. Cooling on (summer, plenty of sun) and Heating off (winter, no sun). By default every mode is blocked.
- **Standby does not count:** when the AC has reached its temperature (`hvac_action` idle), the battery discharges as usual.
- `binary_sensor.hvac_discharge_blocked` has a `reason` attribute, also shown in Forecasting Configuration (HVAC).
- **New: approach *AC not from battery*** (list **Approach**, `input_select.hvac_approach`). When the AC may not run from the battery in the current mode (`binary_sensor.hvac_not_from_battery`), you choose what happens: *No discharging* (default, as before: discharging stops completely) or *AC not from battery*: the Smart Matching discharge blocks subtract the AC power from the grid meter, as for the car (`sensor.hvac_discharge_correction`). The battery then keeps supplying the rest of the house. Needs a power measurement: new field **Power sensor** (`input_text.hvac_power_sensor`, W or kW, e.g. a Shelly; empty = the HVAC sensor if that is a power sensor). Without it, *No discharging* applies.
- **New: count AC usage separately.** While the AC may not run from the battery, its usage does not count in the usage profile (per hour and per quarter), the average daily usage and the solar self-consumption, like the car (`sensor.hvac_separate_total`, `..._from_solar_total` and the 7-day figures; power measurement only, in both approaches). The *Reset usage data* button also clears these counters.
- **Fixed:** a power sensor in kW as HVAC sensor was not converted, so the AC stayed below the threshold and counted as *Off*.

**Negative price**
- New switch **Disable Zendure Pro PV export** (`input_boolean.negative_price_zendure_pv_export`): choose whether, at a negative price, the feature also disables the PV export of the Zendure Pro (solar inputs) via Gielz' *PV Export Disabled*. Turns on by itself as soon as you switch on *No export*; off = only limit the external inverters, e.g. with a Zendure without solar panels.
- The settings for the Zendure Pro and the external inverter are now together in one card.
- **Feed-in markup and bonus** (`input_number.savings_setting_dynamic_feedin_markup`, `..._bonus`) now live in `zendure_negative_price_global.yaml` instead of the optional savings package, so the feed-in price is right without that package too. Same entities: configured values are kept. On the dashboard they are in Forecasting Configuration (Savings), or in (Negative Price) when the savings package is missing.
- **New: pre-discharge** (switch *Pre-discharge*, mode Dynamic Smart Matching + Forecasting, needs a detailed solar forecast such as Solcast). If a window with a negative feed-in price and expected solar surplus is coming, the planner makes sure the battery is empty enough at its start for 75% of that surplus. You set that percentage with **Solar credit** (`input_number.negative_price_pre_discharge_solar_credit`, 0 = 75%): higher = discharge deeper and more room for solar, lower = more careful with an optimistic forecast. More solar then fits into the battery and the inverter needs to throttle less.
  - For this the battery only discharges for the house (no export), in the most expensive quarter hours before the window: the hold (cheap dip, smart hold) is lifted there. If it cannot reach the target even discharging everywhere, it discharges in all quarter hours.
  - Grid charging before the window only stays when it fits within the room (cheapest slots first), e.g. charging at night for an expensive morning peak.
  - If solar fills the battery again before the window anyway, it does nothing. Min. SOC always stays. Feed-in markup and bonus count in the feed-in price.
  - *Plan for today* explains what it does; new attributes `pre_discharge`, `pre_discharge_now`, `pre_discharge_window_start`/`_end`, `pre_discharge_solar_surplus_kwh`, `pre_discharge_target_kwh`, `pre_discharge_expected_kwh`, `pre_discharge_price_limit`, `pre_discharge_solar_credit_pct` and `pre_discharge_grid_dropped`.

**New: diagnostics export** *(optional package)*
- New package `packages/zendure_export_global.yaml` and a **Diagnostics export** block on the Settings tab. *Download export* saves one JSON file directly on your own device, with versions, active packages, all settings, the state of all sensors, the planner details, the collected data (all counters and 7-day statistics with their attributes), the external sensors you entered and the state of the Zendure automations. Nothing is stored in Home Assistant: `script.zendure_diagnostics_export` returns the export as its response and the browser turns it into a file.
- The button needs [button-card](https://github.com/custom-cards/button-card) (HACS); only this block uses it. Without button-card, or if downloading does not work in the app: Developer tools → Actions → *Zendure Diagnostics Export* → Perform action, and copy the response.
- The package also collects three logs: every line the automation writes to the logbook (last 50), a snapshot of mode, SOC, grid meter, power, price and plan every quarter hour (last 24 hours) and warnings and errors from the HA log that concern this set (last 20). For this the package turns on `system_log: fire_event: true`.
- IP addresses and serial numbers are left out. The automation does not need any changes.

**New: reset usage data**
- Button **Reset usage data** in Forecasting Configuration (Basic), with a confirmation dialog. Clears the learned usage profile (per hour and per quarter) and the 7-day history (solar production, grid, battery, average usage, self-consumption; also the car if the EV package is loaded). The planner then first uses start values and learns everything again. The savings and the measured charge power are kept.
- Works via `input_button.forecast_reset_usage_data`: the profile resets itself, a new automation clears the counter history (`recorder.purge_entities`) and reloads the statistics (`statistics.reload`).

**Solar production: no more jumps**
- `sensor.forecast_counter_solar_production` now adds up the increase of your production sensor instead of copying its value, like the grid counters. Entering another sensor, a counter that briefly reports 0 or jumps back, or a replaced inverter no longer counts as production. This could make the 7-day solar production (and so the average daily usage) far too high. An ignored jump is shown in the attribute `last_jump`.
- Right after a reset (no history yet) the planner no longer assumes 7 days of history but uses the start values.

**Grid meter: enter your own kWh counters**
- Two new input fields in Forecasting Configuration (Basic): **Grid import counter** and **Grid export counter** (`input_text.forecast_setting_grid_import_counter_sensor` / `..._export_...`). For meters that are not detected automatically, e.g. a Shelly Pro 3EM (current clamps), P1 Monitor or DSMR Reader. Several sensors separated by a comma are added up (e.g. tariff 1 and 2); Wh and MWh are converted. Empty = detect automatically as before (SlimmeLezer, HomeWizard, DSMR integration).
- Without a detected or entered counter the set calculates import and export from power. That is less accurate; *Collected data* then shows *Calculated from power (no kWh counter found or entered)*.
- Switching source (automatic ↔ entered, or another sensor) does not cause a jump in the grid counters: the new attribute `meter_sensors` remembers which sensors supplied the reading.

**Planner: path check looks beyond the night**
- As soon as tomorrow's prices are known (around 14:00), the path check no longer looks only until the start of tomorrow's cheap hours (e.g. 00:45), but until tomorrow's solar covers usage. An expensive morning peak therefore already counts in the afternoon: if charging now (after charge and discharge loss) is cheaper than buying in that peak and cheaper than charging at night, it charges now. If the night is cheaper, it plans the night.
- If tomorrow's solar does not cover usage (winter), it looks until sunrise + 3 hours: this is about the morning peak, not tomorrow evening. Without a detailed forecast (e.g. Forecast.Solar), sunrise + 3 hours counts as solar coverage.
- When looking ahead, today's solar counts for the moment the battery runs empty (direct use and surplus into the battery).
- The energy balance (bridge, scenario A/B) does not change; after midnight and while tomorrow's prices are unknown, the planner calculates exactly as before. The efficiency filter and minimal spread also apply here.
- New attributes `pathcheck_horizon`, `pathcheck_beyond_night` and `pathcheck_solar_covers_tomorrow_from`; *Plan today* shows *beyond the night*.

**Dashboard**
- **Optional packages show themselves:** Forecasting Configuration (Savings), (EV), (HVAC) and Diagnostics export are only on the Settings tab when the package is loaded. Without `zendure_savings_global.yaml` the Savings tab only shows a notice instead of empty cards.
- New **Optional packages** card on the Settings tab: per optional package whether it is loaded (✅/➖), the file and what it does, with a link to the explanation.
- **Plan Timeline** back in the first column below PV, as one card (`custom:mod-card`, needs card-mod), without the separate colour line below it.
- Plan for today: a line about the kWh the car still asks from the sun during the day.
- `sensor.forecasting_version`: attribute `packages` (which optional packages are active) replaces `set`.

**Clearer what is optional**
- Required are `zendure_gielz1986_global.yaml`, `zendure_forecasting_global.yaml` and `zendure_negative_price_global.yaml`. Optional are `zendure_savings_global.yaml`, `zendure_ev_global.yaml`, `zendure_hvac_global.yaml` and `zendure_export_global.yaml`.
- The README has a **Packages** table: per file required or optional, what it does, what it needs and what you miss without it.
- Every package has, right below the version header, the line `# OPTIONAL PACKAGE` (with what it needs) or `# REQUIRED PACKAGE`.

**Fixed**
- **Solar production always *unavailable*:** the new solar counter missed two variables, so `sensor.forecast_counter_solar_production` was unavailable, the 7-day solar production stayed empty and the planner used start values (*History available: 0 of 7 days*). Fixed. After a restart at night without a reading, the counter waits until the inverter reports a value, and the first time it starts at the inverter reading (matching the old data points).
- **History:** the planner now takes the largest coverage of solar production, grid import and battery charging. Without solar panels, or when the solar counter is briefly missing, the history of the other counters counts.
- **Battery empty on the dashboard** (Plan for today and the path-check line) now takes solar, smart hold and pre-discharge into account, like the plan itself. Before it could say "empty at 21:20" while the battery was being saved for the morning peak. The plan itself does not change.
- **Diagnostics export:** configured fields with several sensors (comma list, e.g. own grid counters) are now listed with the external sensors too.

**Upgrading**
- Replace all files and **restart** Home Assistant.
- Always replace `zendure_savings_global.yaml` and `zendure_negative_price_global.yaml` together: if old and new versions are mixed, feed-in markup and bonus are defined twice and Home Assistant rejects the configuration.
- If `zendure_negative_price_global.yaml` is not yet in your `packages` folder, add it: it is now part of the base. The feature only acts once you turn on *No export at negative price*.
- `zendure_savings_global.yaml` is optional: if you do not want the Savings tab you can remove it. Feed-in markup and bonus are now in `zendure_negative_price_global.yaml` and keep working; without the savings package you enter them in Forecasting Configuration (Negative Price).
- Optional: put `zendure_ev_global.yaml`, `zendure_hvac_global.yaml` and/or `zendure_export_global.yaml` (Global) or `zendure_ev.yaml`, `zendure_hvac.yaml` and/or `zendure_export.yaml` (NL) in the `packages` folder. If you already have `system_log:` in `configuration.yaml`, remove the `system_log` block from the export package and set `fire_event: true` there.
- If you use *No export at negative price*: **Disable Zendure Pro PV export** turns on by itself once after the restart. Turn it off if your Zendure has no solar panels.
- Optional: turn on **Pre-discharge** in Forecasting Configuration (Negative Price) (off by default).
- HVAC: after the update the approach *No discharging* applies (as before). If you want the battery to keep supplying the house while the AC runs, enter a **Power sensor** and choose *AC not from battery*.
- First test whether your car resumes charging when power returns, before letting the charger be switched.
- If your 7-day solar production or average usage is too high because of an earlier jump: press **Reset usage data** once after the update.
- If *Collected data → Grid* says "Calculated from power", enter your own grid counters in Forecasting Configuration (Basic).

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
