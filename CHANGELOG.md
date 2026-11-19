# Changelog – Forecasting (EN)

Versions follow `year.month.sequence`; the sequence restarts at 1 every month. Each version states which Gielz version it is based on. [Nederlands](CHANGELOG.nl.md)

## 2026.11.8 — based on Gielz v20261113

**In short:** a new planner (on by default) that makes the cheapest choice per quarter hour over today and tomorrow, with the current planner as fallback; optional export from the battery; a required Recorder package; an optional Quooker package; price backup when Nord Pool fails.

**New required package: Recorder (`zendure_recorder_global.yaml`)**
- Does not record frequently updating entities of the set: the Gielz automation, powers and indications without a chart, the chart data (> 16 kB), helper sensors (price backup, sensor candidates, notices), the sources of the kWh counters and the logs of the Export package. The sensors keep working; only their history is dropped.
- Deliberately not excluded: what is shown in a chart (Zendure power, the three PV powers) and the sources of averages, counters and statistics.
- Works next to your own `recorder:` in configuration.yaml (Home Assistant merges the lists); do not put single keys such as `purge_keep_days` in the package.

**New optional package: Quooker (`zendure_quooker_global.yaml`)**
- Short, high peaks from e.g. a boiling-water tap such as a Quooker (reheating, also at night every few hours ~2.2 kW), kettle or induction hob come from the grid instead of the battery. Without this package the battery follows every peak in the Smart Matching modes: ramping up and down, frequent relay switching and, because of the control delay, a brief export after the peak.
- Enter one or more **power sensors**, separated by commas (W, kW or A; A × 230 V). Above the **threshold** (default 1000 W) `sensor.zendure_quooker_discharge_correction` is the summed power; the Smart Matching discharge blocks subtract it from the grid meter, just like the car and the air conditioner. Charging from solar is unchanged: the peak then comes off the charging power.
- Automation (EN and NL): the 6 calculations with the EV and HVAC correction also subtract `sensor.zendure_quooker_discharge_correction` / `sensor.zendure_quooker_ontlaad_correctie`. Without the package it is 0.
- Dashboard: block **Forecasting Configuration (Quooker)**, only visible when the package is loaded, and a row in the Optional packages card.
- **Counted separately:** the energy above the threshold does not count in the planner's usage profile, daily usage and self-consumption, just like the car and the AC (the battery does not supply it, so the planner does not need to charge for it). Counters `sensor.zendure_quooker_separate_total`, `..._separate_from_solar_total` and the 7-day figures; row *Counted separately (7 days)* in the block. *Reset usage data* also clears these counters.
- Dashboard: *Status* section in the Quooker block (power, subtracted from grid meter, counted separately, of which from solar) and chart *Quooker and battery (last 6 hours)* with Quooker, correction, Zendure and grid meter.
- Diagnostics export: column `quooker_correction_w` in the snapshots (older rows get an empty value there), `sensor.zendure_quooker_power` and the separate counters in details.

