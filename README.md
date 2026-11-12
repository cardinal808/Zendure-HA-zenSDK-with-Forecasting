# Zendure Home Assistant Integration
Choose your preferred language

 [![English 🌍 Global](https://img.shields.io/badge/English-Global-blue?style=for-the-badge)](README.md) [![Dutch 🇳🇱 NL](https://img.shields.io/badge/Dutch-NL-orange?style=for-the-badge)](README.nl.md)<br><br>

## 🔮 This fork: Forecasting mode

> **This is a fork of [Gielz1986/Zendure-HA-zenSDK](https://github.com/Gielz1986/Zendure-HA-zenSDK)** by Michiel Hofker (Gielz1986). All credit for the integration, the automation and the dashboard goes to the original project. This fork adds **one extra mode: Dynamic Smart Matching + Forecasting** (Dutch: *Dynamisch NOM + Forecasting*). For everything else (modes, wiki, support, updates), see the original repository. The original README follows below this section.

**Version:** `2026.11.4` · based on Gielz configuration `v20261007` · available in Dutch (NL) and Global (EN) · [Changelog](CHANGELOG.md)

Versions follow `year.month.sequence` (the sequence restarts at 1 every month). In Home Assistant you see the installed version and the latest version on GitHub (`sensor.forecasting_version`, `sensor.forecasting_release_check`) on the Configuration tab, and the release notes under Releasenotes.

### What the mode does

The battery charges at the cheapest moments, but **only as much as is actually needed**, taking into account your solar forecast, your usage and tomorrow's prices.

- Calculates a charging plan every minute (`sensor.zendure_forecast_plan`) with the state *Charge / Waiting / Not needed / Not favorable*.
- **Scenario A** (tomorrow cheaper or equal, or prices not yet known): charges enough to bridge until tomorrow's cheap moment or until there is enough sun, plus an adjustable margin.
- **Scenario B** (tomorrow more expensive): charges as full as possible, as long as the price now is lower than tomorrow's charging moment.
- Takes expected solar (today and tomorrow) into account, with a reliability percentage.
- **Solar self-consumption** is calculated automatically from day 1: on the first day as a percentage of production, after that in kWh per day over up to 7 days (on a dull day the percentage is higher than on a sunny one). No input field needed.
- **Average daily usage** comes from your own history (import, export, production, battery in/out): calculated from about 2 hours after installation and more accurate every day, up to 7 days. No input field needed.
- **Grid import and export from the P1 meter:** the meter's kWh counters are detected automatically (SlimmeLezer/ESPHome DSMR: `energy_consumed/produced_tariff_1/2`, HomeWizard P1, DSMR integration) and used, just like the energy dashboard. Without a meter it is calculated from power (method left). If the meter is briefly gone, the missed part is added later.
- **Efficiency filter:** a charge slot must be cheaper than the value of the stored energy after round-trip loss, and in scenario A below the day average. The round-trip efficiency comes from the **total RTE** (all kWh out / all kWh in), split equally over charging and discharging. The 24-hour point measurements of efficiency come out too low (unweighted, every stop counts as 0%) and are only used when the total RTE is not usable yet.
- **Path check:** calculates when the battery runs empty and looks from there until solar covers usage (from the Solcast detailed forecast, otherwise sunrise + 3 hours) or until the end of the bridge, whichever comes first. Expensive quarter hours in that gap get the cheapest charge slots before them, even when nothing else needs to be charged, and only if those are cheaper after round-trip loss. With *hold discharging in a cheap dip* on, the path check assumes the battery supplies nothing in those dips.
- **Usage profile per hour**, separately for workdays and weekends: every full hour your actual house usage is measured and folded into a moving average per hour of the day (`sensor.forecast_usage_profile`). It also learns per hour how usage is spread over the four quarters (e.g. cooking from half past five); that shape learns slowly and only spreads the hourly total. The planner uses it per quarter for the path check, the moment the battery runs empty, solar coverage and the bridge. Until an hour has enough measurements (workday 3, weekend 2), the day average applies. Holidays follow `binary_sensor.workday_sensor` (Workday integration) if it exists.
- **Measured charge power** is used to determine the number of slots.
- **Smart hold** (on by default): if the battery will not last until the end of the gap and no charge moment is left, it keeps its charge for the most expensive quarter hours. Between two charge slots it does not supply when the price now is lower than the next charge slot after loss.
- Optional: **hold discharging in a cheap dip** (save the battery), when grid charging is still needed.
- **Charge blocks in plain language:** per block when, how long, how many kWh and at what average price, for today and (indicatively) for tomorrow.
- **Savings** *(optional package `zendure_savings_global.yaml`)*: every quarter hour your usage is settled at a fixed and a dynamic tariff, with and without solar and battery. A separate tab shows per day, month, year and total what you save and from what (solar, dynamic tariff, battery and smart charging), plus the battery payback time. The tables look better with [card-mod](https://github.com/thomasloven/lovelace-card-mod) (optional).
- **No export at a negative price** (`zendure_negative_price_global.yaml`, part of the base set): when the feed-in price (market price + bonus + markup) is negative, it disables the Zendure PV export. Optionally it also limits one or two external inverters (production limit on the grid meter, export limit, switch or script). It only restores what it changed itself.
- **Electric car** *(optional package `zendure_ev_global.yaml`)*: for a charger without its own control (granny charger, or a wallbox behind a smart switch) with a power measurement, e.g. a Shelly 1PM. The battery then no longer discharges into the car, and the car's charging does not count in the planner's usage profile, daily usage and self-consumption. With a switch you can also plan a charging session: *Night* charges the required kWh in the cheapest price slots until a set time, *Daytime* charges on solar and the planner then charges the battery extra from the grid at the cheapest moment.
- **Air conditioning (HVAC)** *(optional package `zendure_hvac_global.yaml`)*: the AC does not run from the battery, configurable per mode (e.g. not when heating, allowed when cooling) and optionally allowed in an expensive hour. Choose whether the battery then does not discharge at all, or only subtracts the AC power from the grid meter (with a power measurement); that AC usage then also does not count in the usage profile. Charging keeps working.
- **Diagnostics export** *(optional package `zendure_export_global.yaml`)*: one button saves a JSON file directly on your own device, with your settings, sensor states, planner details and the logs of the last 24 hours, to attach to a question or issue. IP addresses and serial numbers are left out. The button uses [button-card](https://github.com/custom-cards/button-card) (HACS); without button-card it works via Developer tools → Actions.
- **Optional packages show themselves:** the Forecasting Configuration (Savings), (EV), (HVAC) and Diagnostics export blocks are only on the dashboard when the matching package is loaded. The **Optional packages** card on the Settings tab shows which ones are loaded and what the others do. See [Packages](#packages).
- **Plan Timeline** on the dashboard: for the next 36 hours per price slot in four compact rows the price (colours as in Gielz: green = planned charging, red = expensive), solar and house usage, battery charge and discharge with the expected state of charge, and grid import and export. As one card via `custom:mod-card`, so card-mod (HACS) is needed. Tip: exclude `sensor.zendure_forecast_chart` from the recorder (`recorder: exclude: entities:`), its attributes exceed the recorder's 16 kB limit.
- Dashboard: a Forecasting section on the Zendure tab (plan for today and tomorrow, usage profile, collected 7-day data, recalculate button), a Savings tab and a Forecasting Configuration (Basic) block with all input fields. Both can be shown or hidden with **Show Forecasting On Dashboard**.

### Packages

The set consists of a base you always need and five optional packages. The base is in the `packages` folder, the optional packages are in the `optional packages` folder. If you only copy the `packages` folder, you get exactly the base. You add an optional package by putting its file from `optional packages` in your own `packages` folder and restarting Home Assistant; removing it and restarting turns the feature off again. The automation and the dashboard work with and without the optional packages.

| Package | File (Global / NL) | | What it does | Needs | Without this package |
|---|---|---|---|---|---|
| Gielz | `zendure_gielz1986_global.yaml` / `zendure_gielz1986_nl.yaml` | **Required** | The original integration, with one extra mode in the selector. | – | Nothing works. |
| Forecasting | `zendure_forecasting_global.yaml` / `zendure_forecasting.yaml` | **Required** | The Dynamic Smart Matching + Forecasting mode: counters, statistics, planner. | Solar forecast, grid meter, Nord Pool | No forecasting mode. |
| Negative price | `zendure_negative_price_global.yaml` / `zendure_negatieve_prijs.yaml` | **Required** | No export when exporting costs money; optionally limits external inverters. | – | Export continues, also at a negative price. |
| Savings | `zendure_savings_global.yaml` / `zendure_besparing.yaml` | Optional | Savings tab: what solar, the battery and a dynamic contract earn, battery payback time. | card-mod for the styling (recommended) | The Savings tab shows a notice. Feed-in markup and bonus are then in Forecasting Configuration (Negative Price). |
| EV | `zendure_ev_global.yaml` / `zendure_ev.yaml` | Optional | Charge the car without the battery discharging into it; night or daytime charging session. | Power measurement of the charger (e.g. Shelly 1PM); a switch for a charging session | The battery can discharge into the car; charging counts in the usage profile. |
| HVAC | `zendure_hvac_global.yaml` / `zendure_hvac.yaml` | Optional | AC not from the battery, per AC mode: no discharging or subtract the AC power; AC usage then kept out of the usage profile. | `climate.*`, power sensor or switch of the AC; a power measurement for subtracting | Discharging continues while the AC runs. |
| Nordpool | `zendure_nordpool_global.yaml` / `zendure_nordpool.yaml` | Optional | Two Nord Pool sensors: all-in price for supply (market price + energy tax + markup, with VAT) and bare market price with VAT for export, with input fields for the amounts. | Nord Pool integration (HACS); remove your own Nord Pool YAML with the same settings | You set up the Nord Pool sensor(s) yourself. |
| Diagnostics export | `zendure_export_global.yaml` / `zendure_export.yaml` | Optional | One JSON file with settings, sensors and logs, to attach to a question or issue. | button-card (HACS) for the download button; turns on `system_log: fire_event: true` | No export; sharing data is manual. |

Every optional file has the line `# OPTIONAL PACKAGE` right below the version header, the required ones `# REQUIRED PACKAGE`, so you can see in the folder which ones you can leave out.

### What changed compared with the original

| File (NL / Global) | Change |
|---|---|
| `packages/zendure_forecasting.yaml` / `packages/zendure_forecasting_global.yaml` | **New.** Helpers, counters, 7-day statistics, the planner and derived sensors. |
| `optional packages/zendure_besparing.yaml` / `optional packages/zendure_savings_global.yaml` | **New, optional.** Input fields for tariffs and battery price, and the savings and payback sensors. |
| `packages/zendure_negatieve_prijs.yaml` / `packages/zendure_negative_price_global.yaml` | **New.** Feed-in price, no export at a negative price, limiting external inverters. Uses the feed-in markup and bonus from the savings package when that is loaded. |
| `optional packages/zendure_ev.yaml` / `optional packages/zendure_ev_global.yaml` | **New, optional.** The car's charging power and discharge correction, kWh counters, charge plan (night/daytime) and charger control. |
| `optional packages/zendure_hvac.yaml` / `optional packages/zendure_hvac_global.yaml` | **New, optional.** AC helpers, `binary_sensor.hvac_ontladen_geblokkeerd` / `binary_sensor.hvac_discharge_blocked`, `sensor.hvac_ontlaad_correctie` / `sensor.hvac_discharge_correction` and the separate AC counters. |
| `optional packages/zendure_nordpool.yaml` / `optional packages/zendure_nordpool_global.yaml` | **New, optional.** Nord Pool sensors for supply (all-in) and export (bare market price with VAT), with input fields for energy tax, markup and VAT. |
| `optional packages/zendure_export.yaml` / `optional packages/zendure_export_global.yaml` | **New, optional.** Decision log, snapshots, error log and the export script. Turns on `system_log: fire_event: true`. |
| `packages/zendure_gielz1986_nl.yaml` / `packages/zendure_gielz1986_global.yaml` | Only one extra option in the mode selector. |
| `automation_nl.yaml` / `automation_global.yaml` | The new mode in the mode selection and in the 6 existing Smart Matching lists (zero-on-the-meter, SOC protection, emergency stop), its own charging block that only charges when the plan says *Charge*, a discharge hold for the cheap dip and for the AC, and in the Smart Matching discharge blocks the car's charging power and (optionally) the AC power subtracted from the grid meter. Without the optional packages everything works as before. Existing modes are otherwise unchanged. |
| `dashboard_nl.yaml` / `dashboard_global.yaml` | New Forecasting section, new Savings tab, new Forecasting Configuration (Basic) and (Negative Price) blocks, the optional Forecasting Configuration (Savings), (EV), (HVAC) and Diagnostics export blocks (only visible when the package is loaded), the Optional packages card and a switch in Configuration (Dashboard). |

Each changed file starts with a two-line header with the version, the Gielz version it is based on and the original author.

### Installation

First install the original integration as described below (packages file, automation, dashboard). Then:

1. Put the **required** files `zendure_forecasting_global.yaml` and `zendure_negative_price_global.yaml` (Global) or `zendure_forecasting.yaml` and `zendure_negatieve_prijs.yaml` (NL) in the same `packages` folder as the Gielz package, and replace the Gielz package with the version from this fork.
   Then choose which **optional** packages you want (see [Packages](#packages)) and copy them from the `optional packages` folder into the same `packages` folder: `zendure_savings_global.yaml`, `zendure_ev_global.yaml`, `zendure_hvac_global.yaml`, `zendure_export_global.yaml` (Global) or `zendure_besparing.yaml`, `zendure_ev.yaml`, `zendure_hvac.yaml`, `zendure_export.yaml` (NL). Only copy the files you want; whatever is in `packages` gets loaded.
2. Replace the automation and the dashboard with the versions from this fork (or merge the changes into your own version).
3. Restart Home Assistant.
4. On the Configuration tab, under **Forecasting Configuration (Basic)**, enter: the sensor for solar remaining today, solar tomorrow (kWh, e.g. Forecast.Solar or Solcast) and a total counter of your solar panels (kWh). Optionally set the charge margin. With the savings package, enter your tariffs and the purchase price of the battery under **Forecasting Configuration (Savings)**.
5. Select the mode **Dynamic Smart Matching + Forecasting**.

**Requires:** the Gielz package, Nord Pool (as already set up in Gielz), a P1/home energy meter, a solar forecast integration and apexcharts-card for the Gielz dashboard and card-mod (for the Plan Timeline and, with the savings package, the table styling on the Savings tab). What the optional packages need is in the [Packages](#packages) table. The planner becomes more accurate after about a week of history.

> **Status:** personal project. The Dutch version is in use by the author. The Global (EN) version is a translation of the Dutch set: it was checked offline (the planner gives the same results as the Dutch version in 400 simulated situations), but has not yet run in a live Home Assistant. No warranty: start with a low charge margin and check the plan on the dashboard.

### Pros and cons

**Compared with the original Dynamic Smart Matching mode**

| ➕ Pros | ➖ Cons |
|---|---|
| Charges only what is needed instead of a fixed number of cheap periods: fewer unnecessary grid kWh and cycles. | More to set up: a solar forecast integration and a total counter for your solar panels. |
| Uses your solar forecast, so a sunny day ahead means less grid charging. | Needs about a week of history before usage and self-consumption are measured; until then it uses default values. |
| Looks at tomorrow's prices (scenario A/B) and checks whether the battery lasts until the first charge slot. | Only as good as your solar forecast; the reliability setting helps, but cannot fix a poor forecast. |
| Adapts to your system: measured efficiency, measured charge power, 7-day self-consumption. | Extra sensors and a planner that recalculates every minute. |
| The plan is fully visible on the dashboard, with a recalculate button. | Rule-based: a good plan, not a mathematically proven optimum. |

**Compared with a full optimizer such as [Day Ahead Optimizer (DAO)](https://github.com/corneel27/day-ahead)**

| This fork | DAO |
|---|---|
| No extra software: everything is YAML in Home Assistant, no add-on or Docker. | A Home Assistant add-on (or Docker container) with its own configuration. |
| An extra mode on top of your existing Gielz setup, not a separate system controlling the Zendure. | A separate system that schedules your devices. |
| Uses your own solar forecast sensors. | Uses weather data from Meteoserver. |
| Battery only. | Battery, heat pump, boiler, EV and more. |
| Rule-based plan (scenario A/B, path check, efficiency filter). | Mathematical optimization over all hours at once. |
| Young project, not widely tested. | Established project with a community and a wiki. |

In short: if you only want to optimize your Zendure battery without an extra add-on, this mode is a good fit. If you want to schedule battery, heat pump/boiler and EV together with a real optimizer, DAO is the more logical route. They don't exclude each other: this mode can stay as a fallback.

### License

This fork falls under the same license as the original ([LICENSE](LICENSE)): **personal and strictly non-commercial use only**, sharing and modifying allowed with the full license text included and the modifications stated (see the table above). Commercial use requires permission from the original author.

---

*Below: the original README by Gielz1986.*


![Preview](Images/Global-Dashboard-290526.gif)
<a href="https://github.com/Gielz1986/Zendure-HA-zenSDK/wiki/Global-%E2%80%90-Available-entities">
Go to the explanation of all entities and the dashboard
</a>


<br>

**Get your battery running locally in Home Assistant in just 2️⃣ simple steps.**

Based on the zenSDK RESTful API for Home Assistant. This package connects locally to one **Zendure Solarflow 2400 (AC, AC+ or AC Pro) / Zendure Solarflow 1600 AC+ / Zendure Solarflow 800 (Pro(2) or Plus) / Zendure Solarflow 3000 Mix AC+ / Zendure Solarflow 4000 Mix (AC+ or Pro)**. Perfect for anyone who wants to run their battery **100% local** in Home Assistant. There are now **11 preconfigured modes** — from relaxed solar-based usage to acting like an energy trader with dynamic pricing for a few extra cents.

Several integration add-ons are also available, including support for multiple inverters and older models such as the SolarFlow Hyper 2000. See [Integration add-ons](#-optional-integration-add-ons) for a complete overview.

Do you find this project useful and want to support further development?  
Buy me a coffee ☕️ and follow this GitHub repository ⭐⭐⭐.

<a href="https://www.buymeacoffee.com/gielz" target="_blank">
  <img src="https://github.com/Gielz1986/Zendure-zenSDK-HA/blob/main/Images/bmc.png?raw=true" width="120" alt="Buy Me a Coffee">
</a><br><br>


## 1️⃣ Making Entities Available

#### ℹ️ Required Hardware

- Homewizard P1 (or another home energy meter that provides per-second data (+watt import / -watt export)).
- One Solarflow 2400 (AC, AC+ or AC Pro) / Solarflow 1600 AC+ / Solarflow 800 (Pro(2) or Plus) / Solarflow 3000 Mix AC+ / Solarflow 4000 Mix (AC+ or Pro).
- Or mutiple identical inverters combined with the [Node-RED proxy by Gast777](https://github.com/gast777/Zendure-zenSDK-proxy)

---

### #️⃣ Configuration and Restart

1. Make sure **HEMS is disabled** in the Zendure app.
2. Place [Zendure_gielz1986_global.yaml](./Global%20(EN)%20Integration/packages/zendure_gielz1986_global.yaml) from the GitHub packages folder into your Home Assistant `packages` folder. If it does not exist, create it.
3. Create a **backup** of your `configuration.yaml`.
4. Then edit your `configuration.yaml` and add the following:

```
homeassistant:
  packages: !include_dir_named packages
```

| ![Preview](Images/packages2.png) |
|-----------------------------------|

5. Restart Home Assistant.
6. Optionally create the plug-n-play dashboard [Go to Plug-N-Play Dashboard](#-optional-plug-n-play-dashboard). Or fill in the entities below in Home Assistant and restart again.
7. Go to [part 2](#2️⃣-zendure-zensdk-gielz-automation) to not only read data but also use the battery with an single automation.


---

<img alt="image" src="https://github.com/user-attachments/assets/c3dc867f-6022-4d12-8926-0e593f411856" />
*plug-n-play dashboard

<br>
<br>

| Explanation per configuration item | |
|-|-|
| **Gielz Configuration (Basic)** | **Information** |
| `zendure_setting_ip_address` | **e.g. 192.168.0.172** – Found in the Zendure app under device information. |
| `homewizard_setting_p1_ip_address` | **e.g. 192.168.0.192** – Enable local API in the Homewizard app |
| `zendure_setting_standby_delay` | **(Recommended: 15 minutes) 5–30 minutes** – Defines how quickly the inverter goes into full standby at 0 activity. Prevents ~19W idle consumption. |
| `zendure_setting_set_default_settings` | Once the battery is running, you can use this to apply the recommended settings below. |
| **Gielz Configuration (Charging)** | **Information** |
| `zendure_setting_max_charge_power` | **400–2400W** – Maximum charging power (up to 7200W with multiple inverters via Node-RED). |
| `zendure_setting_start_charging_at` | **(Recommended: -300W) -1000 to -80W** – Defines when charging starts. |
| `zendure_setting_charge_buffer` | **(Recommended: 50W) 0–250W** – Determines how much less to include during charging. In summer you can increase this (e.g. 200W) to prevent daytime grid import. |
| **Gielz Configuration (Discharging)** | **Information** |
| `zendure_setting_max_discharge_power` | **400–2400W** – Maximum discharge power (up to 7200W with multiple inverters via Node-RED). |
| `zendure_setting_start_discharging_at` | **(Recommended: 100W) 80–500W** – Defines when discharging starts. |
| `zendure_setting_discharge_buffer` | **(Recommended: 5W) 0–250W** – Extra margin for discharging. |
| **Gielz Configuration (State Of Charge)** |**Information**|  
| `zendure_setting_soc_protection_disabled`    | Check this to disable the dual SOC protection. When the battery drops below the minimum allowed charge percentage, it will no longer automatically recharge. It will wait until the BMS (Battery Management System) takes action. |  
| `zendure_setting_minimum_allowed_state_of_charge` | **(Recommended: 10%) 5% to 50%** – Set the minimum allowed state of charge percentage here. | 
| `zendure_setting_maximum_allowed_state_of_charge` | **(Recommended: 100%) 70% to 100%** – Set the maximum allowed state of charge percentage here. At 100%, an SOC calibration is performed to accurately estimate the state of charge level. | 
| **Gielz Configuration (PV)** |**Information**|  
| `zendure_setting_pv_export_disabled`    | Check this to disable the pv export. When the battery is full it will no longer export the energy of connected solarpanels. | 
| **Gielz Configuration (Optional)** | **Information** |
| `home_energy_setting_meter_sensor` | **e.g. sensor.custom_energy** – Add your own home energy sensor (+watt import / -watt export). This will take priority. [Go to WIKI](https://github.com/Gielz1986/Zendure-HA-zenSDK/wiki/Global-and-NL-%E2%80%90-P1-CT-meters-(API's))) for P1/CT API's. |
| `zendure_setting_battery_order` | **e.g. 1;5;3;4;2** – Manually define battery order based on serial numbers and physical stacking. |
| **Gielz Configuration (Dynamic)** | **Information** |
| `dynamic_setting_nordpool_sensor` | **e.g. sensor.nordpool_kwh_nl_eur_3_09_0** – Your Nordpool (HACS) sensor. |
| `dynamic_export_correction` | Specify how many cents should be subtracted during export. This value is used in the spread calculation. |
| `dynamic_setting_minimal_spread` | **e.g. 25%** – Minimum price spread before dynamic charging/discharging activates. |
| `dynamic_setting_15_minute_interval` | Enable this if you want to use 15-minute intervals. |
| **Configuration (Dashboard)** | **Information** |
| `dashboard_setting_show_help` | Enable to show help text on the dashboard. |
| `dashboard_setting_show_pv` | Enable to show connected (offgrid/mppt) PV on the dashboard. |
| `dashboard_setting_show_dynamic` | Enable to show dynamic control on the dashboard. |

---

## 2️⃣ Zendure zenSDK (Gielz) Automation

The engine of everything: it charges smartly, discharges smartly, and ensures everything works together. Choose from 11 different modes to make it behave exactly how you want.

If you didn’t change any entity names above, you can simply create this automation:

1. Create a new automation.
2. Click **Edit in YAML**.
3. Paste the YAML code from [Automation_global.yaml](./Global%20(EN)%20Integration/automation_global.yaml).
4. Save and start the automation.

![Preview](Images/Global-Automation-300326.gif)  
![Preview](Images/Global-Automation2-300326.gif)

---

## ✅ Battery Ready to Go

The moment has arrived: time for your battery to prove it’s more than just an expensive decoration with cables.

1. Open the plug-n-play dashboard or add the entity **Zendure Operation Mode**.
2. The mode will be set to **Standby**.
3. Select your desired mode to activate the **Zendure zenSDK (Gielz)** automation.
4. The battery will with the desired operation mode.

![Preview](Images/Mode-290326.gif)  
<a href="https://github.com/Gielz1986/Zendure-HA-zenSDK/wiki/Global-%E2%80%90-Operation-modes">
Go to the explanation of all modes
</a>


---

## 🔃 (Optional) Plug-N-Play Dashboard

You can now also directly use a fully plug-n-play dashboard:

1. Requires [Apexcharts HACS](https://github.com/RomRider/apexcharts-card) and (optionally) [Graphite HACS](https://github.com/TilmanGriesel/graphite).
2. Create a new empty dashboard via ⚙️ and go to **Dashboards**.
3. Click **Add Dashboard** and choose **New dashboard from scratch**
4. Open the new dashboard.
5. Click on the 3 dots → **Edit Dashboard**.
6. Click on the 3 dots → **Raw configuration editor**.
7. Paste the YAML from [Dashboard_global.yaml](./Global%20(EN)%20Integration/dashboard_global.yaml).
8. Save — dashboard is ready to use.
9. [Go to the WIKI](https://github.com/Gielz1986/Zendure-HA-zenSDK/wiki/Global-%E2%80%90-Available-entities) for explanation of all entities.

![Preview](Images/Global-Plug-N-Play-Dashboard.gif)

---

## 🔃 (Optional) Integration add-ons

Several users have created additional code to integrate directly with this integration. They are listed below.

| Extra add-ons | Use case | Information |
|-|-|-|
| [Node-RED proxy](https://github.com/gast777/Zendure-zenSDK-proxy) from [@gast777](https://github.com/gast777) | Multiple inverters in use | Then you can expand this with this Node-RED proxy. This proxy ensures everything in this automation works seamlessly together, allowing multiple identical inverters to be controlled intelligently with optimal power distribution.  |
| [Node-RED proxy (Hyper 2000)](https://github.com/twoenter/Zendure-zenSDK-Hyper-proxy) from [@twoenter](https://github.com/twoenter) | SolarFlow Hyper 2000 user | Then you can use this add-on to connect Zendure Home Assistant (MQTT/Cloud) through a Node-RED proxy and gain access to all the features of this integration. |
