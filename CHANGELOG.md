# Changelog – Forecasting (EN)

Versions follow `year.month.sequence`; the sequence restarts at 1 every month. Each version states which Gielz version it is based on. [Nederlands](CHANGELOG.nl.md)

## 2026.11.5 (in development) — based on Gielz v20261113

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
- *Measured Charge Power* now uses the median instead of the mean. Old low readings drop out within 14 days; faster with *Reset usage data*.

**Input and detection**
- **Input fields cleaned up:** a new automation converts entered entities to lower case without spaces (e.g. `Sensor .solcast_…` from phone autocorrect becomes `sensor.solcast_…`). Applies to the forecasting, negative price, Nordpool, EV and HVAC fields and Gielz's Nordpool and grid meter sensor. Logged in the logbook.
- **HomeWizard in a Dutch-language Home Assistant** is now detected automatically (`sensor.p1_meter_energie_import` / `_export`).
- **Dashboard notice** (Zendure tab, Forecasting) when the solar panel counter or a custom grid counter does not point to an existing sensor.
- **Usage profile keeps learning without a valid solar panel counter:** if the field is empty or the sensor does not exist, the profile uses 0 solar production (previously learning stopped completely). If the counter drops out briefly, the previous measurement stays instead of disappearing.
- **Feed-in markup:** range now −0.50 to 0.50 €/kWh (was −1 to 1) and a warning in Forecasting Configuration (Negative Price) for a markup outside −0.10 to 0.10. A markup of −1.00 made the feed-in price always negative and blocked export permanently.
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

**Path check is now "Shortfall until the sun"**
- New text, for example: *Shortfall until the sun: without topping up, the battery is empty today around 08:21. Until tomorrow 01:45 the house would then buy 9.5 kWh, of which 7.9 kWh expensive (avg. €0.428). So 5.5 kWh charging 02:30–05:00 (10 quarter hours); 3.7 kWh of room stays free for the sun.* Makes clear that the purchase is without topping up, and why not everything is topped up (room for the sun).

**Upgrading**
- Replace `zendure_forecasting_global.yaml`, `zendure_negative_price_global.yaml`, the automation and the dashboard (optionally also `zendure_export_global.yaml`) and **restart** Home Assistant (new helpers). Paste the dashboard again via the Raw configuration editor.
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