**Path check: charging limited by the room at that moment, not the room now**
- Allocating charge slots to expensive quarter hours capped the total at the room the battery has *now*. Charging in the afternoon for the evening peak and at night for the morning peak then shared that room, and the night used it up (prompted by Omnibattery 2.0, discussion #865). The planner now runs the battery content per price slot (usage out, solar in) and a charge slot may only fill up to the room until the expensive quarter it serves. New variables `path_slots` and `path_base`.
- **Smart hold looks up to the next planned charging** (`sh_end_ts`): the charge of now goes to the most expensive quarter hours before that charging. Before, any charging planned before the end of the gap (also the night after the evening peak) turned smart hold off completely.
- **Holding between charge slots is independent of *Smart hold*:** what the battery supplies now and is charged back later with loss always costs more than buying now; the switch also turned that off. With the switch off, the battery supplied during the day and then charged back again and again (prompted by Omnibattery 2.0).
- **At an equal price the latest quarter before the peak:** at exactly equal prices the allocation chose the earliest quarter; the battery then sat full for hours and was topped up again and again.
- Closed loop (`tools/scenario_sim.py`), net cost old → new (optimum): afternoon + night at 60% €5.94 → €5.74 (€5.74), at 20% €6.71 → €6.49 (€6.49), at 95% €5.11 → €5.08 (€5.08); three tariffs with smart hold unchanged at the optimum.

**Prices after midnight: backup from yesterday's prices**
- If Nord Pool drops out after midnight (the HACS sensor then sometimes gives no `raw_today` for hours, or still yesterday's), the planner planned nothing and nothing was charged. New sensor **Forecast Price Backup** (`sensor.forecast_price_backup`) stores tomorrow's prices every 5 minutes as soon as they are known; when Nord Pool has no price for now, the planner uses that backup (attribute `price_source`: `nordpool`, `reserve` or `none`). Tomorrow's prices arriving later are appended after the backup.
- Notice in the plan card when Nord Pool gives no price for now for more than 5 minutes: warning when the backup takes over, error when the backup is empty too (prompted by the QempZoR diagnostics export).

**Savings start again**
- The button is now called **Savings Start Again** (dashboard: *Start again (all periods)*) and resets today, this month, this year and yesterday as well as the total. Installations from before 2026.11.7 with a wrong fixed tariff setting had a negative dynamic cost item; resetting only the total left month and year wrong.
- Notice in the plan card when the dynamic costs of this month or the total are negative while power was taken from the grid.
- Note: in the per-source statistics graphs the reset gives a negative step on the day itself.

**Notice for a very low solar forecast reliability**
- When the general value or a month value is between 0 and 10%, the plan card notes that the planner uses that percentage of the expected solar. Usually a factor (1 = 100%) was entered.

**Planner: fewer charge starts, timeline with holding, adjusting to usage**
- **Fewer charge starts:** the allocation picked the cheapest per quarter, also when that left a single-quarter gap between two charge blocks (often a hundredth of a cent apart; prompted by QempZoR, 01:30–01:45 and 02:00–05:45). The planner now swaps a quarter at the edge of a block (or a lone quarter) for a quarter that closes the gap or joins a block, if it is at most €0.005/kWh more expensive (`c_gap_max_difference`) and no more expensive quarter lies between the two. Applies to today's plan and tomorrow's estimate; number of quarters and kWh stay the same, the running quarter stays.
- **Line *Plan* after midnight:** when all charging falls after midnight and there is an estimate for tomorrow, the *Plan* line shows the provisional plan (which replaces the plan at 00:00), no longer the charging of today's plan. Under *Today* it then says *Charge from the grid: nothing more today*, the *Planning* line is left out and *Expected usage* does not count that charging (they described the plan that is replaced at 00:00). *Battery is holding now* only when there is something in the battery.
- **Plan Timeline holds like the automation:** in cheap dips, between charge slots (later charge slot more expensive after loss), with smart hold today below the threshold price and tomorrow below its own threshold (`tl_threshold_tomorrow`: tomorrow's expected charge exactly covers the most expensive quarters). Before, the timeline discharged in the cheaper afternoon hours and was empty before the evening peak, while the battery actually holds (prompted by QempZoR). New series `hold` in the timeline.
- **Adjusting when usage deviates:** the usage profile keeps the last 6 measured hours with what the profile expected (attribute `recent_hours`). When usage deviates, the planner uses a factor for the coming 6 hours (measured ÷ expected, limited to 0.7–1.5, damped by the number of hours, fading to 1). Attribute `usage_adjustment`; line on the plan card at a deviation of at least 5%.

**New planner in control (on by default since this version)**
- **On by default:** the *New planner* switch (`input_boolean.forecast_setting_new_planner`) turns on once by itself after the upgrade (automation `forecast_new_planner_default`, flag `..._set`). If you turn it off, the current planner is in control again (fallback, kept for one more version). *New planner may export* stays off by default.
- Less switching between supplying and holding: every hold start costs €0.005 in the decision (`c_opt_hold_start`), so short pieces of holding (with the standby and flash write that come with it) only happen when they yield at least that. The optimisation now remembers the previous action (supply, charge or hold); the start also counts from the current state (charging running / hold active).
- Calibration charging is in the optimisation itself: if the battery does not reach 100% within the horizon, that costs from half the threshold rising to €0.30 (`c_opt_cal_soft`) and at the threshold €2 (`c_opt_cal_hard`, then it practically always charges full). It picks the cheapest way itself (also with solar), and the *New planner* block shows *Calibration: battery at 100% at …*. The calibration slots of the current planner no longer control the new planner.
- Export in the new planner: switch *New planner may export* (`input_boolean.forecast_setting_new_planner_export`, off by default). Per quarter hour it also weighs *export* (battery at full discharge power: the house first, the rest to the grid), for example making room for the sun in the morning or exporting stored solar in the evening. State *Export*; the automation uses the existing *export* branch (`binary_sensor.forecast_solar_surplus_export`, reason *new planner*).
- Uses the feed-in price **without net metering** (bare market price + markup + solar bonus), also in 2026: safe for whoever exports more than they import over the year, and the real price from 2027. Only with a real market price (*Market price sensor*); only works when *PV Export Disabled* is off. Solar surplus that does not fit in the battery now also counts at that price (all variants of the new planner).
- With the new planner on, *Discharge battery at negative prices* and *at solar surplus* no longer do anything.
- Reason: backtest 3-2 to 18-11 with Bjorn's solar and the 2026 quarter-hour prices (`tools/terugrekenen.py`): with the 2027 rules €153 → €72 net (≈ €81 less) with export.
- Fewer charge starts: every charge start costs €0.02 in the decision (`c_opt_charge_start`), so charging in one block beats charge-hold-charge at a small price difference. If the Zendure is already charging, the next quarter of charging does not count as a new start.
- More accurate: the action per quarter hour is chosen from the real state of charge (not rounded to the 40 steps), looking one step ahead. With 40 steps the result on the 18-11 exports is within €0.004 of 80 steps; calculation time unchanged.
- Switch *New planner in control (test)* (`input_boolean.forecast_setting_new_planner`, Configuration Basic): the optimisation per quarter hour (below) decides charging and holding instead of the current planner. Turns the shared battery model on by itself. Turn off = back to the current planner.
- The state (*Charge* / *Waiting* / *Not needed*), `hold_discharge`, `planned_grid_charge_kwh`, the *Plan* line and the Plan Timeline (charge, hold, battery, state of charge, grid) then come from the same plan. Charging only when there is room in the battery.
- Charge margin: counts as that percentage more usage in the decision. Calibration charging runs via the calibration slots of the current planner and goes first. Export (discharge battery at negative prices and at solar surplus) and the AC work as always.
- Reason: export 18-11 17:13. The current planner held the full battery all day (*holding until the next charge slot, topping up costs €0.394*), also at 17:00 at €0.383, and planned 0.7 kWh of charging into a full battery tonight. The new planner supplies in the evening peak, does not charge and keeps ~85% for tomorrow's more expensive hours: €0.19–0.23 cheaper until the end of tomorrow.
- State with the switch on: *Charge*, *Hold* or *Supply* (the automation only charges on *Charge*).
- Configuration: *Shared battery model* is no longer on the dashboard (the new planner turns it on by itself). *Hold discharge in cheap dip* and *Smart hold* only show when the *New planner* switch is off; the new planner finds dips and expensive quarter hours by itself.
- *Discharge battery at negative prices* and *at solar surplus* (Negative Price block) only show when *New planner* is off. With the new planner, pre-discharge no longer overrides holding: the planner makes room before a negative window by itself and only holds when that is cheaper (tested: 20:00, battery 40%, window tomorrow 11–15, holding 02:30–06:00 in the cheap night was overruled before, while the sun fills the battery anyway). The plan card then drops the lines *Negative prices* and *Export before the sun*.
- Plan Timeline: narrow *Plan* bar below the prices with per quarter hour charge (blue), supply (orange), hold (grey) and export (red), from the same plan as the *Planning* block. New series `supply` in the timeline (only quarter hours in which the battery really supplies); with the old planner derived from discharging.
- *Planning* block: new line *Supply* (when the battery powers the house, with kWh; only quarter hours in which the battery really supplies), also in *Planning tomorrow*. While tomorrow's prices are unknown, *Supply* and *Hold* only show today (tomorrow is then today's pattern; it is listed under *Planning tomorrow*). *Empty at* says *empty tomorrow at …* when that is tomorrow. Plan attribute `optimal.supply`.
- Plan card: with the switch on, the block is called *Planning* (without the intro sentence) and the lines of the current planner disappear (*Scenario*, *Today's plan runs until*, *Expected usage until end of bridge*, *Battery is holding now*, *Grid charging*, *Planning*, charge blocks; under Tomorrow *Cheapest hours tomorrow*, *Expected usage tomorrow*, the estimate and the provisional plan). Tomorrow then shows *Planning tomorrow: charge …; hold …*. Log line *Discharging stopped: new planner, battery saved for more expensive quarter hours*.

**Shadow planner (test, only with Shared battery model on, controls nothing)**
- New planner that works out the cheapest choice per quarter hour over all known price slots (today and tomorrow, or today's pattern): charge from the grid, hold, or supply normally. Method: dynamic programming over the state of charge (40 steps); the charge left at the end counts at the cheapest price × discharge efficiency. Holding, the efficiency filter, minimal spread and the path check follow from it; charge margin, calibration charging and export are not in it yet.
- Reason: export 18-11 08:30 (battery 98%). The current plan held the full battery until 14:45, planned 1.5 kWh of charging into a full battery (the path check calculates without the plan) and still had 39% left at midnight. The shadow planner supplies in the morning, holds in the cheaper afternoon and does not charge today: €0.24 cheaper until the end of tomorrow.
- Plan attribute `optimal` (action now, charge and hold blocks, state of charge at midnight, costs vs the current plan, calculated the same way); chart data `optimal_actions` (action per price slot). A *Shadow planner (test)* block in the plan card.
- Plan card: the *Planning* line now says it is about the situation in which the battery just supplies from now on and does not top up (was *without topping up, the battery is empty …*, which read like a forecast).
- `tools/scenario_sim.py --opt`: closed loop with the shadow planner in control.
- Shared battery model without a detailed forecast during the day: the solar still expected today, spread evenly until sunset (was: the sun covers all usage until sunset, even when hardly any sun is coming). Nothing changes with Solcast or Helios.

**Shared battery model (new, test, off by default)**
- New switch **Shared battery model (new, test)** (`input_boolean.forecast_setting_shared_battery_model`) in Forecasting Configuration (Basic). Off = everything as before (verified: identical). On: one list `bat_slots` with per future price slot the usage, direct solar, solar surplus and dip, with one solar source (detail of today and tomorrow). From it read:
  - the **start of the shortfall** (`bm_empty_ts`; without looking ahead it used no solar);
  - the **path check** (`path_base`): now holds between charge slots like the automation, so it does not count with too much room;
  - the **expensive quarter hours** in the shortfall;
  - **smart hold**: skips dip quarters and counts the solar surplus before the end (`sh_solar_dc`), so the battery does not save in the morning while the sun fills it later anyway;
  - the **Plan Timeline**;
  - **"battery empty"** on the dashboard, now from the timeline (with planned charging and holding, like the chart).
- Attributes `battery_model` (`classic` / `shared`) and `calculation_time_s` (planner calculation time); both also in `meta` of the diagnostics export.

**Planner no longer recalculates on every percent**
- The planner recalculates every quarter hour and on changes in settings or prices, no longer on every percent of state of charge (that was 10–35 times per hour). An extra trigger as soon as the battery is 1% below the max. state of charge, so charging stops in time. Nord Pool only on new prices (`raw_today` / `raw_tomorrow`), no longer on the price change per quarter (that coincided with the quarter-hour pattern); the measured charge power (information only) is no longer a trigger. Together: 4 times per hour, plus on new prices and changes in settings.

**Categorise automations**
- Button **Categorise automations** in the Diagnostics export block: puts all automations of the set (including Gielz's *Zendure zenSDK (Gielz) Global*) in the category **Zendure zenSDK Forecasting**. A category cannot be set in YAML; the button uses the HA websocket (administrator, button-card). A category of your own is kept.

**Tools**
- `tools/scenario_sim.py` `--model`: with the switch Shared battery model on.
- `tools/scenario_sim.py`: closed-loop simulation per quarter hour on synthetic scenarios, compared with the optimum (dynamic programming), and `--regels`: rule tests over 54 situations (more usage → never less charging, no loss-making slot, plan stable after a quarter hour).

**Upgrading**
- Replace **all** files (also the optional packages you use and the automation), add the new required package `zendure_recorder_global.yaml`, **restart** Home Assistant (new helpers) and paste the dashboard again via the Raw configuration editor.
- **The planner works differently:** after the restart *New planner* is on (once). The state is then *Charge*, *Hold*, *Supply* or *Export*, and the plan card shows the *New planner* block. To go back to the old planner: turn *New planner* off (Settings → Forecasting Configuration (Basic)). That fallback stays for one more version.
- *Discharge battery at negative prices* and *at solar surplus* no longer do anything with the new planner. If you want export from the battery: turn on *New planner may export* (needs the *Market price sensor* and *PV Export Disabled* off).
- Your own `recorder: exclude` for `sensor.zendure_forecast_chart` in configuration.yaml can stay or go.
- Problems or odd choices: turn *New planner* off and send a diagnostics export (the plan of the new planner is in it as `optimal` / `optimal_actions`).

## 2026.11.7 — based on Gielz v20261113

**Helios Forecast as solar forecast, with detail per quarter hour**
- [Helios Forecast](https://github.com/ReikanYsora/Helios-Forecast) now works just as well as Solcast. Enter `sensor.<name>_energy_today_remaining` at **Solar remaining today** and `sensor.<name>_energy_day_2` at **Solar tomorrow** (day 1 is today, day 2 is tomorrow).
- The planner takes the curve per quarter hour from the attribute `forecast` of the *Power now* sensor of the same Helios device (`sensor.<name>_power_now`, also when renamed) and converts it to half hours, like Solcast. With Helios, the path check (*solar covers from*), pre-discharge, discharge at solar surplus and the Plan Timeline now also know when solar covers the usage. Before, the planner fell back to *sunrise + 3 hours*.
- Sensor detection: Helios Forecast is found after Solcast and before Forecast.Solar.
- Tip: Helios corrects itself with your measured yield. Leave **Solar forecast reliability** at 100%, otherwise you correct twice.

**Fix: night charging stopped every 2 minutes (EN set only)**
- The charging check (since 2026.11.5) looked for the planner status `Charging`, but the English planner says `Charge`. As a result it stopped every charge after one minute and the charging branch restarted it two minutes later. Every restart left a waiting run behind, until the automation hit its maximum of parallel runs (*Maximum number of runs exceeded*) and, at the end of the slot, all waiting runs sent a stop to the Zendure at the same time (*Client error … /properties/write*). The Dutch set was not affected.
- In addition, a charging run now ends by itself when charging was already stopped elsewhere (e.g. by the charging check), so runs can no longer pile up (EN and NL).

**Fix: savings counted a supply markup of −1 €/kWh on a new installation**
- Home Assistant starts an `input_number` without a stored value at its minimum. **Dynamic supply markup** and **Fixed contract feed-in tariff** then started at −1 €/kWh. With the Nordpool package the markup field is hidden on the dashboard, so it went unnoticed, but the savings still counted it: every kWh became about €1 cheaper and *Savings* and the battery payback time came out far too high (seen in an export: €86 in 8 days).
- With the Nordpool package the supply markup no longer counts at all (the all-in price already includes it).
- New automation *Savings Default Values*: sets both fields to 0 at start when they are at −1 (logbook line). Savings already collected stay as they were.

**Feed-in price: Dutch net metering (salderingsregeling) until the end of 2026, then without VAT (switches by itself on 1 January 2027)**
- **Net metering until 31-12-2026, then without** (no choice): every quarter hour that starts before 1 January 2027 00:00 counts with net metering, after that without. Outside the Netherlands: leave the energy tax at 0.
- While net metering applies: feed-in price = market price **with** VAT + energy tax (incl. VAT) + bonus + markup. Through net metering you get the energy tax back; it did not count before. As a result *no export at negative price* now only steps in when the market price drops below about −€0.11 (before already below €0, while exporting still earned money), and the savings value export higher.
- From 1 January 2027 (per quarter hour, so pre-discharge for quarters after midnight too): market price **without** VAT (private households pay and receive no VAT on export) + bonus + markup, no energy tax.
- Whether the market price sensor includes VAT is taken from the Nord Pool sensor name: `sensor.nordpool_kwh_nl_eur_5_10_021` = incl. 21% VAT, `..._0` = without VAT. Another sensor is treated as incl. VAT. The dashboard shows this at **Market price sensor is** (no setting).
- Energy tax and VAT % come from the Nordpool package. Without that package: new field **Energy tax under net metering (incl. VAT)** (`input_number.negative_price_net_metering_energy_tax`).
- `sensor.zendure_feedin_price_now` has new attributes `net_metering_active`, `net_metering_until`, `net_metering_until_ts`, `vat_pct`, `market_vat_factor`, `energy_tax_net_metering`; the savings and the planner (pre-discharge) use them per quarter hour.
- **Savings, fixed contract:** while net metering applies, export counts at the supply tariff. The field is now called **Fixed contract feed-in tariff (without net metering)**: enter your contract's feed-in tariff for 2027.

**Dynamic and Forecasting always on the dashboard**
- The switches *Show Dynamic On Dashboard* and *Show Forecasting On Dashboard* are gone; the dynamic information and the Forecasting section (and settings) are always on the dashboard. `input_boolean.dashboard_setting_show_forecasting` is removed; Gielz's `input_boolean.dashboard_setting_show_dynamic` stays in his package but is no longer used. *Show Help* stays.

**PV information shown automatically on a Zendure with solar inputs**
- The *Show PV On Dashboard* switch is gone. The PV chart and badges (Zendure tab), *Gielz Configuration (PV)* and *PV Export Mode* (Health tab) now appear when the Zendure has solar inputs (Pro, Plus or Hyper, `binary_sensor.zendure_has_pv_inputs`; unknown = shown). On a 2400 AC or AC+ they disappear automatically.
- Gielz's `input_boolean.dashboard_setting_show_pv` stays in his package but is no longer used.

**Fix: review of all files (15-11)**
- EN dashboard: Gielz's *Import | Export* chart was damaged when the usage profile was added (the Export series lacked statistics, column and colour; the counter card was at the bottom). Restored as in Gielz.
- Dashboard: in three of Gielz's help texts the hard line breaks (two spaces) were lost, so lines ran together. Restored.
- Plan card and *Collected data*: no template error any more when the planner does not exist yet (dashboard pasted before the restart); the plan then shows a notice.
- Checked: all references to entities and attributes between the files, NL = EN, and the Gielz files only differ in the intended places (mode *Dynamic Smart Matching + Forecasting*, `pv_active` without pvStatus, EV/HVAC correction and dip block in Smart Matching, checks not in Forecasting mode).

**Dashboard no longer calculates itself (16-11)**
- **Usage per weekday** is calculated by the planner (attributes `usage_per_weekday_kwh` and `profile_weeks_per_weekday`), with the same blending as the plan. The card *Collected data* and the chart *Usage per day* only read it (each calculated it themselves before, and without the fallback to the day average the plan uses).
- **Plan card:** what the house buys directly from the grid (`direct_grid_kwh`), the part of the energy balance that is not stored (`grid_charge_not_stored_kwh`) and the average feed-in price for *Negative prices* (`pre_discharge_export_price`) and *Export before the sun* (`solar_surplus_export_price`) come from the planner.
- **New sensor `sensor.forecast_notices`** (count; attribute `notices` with id, level and text): missing HACS cards, new release, mode not active, solar forecast not available, filled-in field without an existing sensor. The plan card shows this list; the diagnostics export includes it (`meta.notices`). Only the difference between dashboard and package version is checked by the card itself.
- **Savings:** the *Overview* table reads the sensors per period (Today, This Month, This Year, total) instead of calculating from the buckets; new attribute `costs_fixed_without_solar_and_battery`.
- **Card Optional packages** uses the `packages` attribute of `sensor.forecasting_version`.

**Calibration charging by default after 21 days** (was 14). Applies to new installations and when the field is 0; a value set earlier stays.

**Calibration charging: continue to 100% early (17-11)** — from half the threshold: if planned grid charging brings the battery to at least 85% anyway (or it is charging and already there), it continues to 100% in the cheapest quarter hours around that charge block. Costs little extra and the counter restarts earlier. Plan line *Calibration*: "… brings the battery to about X% anyway: it continues to 100%". Attribute `calibration_early_soc`.

**Fix: hold between charge slots only with real charging (16-11)**
- A full battery (98%) stayed in standby in the morning in an expensive quarter (€0.407), because a remainder of 0.24 kWh charging was planned at 13:15 (€0.357 / 84.5% efficiency = €0.423). What the battery supplies now is then not charged back but simply used earlier; the plan itself already counted on discharging.
- Hold between charge slots now only applies with at least 0.5 kWh planned grid charging later (the same limit as smart hold), and the price now must be at least €0.01 below the charge price after loss.

**New: charging at a negative purchase price (16-11)**
- When the all-in supply price is negative (you get paid to take power), the battery charges in all those quarter hours until full, at full power. Outside the efficiency filter and minimal spread; later solar does not count. Only in the mode *Dynamic Smart Matching + Forecasting*.
- **Negative purchase price** line in the plan; attributes `negative_purchase_charge`, `_quarters`, `_from`, `_until`, `_price`.

**Decision log: the real reason for *Discharging stopped* (16-11)**
- Always said *cheap dip or HVAC on*, also with smart hold. Now e.g. *smart hold, battery saved for prices from €0.405 (now €0.397)*, *holding until the next charge slot, topping up costs €0.423 after losses*, *cheap dip (below €0.316)* or *AC on*. New plan attribute `between_charge_threshold_price`.

**Fix: price shortly after a restart (16-11)**
- After a restart the Nord Pool sensor of the Nordpool package sometimes briefly calculated without energy tax, markup and VAT (the input fields were not loaded yet): in an export of 16-11 e.g. €0.137 at 14:15 where it should have been €0.28. The package now uses the default values then (VAT 21%, energy tax €0.09161, markup €0.02).
- **Savings:** an all-in price below the bare market price (impossible) is no longer stored; that quarter is settled at the price of the next measurement.

**HVAC: approach per AC mode (16-11)**
- Under *Approach per mode* choose *Default*, *No discharging* or *AC not from battery* per mode (e.g. Cooling: AC not from battery, Heating: No discharging). *Default* = the general approach. New `input_select.hvac_approach_heating` / `_cooling` / `_drying` / `_fan` / `_auto` and `sensor.hvac_approach_now` (the approach that applies now).

**Savings per source as separate sensors (16-11)**
- `sensor.zendure_savings_solar_panels`, `_dynamic_tariff` and `_battery_and_smart_charging` (total, same numbers as the attributes of `sensor.zendure_savings`). New stacked chart **Savings per source per day** on the Savings tab; counts from this update.

**Plan Timeline and usage profile (16-11)**
- **Plan Timeline:** export from the battery (at solar surplus or ahead of negative prices) shows red in the battery row and the grid shows the export; planned car charging (EV package, *Night*) shows as a purple line under Solar and usage and counts in the grid. EV package: new attribute `charge_slots` on `sensor.ev_charge_plan`.
- **Usage profile per quarter hour:** new chart below the hourly profile (workday and weekend, kWh per quarter, with the learned shape within the hour). Attributes `usage_per_quarter_workday_kwh` and `_weekend_kwh` on `sensor.zendure_forecast_chart`.

**Diagnostics: Flash counter (16-11)**
- `sensor.zendure_flash_writes` (diagnostics export package) counts how often per day the Zendure switches to *Flash Memory*; `per_day` keeps 14 days and is in the export (`flash_writes`). Row *Switches to Flash (today)* in the Diagnostics export block.

**After the test of 17-11**
- Sensor detection choice lists: no more *Template variable warning* at a restart.
- Diagnostics export: also `sensor.forecast_solar_month_measurement` and `sensor.hvac_power_from_counter` with attributes.

**Tools (16-11)**
- `tools/planner_sim.py` and `vergelijk.py` work again with the 2026.11.7 planner (`integration_entities` etc. emulated).

**Fix: solar bonus only in daylight, on bare market price + markup (like Zonneplan)**
- The feed-in bonus (now **Solar bonus % (daytime)**) counted on the market price **including** VAT, all day. Zonneplan gives the solar bonus on the bare market price (without VAT) plus the sales fee, only between sunrise and sunset and only when that amount is positive.
- Now: solar bonus = bonus % × max(bare market price + feed-in markup, 0), only while the sun is up (`sun.sun`; for quarter hours in the plan and the savings the middle of the quarter between sunrise and sunset).
- Example Zonneplan (10%, markup €0.02, market price €0.20384 incl. VAT): in the evening €0.3347 (was €0.3571), in daytime €0.3535.
- Applies to the feed-in price, *No export at negative price*, *Discharge battery at negative prices*, *Discharge battery at solar surplus* and the savings.

**Fix: Solcast detail for today with Dutch entity names**
- With HA in Dutch the Solcast sensor is called `…_resterende_voorspelling_vandaag`. The planner only looked for today's detailed forecast under the English name (`…_remaining_today` → `…_today`), and found nothing with the Dutch name. As a result there was no solar for the rest of today in the Plan Timeline, the state of charge line ran empty during the day and the path check used *sunrise + 3 hours*. Now also `…_voorspelling_vandaag`, and as a fallback all Solcast sensors (only if you use Solcast). Also in the diagnostics export.

**Discharge battery at negative prices: now actively exports**
- The switch is called **Negative prices (export before)**. If the battery holds more than the target at the start of a window with a negative feed-in price (room for the expected solar surplus), it exports the difference **at full power**, in the quarter hours with the highest positive feed-in price before the window, until the target is reached. Before, it only lifted holding and limited grid charging.
- Now also counts when the morning sun would fill the battery before the window (what no longer fits has to go out beforehand). Before, pre-discharge then did nothing.
- Planner: attributes `pre_discharge_export_now`, `pre_discharge_export_kwh`, `pre_discharge_export_slots`. `binary_sensor.forecast_solar_surplus_export` is also on when exporting before negative prices (attribute `reason`); the automation's export branch handles both. Plan for today: line **Negative prices** with window, target and export.

**New: discharge battery at solar surplus (export before the sun)**
- Switch **Solar surplus** (`input_boolean.solar_surplus_discharge`) in Forecasting Configuration (Battery discharge and Negative Price), under *Discharge battery at*. Off by default.
- If the sun will fill the battery anyway, the battery exports what the house does not need until the sun (plus margin) to the grid before the sun: in the quarter hours with the highest feed-in price, at maximum discharge power. Example: battery 40%, 20% needed until the sun, the sun fills the battery → about 20% exported in the most expensive quarter hours before the sun.
- Only when it pays off: feed-in price now > feed-in price during the sun / efficiency (+ €0.01). Not when grid charging is planned before the sun, and only with a detailed solar forecast (Solcast or Helios). Without a filled-in reliability, 75% of the expected surplus counts.
- Planner: attributes `solar_surplus_*` (kWh, quarter hours, sun from, price during the sun, threshold price, revenue); `binary_sensor.forecast_solar_surplus_export`. Automation: new branches *Dynamic Smart Matching + Forecasting export at solar surplus* (Gielz's `zendure_quick_discharge`, stops when there is no export quarter left or at minimum state of charge) and *… export check* (after a restart). Gielz's *Dynamic discharging check* does not apply in Forecasting mode.
- Plan today: line **Export before the sun** with kWh, times, price and estimated revenue. The Plan Timeline shows the export in red.

**Easier configuration**
- **Sensors detected automatically:** the set looks for the sensors for the five sensor fields in Forecasting Configuration (Basic) itself:
  - *Solar remaining today* and *Solar tomorrow*: Solcast, then Helios Forecast, then Forecast.Solar.
  - *Solar production sensor*: the total counter (kWh) of an inverter integration (SolarEdge, Enphase, Growatt, SMA, Huawei, Fronius, GoodWe, Solax, Solarman, APsystems, Hoymiles and others), then HomeWizard or Shelly meters with solar/pv/inverter in the name.
  - *Grid import/export counter*: HomeWizard P1, DSMR integration, P1 Monitor, SlimmeLezer (ESPHome), DSMR Reader; then Shelly energy meters (Pro 3EM, 3EM, EM). Tariff 1 + 2 or per phase as a comma list.
  - **One candidate:** an empty field is filled in with the full sensor (a Shelly only when its name points to the grid, e.g. *Main meter*). A field you filled in yourself is kept; every fill-in is in the logbook.
  - *Home energy meter sensor* (Gielz's field, power in W): a Zendure P1 meter via the local API (own REST sensor with *zendure* and *p1* in the name, e.g. `sensor.p1_zendure_api`), then HomeWizard P1 (integration) and Shelly Pro 3EM (total power). Filled in automatically only when Gielz's HomeWizard P1 via the IP address gives no value, so Smart Matching does not switch source unasked. Gielz's own P1 sensors do not count.
  - *Dynamic Nordpool Sensor* (Gielz's field): `sensor.nordpool_kwh_nl_eur_5_09_0` from the Nordpool package is preferred, then other Nord Pool sensors (HACS) with `raw_today`, except the bare market price sensors (5_10_…).
  - **More candidates:** a dropdown **↳ Choose from the sensors found** appears below the field; choosing writes the sensor into the field.
  - New: `sensor.forecast_sensor_candidates` (candidates per field, also in the diagnostics export), `select.forecast_choose_…` (5 dropdowns), automation `forecast_sensors_fill` (replaces filling in only the solar sensors from the test version).
- **Grid counters:** when they are detected automatically (HomeWizard, SlimmeLezer, DSMR), the dashboard hides the input fields and shows which sensor is used (*Grid import counter (detected automatically)*). New `binary_sensor.forecast_grid_import_counter_automatic` and `..._export_...` (attribute `sensors`).
- **No more "unknown" in empty input fields:** a field that was never filled in is emptied (not Gielz's own fields). Solar fields and grid counters that are still empty show **(please fill in)**.
- **Extra planner charge margin %** was called *Battery charge margin %*.
- The block is now called **Forecasting Configuration (Battery discharge and Negative Price)**. At the top **Discharge battery at** with the switches **Negative prices** (was *Pre-discharge*, same entity) and **Solar surplus**; below it **Negative price** with *No export at negative price*.
- **No more "(0 = …)":** the default value is now really in the field: *Calibration after days* 21, EV *Charging power kW* 2.3, *Threshold W* 300, *Ready by* 07:00, HVAC *Threshold power W* 50, *Solar forecast reliability %* 100. That 100 does not count as *filled in*: without a value of your own, pre-discharge still uses 75% of the solar surplus. The month fields are now called *January %* etc.; 0 still means *the general value* there. If you set a field to 0, the default comes back (automations `forecast_default_values`, `ev_default_values`, `hvac_default_values`).
- **Fill in the monthly value automatically** (was *Do not fill in the monthly value automatically*, `input_boolean.forecast_setting_reliability_auto_fill`) is on by default. Had you turned the old switch on (do not fill in), turn the new one off after the upgrade.
- **Calibration charging** is now an on switch (was *Calibration charging off*) and is on by default, also if you turned it off before: turn it off again after the upgrade if needed.
- **Missing cards notice:** if apexcharts-card, card-mod or button-card is missing (detected via HACS), the dashboard says which to install.
- **Upgrade notice:** if the dashboard does not match the version of the packages, the plan says what to replace (paste the dashboard or replace the packages). If a new version is on GitHub, it says so too.

**Charge power: the configured value**
- The planner now uses the **Max Charge Power** from Gielz. Despite the fixes, the measured charge power kept coming out too low (ramp-up, changing sun, balancing; e.g. 1.4–1.6 kW for a real 2.4 kW), so it planned too many quarter hours. The measurement (now the 90th percentile) is only shown for information under Collected data.

**Clearer plan on the dashboard**
- *Today's plan runs until* without the fixed explanation after it.
- *Expected usage until end of bridge*: now split into battery now + solar to the battery + planned charging (after losses), and how much the house buys directly.
- Charge blocks of tonight after midnight no longer show under *Today* when there is an indication for tomorrow (it plans again at 00:00). Under *Tomorrow* the charge lines are called *Provisional plan: charge tomorrow …*.
- *Price now* removed (already in the chart and badges); when the battery holds, the reason is in the line **Battery is holding now**.
- **Planning** and **Tomorrow**: clear that it plans again after midnight for tomorrow's expensive hours, and that tomorrow's estimate replaces tonight's charging.
- **Collected data:** new line **Usage per day** (kWh per weekday from the profile). The own profile per weekday shows how many weeks have been measured (*Mon 1/3*) instead of *0 of 24 learned*.

**Charts**
- **Fix (EN):** the planner attribute for exporting at solar surplus is now `solar_surplus_export_kwh`; as `solar_surplus_kwh` it overwrote the existing attribute of the same name.
- **Plan Timeline:** the columns now sit in their own quarter hour (before they were centred on the start, half a column early compared with the usage line and the time). The time labels at the bottom are annotations at the exact time (03:00, 06:00 …, day name at midnight); before, the bottom row could shift (e.g. around 12:00).
- **Usage Profile:** the column of an hour sits between that hour and the next. The legend no longer shows *0.6 hours* (that was the last bar with the unit of the profile sensor). New second chart **usage per day**: expected usage per weekday in kWh (green workday, grey weekend).

**Upgrading**
- Replace **all** files (including the optional packages you use and the automation), **restart** Home Assistant (new helpers) and paste the dashboard again via the Raw configuration editor. If the dashboard does not match the packages, the plan card says so.
- **Check after the restart:**
  - *Calibration after days*: a value set earlier stays; set it to 21 if you want the new default.
  - *Calibration charging* is on again, also if you had turned it off: turn it off again if needed.
  - *Fill in the monthly value automatically* is on: if you had the old *do not fill in automatically* switch on, turn the new one off.
  - *Market price sensor is* now shows what the set reads from the sensor name (e.g. *incl. 21% VAT*); no longer a setting.
  - Savings: enter the fixed feed-in tariff for 2027 (*Fixed contract feed-in tariff (without net metering)*).
  - Sensor fields are filled in automatically where possible; a field you filled in yourself stays.
- **Can be removed** (orphaned, if HA still shows them): `input_boolean.dashboard_setting_show_forecasting`, `input_boolean.forecast_setting_calibration_off`, `input_boolean.forecast_setting_reliability_no_auto_fill`, `input_select.negative_price_net_metering`, `input_select.negative_price_market_price_vat` and the automation `forecast_solar_sensors_fill` (from a test version).

## 2026.11.6 — based on Gielz v20261113

**Dashboard fix: Forecasting Configuration (Negative Price) always visible**
- The block only appeared when *Show PV On Dashboard* was on. On a Zendure without solar inputs (e.g. 2400 AC+) that is usually off, and then the whole block was missing, including the part for the external inverter. Now it only depends on the negative price package. The row *Disable PV export at negative prices* (Zendure Pro) stays visible only on a Zendure with solar inputs.

**Upgrading**
- Only the dashboard changed in content (the other files have a new version number). Paste the dashboard again via the Raw configuration editor; replace the other files and restart for the correct version number.

## 2026.11.5 — based on Gielz v20261113

**Updated to Gielz v20261113**
- Configuration Version and the automation description are at v20261113, so Gielz's release check shows *Up-to-date* again.
- **Total Capacity** now knows all battery types for the SolarFlow 4000/3000 Mix models (previously only packType 70). Nothing changes for the 2400 AC.
- Automation: notation only (`name: " "`, two lines joined); works the same.
- **Deliberately not adopted:** Gielz now reads `pvStatus` more safely but still uses it. This set has not used `pvStatus` at all since 2026.11.4 (new Zendure firmware reports it incorrectly); that stays.

**Smart hold as its own switch**
- New **Smart hold** switch (`input_boolean.forecast_setting_smart_hold`) in Forecasting Configuration (Basic). Smart hold (if the battery won't last, it keeps its charge for the most expensive quarter hours) used to depend on *Hold discharge in cheap dip*. With that switch off the battery discharged at low prices in the morning and the house bought the evening peak. Smart hold costs no extra loss and is now **on** by default, also when the dip switch is off (set once after the upgrade; after that your choice stays).
- The path check over the day works with the dip switch **or** smart hold.
- **Small top-up slots no longer block smart hold:** smart hold only turns off from 0.5 kWh of planned grid charging before the end of the gap. A remainder counts towards what the battery can supply.
- **New: hold between charge slots** (part of smart hold). If a charge slot is planned later and the price now is lower than that slot after charge and discharge loss (slot price / efficiency), the battery does not supply now: what it supplies now would have to be charged back there with loss. Prevents the battery from discharging at night between two charge blocks and being charged back at a higher cost. Attribute `between_charge_hold`.

**Charging in Dynamic Smart Matching + Forecasting**
- **Fixed: "charging started" every 2 minutes while the battery discharges.** Gielz's check *Dynamic charging running status is incorrect* turned charging off after 30 seconds when it was not Gielz's cheapest period, even when the planner had a charge slot. The planner then started again after 2 minutes. The check no longer applies in Dynamic Smart Matching + Forecasting.
- **New: Forecasting charging check.** If charging is still running while the planner has not said *Charging* for a minute (e.g. after a Home Assistant restart in the middle of a charge slot), the automation stops charging and returns to Smart Matching.

**Measured charging power without the balancing tail**
- `sensor.forecast_grid_charge_power` now only measures up to 10% below the maximum state of charge. At the end of a charge the power drops (balancing between the batteries); that pulled the measured charging power down (559 W at 2.4 kW for one user), so the planner used far too many quarter hours.
- *Measured Charge Power* now uses the median instead of the mean. Old low readings drop out within 14 days; faster with *Reset usage data* (now also clears the charge power readings).
- **Measured at the Zendure, only during grid charging.** The charge power was the lower of P1 import and charging. With solar from another inverter (e.g. SolarEdge) the import is lower than what the Zendure charges, and charging from solar counted too: the median came out at 1.3 kW for a real 2.4 kW, and the planner then planned almost twice as many quarter hours. Now only the Zendure's charging power counts while *Dynamic charging running* is on (charging by Forecasting or Gielz).

**Input and detection**
- **Input fields cleaned up:** a new automation converts entered entities to lower case without spaces (e.g. `Sensor .solcast_…` from phone autocorrect becomes `sensor.solcast_…`). Applies to the forecasting, negative price, Nordpool, EV and HVAC fields and Gielz's Nordpool and grid meter sensor. Logged in the logbook.
- **HomeWizard in a Dutch-language Home Assistant** is now detected automatically (`sensor.p1_meter_energie_import` / `_export`).
- **Dashboard notice** (Zendure tab, Forecasting) when the solar panel counter or a custom grid counter does not point to an existing sensor.
- **Usage profile keeps learning without a valid solar panel counter:** if the field is empty or the sensor does not exist, the profile uses 0 solar production (previously learning stopped completely). If the counter drops out briefly, the previous measurement stays instead of disappearing.
- **Feed-in markup:** range now −0.50 to 0.50 €/kWh (was −1 to 1) and a warning in Forecasting Configuration (Negative Price) for a markup outside −0.10 to 0.10. A markup of −1.00 made the feed-in price always negative and blocked export permanently.
- **Diagnostics export, error log:** long messages keep both start and end (the cause of a template error is at the end; before, everything after 400 characters was cut off).
- README: clearer that the Diagnostics export package turns on `system_log: fire_event: true` itself.
- **Diagnostics export:** `meta.missing_helpers` (expected settings that do not exist) and `meta.filled_in_but_missing` (entered entities that do not exist).

**Usage profile per weekday**
- The usage profile now also learns **per weekday** (attributes `per_day` / `n_per_day`, 0 = Monday), so the planner sees working-from-home days. Each weekday comes round once a week; while an hour of that day has fewer than 3 measurements, the planner blends it with the workday or weekend profile (1 measurement = one third). Holidays counted as weekend are not learned per weekday. Existing data stays: the workday/weekend profile is the start.
- *Collected data* shows how many hours are learned per weekday.

**Recalculate every quarter hour**
- The planner calculates every quarter hour (just after the price change) instead of every minute, and also right away on changes in settings, prices or state of charge (so charging stops when the battery is full). The **Recalculate** button works as always.

**Solar forecast reliability per month**
- 12 month fields (0–150%, 0 = not filled in: then the general reliability). Shown with **Show reliability per month** in Forecasting Configuration (Basic).
- New `sensor.forecast_solar_month_measurement`: every day it counts actual solar (solar counter) against the previous day's forecast ("Solar tomorrow sensor"). State = ratio this month (%). After a month ends (at least 10 days and 5 kWh forecast) an automation fills the measured value into that month's field, for next year. Turn off with **Do not fill in the monthly value automatically**.
- If a value is filled in for the current month, the dashboard shows the reliability that applies now instead of the general field (`sensor.forecast_reliability_now`, with `binary_sensor.forecast_reliability_month_set`). The general field only applies to months set to 0.
- **Solar credit is gone** (Forecasting Configuration (Negative Price)). Pre-discharge now counts the solar surplus fully when a reliability is filled in (per month or general; it is then already in the forecast), and otherwise for 75%.

**Calibration charging**
- The Zendure calibrates (SOC and balancing) when the battery reaches 100%. With the forecasting that rarely happens in winter. New: **Calibration after days** (0 = 14) and **Calibration charging off**.
- From half the threshold (day 7) the planner waits for a sunny day (if the sun fills the battery today or tomorrow, it does nothing). At the threshold (day 14) it charges the battery to 100% from the grid in the cheapest quarter hours of today and tomorrow, outside the efficiency filter (it is maintenance). Turns off by itself once Gielz's *Last Calibration* sees a new calibration.
- *Plan today* shows a **Calibration** line with the number of days and what the planner does. If *Max. State Of Charge* is below 100%, it says so (calibration only happens at 100%).

**Plan Timeline**
- Price: planned grid charging is now **blue** (was green), like in the Battery row.
- Battery: the state of charge is on its own axis with 0% on the zero line of the kW columns; the line no longer drops below it.
- Grid: **blue** = battery charging from the grid, **purple** = house from the grid, **grey** = export.
- Time axis: labels every 3 hours on whole hours (03:00, 06:00, 09:00 …), midnight as day name, and a dotted line at every midnight in all four rows.

**Path check is now "Planning"**
- New text, for example: *Planning: without topping up, the battery is empty today around 08:21. Until tomorrow 01:45 the house would then buy 9.5 kWh, of which 7.9 kWh expensive (avg. €0.428). So 5.5 kWh charging 02:30–05:00 (10 quarter hours); 3.7 kWh of room stays free for the sun.* Makes clear that the purchase is without topping up, and why not everything is topped up (room for the sun).
- The *empty* time is the start of the shortfall (new attribute `pathcheck_gap_start`). Before, it showed the empty time with smart hold, which could fall after the end of the shortfall (*empty tomorrow around 22:34 … until tomorrow 09:00 buy 0.2 kWh*).

**Upgrading**
- Replace all files (changed in content: `zendure_gielz1986_global.yaml`, `zendure_forecasting_global.yaml`, `zendure_negative_price_global.yaml`, `zendure_export_global.yaml`, the automation and the dashboard; the others only in version number) and **restart** Home Assistant (new helpers). Paste the dashboard again via the Raw configuration editor.
- **Start the measured charge power over** (recommended if *Measured Charge Power* is clearly lower than your real charging power): Developer tools → Actions, `recorder.purge_entities` with `entity_id: sensor.forecast_grid_charge_power` and `keep_days: 0`; about 15 seconds later `statistics.reload`. Until the next grid charge the planner uses your configured charge power.
- After the restart *Smart hold* is on. If you want the behaviour from before this version with the dip switch off, turn *Smart hold* off.
- If you had set a solar credit: that field no longer exists (`input_number.negative_price_pre_discharge_solar_credit` can go). Fill in the reliability per month if you like.
- Calibration charging is on (after 14 days without 100%). Turn it off with *Calibration charging off*.

## 2026.11.4 — based on Gielz v20261007

**Fix for new Zendure firmware** *(ahead of Gielz)*
- With the new Zendure firmware the `pvStatus` field is no longer reliable. *Zendure Power* then used the PV fields even without sun and passed a wrong battery power to the planner, Smart Matching and negative price.
- *Zendure Power* and the PV sensors (*Power PV To Home*, *Power PV Total*, *Power PV To Battery*) now only use `solarInputPower > 0` or `gridOffPower < 0` to decide whether solar is coming in. The old lines are kept as Jinja comments in `zendure_gielz1986_global.yaml`.
- Also works on the old firmware. Restart Home Assistant after updating (REST sensors).

## 2026.11.3 — based on Gielz v20261007

**New: electric car** *(optional package)*
- New package `optional packages/zendure_ev_global.yaml` and a **Configuration (EV)** block on the Settings tab. For a charger without its own control (granny charger, or a wallbox behind a smart switch) with a power measurement, e.g. a Shelly 1PM or Pro 1PM in the charger's circuit.
- **No battery discharge into the car:** the Smart Matching discharge blocks subtract the car's charging power (`sensor.ev_discharge_correction`, above a threshold of 300 W by default) from the grid meter. The battery then only supplies the house; the car charges from the grid or the sun. Always applies, also without a charging session.
- **Planner:** the car's charging no longer counts in the usage profile (per hour and per quarter), the average daily usage and the solar self-consumption. A charging day does not skew the battery forecast.
- **Charging session** (with a configured switch): choose the charge moment and the required kWh. *Night (cheapest hours)* only turns the charger on in the cheapest price slots until *Ready by* (tomorrow's prices unknown: today's pattern, replanned around 14:00). *Daytime (solar)* charges while the sun is up; the planner subtracts those kWh from the solar surplus for the battery and charges the shortfall from the grid at the cheapest moment. Done or time passed: charge moment back to Off and the charger on again.

**HVAC now in the public set** *(optional package)*
- `optional packages/zendure_hvac_global.yaml` (and `zendure_hvac.yaml`) is now part of the public set: no discharging while the AC runs. There is no separate complete set any more.
- The automation checks the AC with a template, so everything keeps working without the HVAC package.
- **Settings per mode instead of per hour:** the *Charge only from/until* times are gone. New `sensor.hvac_mode` (Off, Standby, Heating, Cooling, Drying, Fan, Auto) from the climate entity's mode and `hvac_action`. Per mode you choose whether discharging is still allowed, e.g. Cooling on (summer, plenty of sun) and Heating off (winter, no sun). By default every mode is blocked.
- **Standby does not count:** when the AC has reached its temperature (`hvac_action` idle), the battery discharges as usual.
- `binary_sensor.hvac_discharge_blocked` has a `reason` attribute, also shown in Forecasting Configuration (HVAC).
- **New: approach *AC not from battery*** (list **Approach**, `input_select.hvac_approach`). When the AC may not run from the battery in the current mode (`binary_sensor.hvac_not_from_battery`), you choose what happens: *No discharging* (default, as before: discharging stops completely) or *AC not from battery*: the Smart Matching discharge blocks subtract the AC power from the grid meter, as for the car (`sensor.hvac_discharge_correction`). The battery then keeps supplying the rest of the house. Needs a power measurement: new field **Power sensor** (`input_text.hvac_power_sensor`, W or kW, e.g. a Shelly; empty = the HVAC sensor if that is a power sensor). Without it, *No discharging* applies.
- **kWh counter as power measurement:** if the AC only has an energy counter (e.g. *Energy consumption total* of the AC integration), enter it as **Power sensor**. The power is calculated from the counter's steps (`sensor.hvac_power_from_counter`): last step divided by the time since the previous step or since the AC came on, going down when no step comes, 0 when the AC is off or in standby. Until the first step after switching on, the power of the previous time is used. Use the total counter, not the per-cycle one.
- **New: count AC usage separately.** While the AC may not run from the battery, its usage does not count in the usage profile (per hour and per quarter), the average daily usage and the solar self-consumption, like the car (`sensor.hvac_separate_total`, `..._from_solar_total` and the 7-day figures; power measurement only, in both approaches). The *Reset usage data* button also clears these counters.
- **Fixed:** a power sensor in kW as HVAC sensor was not converted, so the AC stayed below the threshold and counted as *Off*.

**Negative price**
- **Market price sensor automatic:** with the Nordpool package a new automation fills the *Market price sensor* field with the bare Nord Pool sensor (`sensor.nordpool_kwh_nl_eur_5_10_021`, or `..._5_10_0` with VAT: False) as soon as the field is empty. The field therefore always shows which sensor is used; your own sensor stays.
- **Dashboard Configuration (Negative Price):** the feed-in price now has its own line below the title (it overlapped on narrow screens). The Zendure Pro section with **Disable PV export at negative prices** only shows for a Zendure with solar inputs (Pro, Plus or Hyper, new `binary_sensor.zendure_has_pv_inputs` from Gielz' Product Model; unknown = shown). Sections renamed: *Discharge battery ahead of negative prices* and *External inverter (optional) managed at negative prices*.
- **New optional package Nordpool** (`optional packages/zendure_nordpool_global.yaml`): two Nord Pool sensors, the all-in price for supply (`sensor.nordpool_kwh_nl_eur_5_09_0`, for Gielz Configuration (Dynamic)) and the bare market price with VAT for export (`sensor.nordpool_kwh_nl_eur_5_10_021`, for the Market price sensor), with input fields for energy tax, supplier markup and VAT in the new block Forecasting Configuration (Nordpool). Needs: the Nord Pool integration from HACS. If you already set up Nord Pool in YAML with the same settings, remove that.
- **New: Market price sensor (feed-in)** (`input_text.dynamic_setting_market_price_sensor`) in Forecasting Configuration (Negative Price) and (Savings). If your Nordpool sensor is all-in (with energy tax, markup and VAT), fill in a Nordpool sensor with the bare market price here: energy tax and markup only apply to supply. Without this field export was valued too high in that case (for example € 0.315 instead of € 0.128 per kWh) and *no export at a negative price* only kicked in when the market price dropped below about -€ 0.13. Used by the current feed-in price (`sensor.zendure_feedin_price_now`, attribute `market_price_source`), pre-discharge and the savings. Empty = as before. Supply markup can then stay at 0.
- New switch **Disable Zendure Pro PV export** (`input_boolean.negative_price_zendure_pv_export`): choose whether, at a negative price, the feature also disables the PV export of the Zendure Pro (solar inputs) via Gielz' *PV Export Disabled*. Turns on by itself as soon as you switch on *No export*; off = only limit the external inverters, e.g. with a Zendure without solar panels.
- The settings for the Zendure Pro and the external inverter are now together in one card.
- **Feed-in markup and bonus** (`input_number.savings_setting_dynamic_feedin_markup`, `..._bonus`) now live in `zendure_negative_price_global.yaml` instead of the optional savings package, so the feed-in price is right without that package too. Same entities: configured values are kept. On the dashboard they are, together with the market price sensor, in Forecasting Configuration (Negative Price) under *Feed-in price*; Forecasting Configuration (Savings) no longer shows them twice, and *Dynamic supply markup* is hidden there when the Nordpool package is loaded (that sensor is already all-in).
- **New: pre-discharge** (switch *Pre-discharge*, mode Dynamic Smart Matching + Forecasting, needs a detailed solar forecast such as Solcast). If a window with a negative feed-in price and expected solar surplus is coming, the planner makes sure the battery is empty enough at its start for 75% of that surplus. You set that percentage with **Solar credit** (`input_number.negative_price_pre_discharge_solar_credit`, 0 = 75%): higher = discharge deeper and more room for solar, lower = more careful with an optimistic forecast. More solar then fits into the battery and the inverter needs to throttle less.
  - For this the battery only discharges for the house (no export), in the most expensive quarter hours before the window: the hold (cheap dip, smart hold) is lifted there. If it cannot reach the target even discharging everywhere, it discharges in all quarter hours.
  - Grid charging before the window only stays when it fits within the room (cheapest slots first), e.g. charging at night for an expensive morning peak.
  - If solar fills the battery again before the window anyway, it does nothing. Min. SOC always stays. Feed-in markup and bonus count in the feed-in price.
  - *Plan for today* explains what it does; new attributes `pre_discharge`, `pre_discharge_now`, `pre_discharge_window_start`/`_end`, `pre_discharge_solar_surplus_kwh`, `pre_discharge_target_kwh`, `pre_discharge_expected_kwh`, `pre_discharge_price_limit`, `pre_discharge_solar_credit_pct` and `pre_discharge_grid_dropped`.

**New: diagnostics export** *(optional package)*
- New package `optional packages/zendure_export_global.yaml` and a **Diagnostics export** block on the Settings tab. *Download export* saves one JSON file directly on your own device, with versions, active packages, all settings, the state of all sensors, the planner details, the collected data (all counters and 7-day statistics with their attributes), the external sensors you entered and the state of the Zendure automations. Nothing is stored in Home Assistant: `script.zendure_diagnostics_export` returns the export as its response and the browser turns it into a file.
- The button needs [button-card](https://github.com/custom-cards/button-card) (HACS); only this block uses it. Without button-card, or if downloading does not work in the app: Developer tools → Actions → *Zendure Diagnostics Export* → Perform action, and copy the response.
- The package also collects three logs: every line the automation writes to the logbook (last 50), a snapshot of mode, SOC, grid meter, power, price and plan every quarter hour (last 24 hours) and warnings and errors from the HA log that concern this set (last 20). For this the package turns on `system_log: fire_event: true`.
- IP addresses and serial numbers are left out. The automation does not need any changes.
- Also in the export: the plan timeline (`sensor.zendure_forecast_chart`: charging, battery, usage, solar and SOC per quarter hour) and Gielz' spread sensors with their attributes (difference value, average cheap and expensive price), so you see what the user sees on the dashboard.
- If the export gets too large for Home Assistant (256 kB), the largest single attributes are left out first; the planner attributes and Nord Pool's `raw_today`/`raw_tomorrow` go last. `meta.shortened` lists what was left out. Only if that is not enough, just the attribute names remain.
- The detailed solar forecast (Solcast `detailedForecast`, compact: start and estimate per period) is always included, even when the sensor is otherwise too large, as is the `_today` sensor the planner also reads that forecast from.

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

**Savings: stored solar energy counts for the solar panels** *(optional package)*
- The package tracks per quarter hour how much solar energy goes into the battery and which share of the battery content is solar energy. When discharging, that share counts as solar energy, valued at the price it saves at that moment. Stored solar energy therefore counts for the **solar panels** (without costs), no longer for the battery.
- Overview table: **solar panels** with the sub-rows *direct use and export* and *stored in the battery*; **dynamic tariff**; **battery and smart charging** (what remains: charging from the grid, its charge and discharge loss and energy still in the battery); **Actual costs** (was *Actually paid*). Energy table: row *solar into / out of the battery* (kWh).
- Block **Payback time** (was *Payback*): *Earned back* with the sub-rows *of which stored solar energy* and *of which smart charging*; the payback time itself is calculated as before from everything the battery yields. With negative earnings after more than a day of measuring the card now says *No payback time yet* instead of *Not enough data yet*, and the progress no longer shows *-0.0%*.
- Attributes of the savings sensors renamed: `solar` → `solar_panels` (with `solar_panels_direct_and_export` and `solar_panels_via_battery`), `battery` → `battery_and_smart_charging` (now without the solar energy), `paid` → `actual_costs`; `dynamic_tariff` unchanged. Payback time: new `of_which_solar_energy`, `of_which_smart_charging`, `battery_solar_share_pct`. The total and the payback time do not change.
- Counts from the upgrade; earlier quarter hours have no stored solar energy and stay with battery and smart charging. The battery content at the moment of upgrading counts as grid energy.

**Dashboard**
- **Optional packages show themselves:** Forecasting Configuration (Savings), (EV), (HVAC) and Diagnostics export are only on the Settings tab when the package is loaded. Without `zendure_savings_global.yaml` the Savings tab only shows a notice instead of empty cards.
- New **Optional packages** card on the Settings tab: per optional package whether it is loaded (✅/➖), the file and what it does, with a link to the explanation.
- **Plan Timeline** back in the first column below PV, as one card (`custom:mod-card`, needs card-mod), without the separate colour line below it.
- Plan for today: a line about the kWh the car still asks from the sun during the day.
- Charge block already running: *Plan for today* now shows the time left (*4 minutes left*) next to the kWh still to come, instead of the full 15 minutes. Attribute `charge_blocks`: `minutes` is the time left for a running block, new field `running`.
- `sensor.forecasting_version`: attribute `packages` (which optional packages are active) replaces `set`.

**Clearer what is optional**
- Required are `zendure_gielz1986_global.yaml`, `zendure_forecasting_global.yaml` and `zendure_negative_price_global.yaml`. Optional are `zendure_savings_global.yaml`, `zendure_ev_global.yaml`, `zendure_hvac_global.yaml` and `zendure_export_global.yaml`.
- The README has a **Packages** table: per file required or optional, what it does, what it needs and what you miss without it.
- **Optional packages in their own folder:** `zendure_savings_global.yaml`, `zendure_ev_global.yaml`, `zendure_hvac_global.yaml` and `zendure_export_global.yaml` are now in `Global (EN) Integration/optional packages` (NL: `Dutch (NL) Integration/optional packages`), no longer in `packages`. Copying the `packages` folder gives you only the base; you add optional packages deliberately.
- Every package has, right below the version header, the line `# OPTIONAL PACKAGE` (with what it needs) or `# REQUIRED PACKAGE`.

**For developers**
- New `tools` folder with a planner simulation: `planner_sim.py` calculates the plan outside Home Assistant with the states from a diagnostics export, `vergelijk.py` compares two planner versions on the same export. See `tools/README.md`.

**Fixed**
- **Minimal spread counted the loss twice:** the planner first subtracted the charge and discharge loss from the expensive price and then also required the minimal spread. With 25% and an 85% round trip the expensive quarter had to be about 47% more expensive than the charge quarter, and on flat days nothing was planned while Gielz showed a 35% spread. The planner now checks the minimal spread like Gielz on the gross price difference (expensive − cheap) / cheap, and separately that charging stays cheaper than buying later after the loss. Applies to today's charge slots, the path check and tomorrow's estimate.
- **Measured charge power hardly ever used:** *Forecast Grid Charge Power* was only available while charging from the grid, so *Forecast Measured Charge Power* (a statistic on it) became *unavailable* outside grid charging. The planner then used the configured charge power and only during charging the measured power, so the plan could shift once charging started. The sensor now keeps its last measurement (also after a restart).
- **Diagnostics export, error log:** the same message (e.g. the recorder warning about large attributes) is merged into one row with from, until and count, so it does not push out the rest.
- **Daily usage and self-consumption skewed after a restart:** the Zendure counters (charge, discharge, charge from solar) and *grid export from solar* were *unavailable* until the first quarter hour after a restart, because the Zendure had not reported power yet. The planner counted them as 0: the daily usage without battery charging and discharging and a self-consumption of 100%. Now these counters (also those of EV and HVAC) keep their previous value while the source is briefly gone, and the planner uses the previous value for a missing 7-day sensor (attributes `history_7_days` and `history_7_days_previous_value`; the source then shows *partly previous values*).
- **Diagnostics export, decision log:** repeats of the same message (only the numbers differ, e.g. *Discharge balancing* every 5 s) are merged into one row with from, until and count. That way 50 rows cover hours instead of a few minutes.
- **Solar production always *unavailable*:** the new solar counter missed two variables, so `sensor.forecast_counter_solar_production` was unavailable, the 7-day solar production stayed empty and the planner used start values (*History available: 0 of 7 days*). Fixed. After a restart at night without a reading, the counter waits until the inverter reports a value, and the first time it starts at the inverter reading (matching the old data points).
- **History:** the planner now takes the largest coverage of solar production, grid import and battery charging. Without solar panels, or when the solar counter is briefly missing, the history of the other counters counts.
- **Battery empty on the dashboard** (Plan for today and the path-check line) now takes solar, smart hold and pre-discharge into account, like the plan itself. Before it could say "empty at 21:20" while the battery was being saved for the morning peak. The plan itself does not change.
- **Diagnostics export:** the export failed on dates in attributes (`TypeError: Type is not JSON serializable: datetime.datetime`, e.g. with Nord Pool or `last_triggered`); dates and other objects are now included as text.
- **Diagnostics export:** configured fields with several sensors (comma list, e.g. own grid counters) are now listed with the external sensors too.

**Upgrading**
- Replace all files and **restart** Home Assistant.
- **Minimal spread:** it now means the same as in Gielz (gross, e.g. 25%). If you lowered it for the planner (e.g. to 3–6%) to work around the double loss, set it back to your usual value.
- **Note, optional packages moved:** they are now in the `optional packages` folder. If you only copy the new `packages` folder, your old `zendure_savings_global.yaml`, `zendure_ev_global.yaml`, `zendure_hvac_global.yaml` and `zendure_export_global.yaml` stay in your own packages folder. Replace them with the versions from `optional packages`, or remove the ones you do not use. An old `zendure_savings_global.yaml` next to the new `zendure_negative_price_global.yaml` causes a configuration error (see below).
- Always replace `zendure_savings_global.yaml` and `zendure_negative_price_global.yaml` together: if old and new versions are mixed, feed-in markup and bonus are defined twice and Home Assistant rejects the configuration.
- If `zendure_negative_price_global.yaml` is not yet in your `packages` folder, add it: it is now part of the base. The feature only acts once you turn on *No export at negative price*.
- `zendure_savings_global.yaml` is optional: if you do not want the Savings tab you can remove it. Feed-in markup and bonus are now in `zendure_negative_price_global.yaml` and keep working; you enter them in Forecasting Configuration (Negative Price).
- Optional: copy `zendure_ev_global.yaml`, `zendure_hvac_global.yaml` and/or `zendure_export_global.yaml` (Global) or `zendure_ev.yaml`, `zendure_hvac.yaml` and/or `zendure_export.yaml` (NL) from the `optional packages` folder to your `packages` folder. If you already have `system_log:` in `configuration.yaml`, remove the `system_log` block from the export package and set `fire_event: true` there.
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
