# Zendure Home Assistant Integration
Choose your preferred language

 [![English 🌍 Global](https://img.shields.io/badge/English-Global-blue?style=for-the-badge)](README.md) [![Dutch 🇳🇱 NL](https://img.shields.io/badge/Dutch-NL-orange?style=for-the-badge)](README.nl.md)<br><br>

## 🔮 This fork: Forecasting mode

> **This is a fork of [Gielz1986/Zendure-HA-zenSDK](https://github.com/Gielz1986/Zendure-HA-zenSDK)** by Michiel Hofker (Gielz1986). All credit for the integration, the automation and the dashboard goes to the original project. This fork adds **one extra mode: Dynamic Smart Matching + Forecasting** (Dutch: *Dynamisch NOM + Forecasting*). For everything else (modes, wiki, support, updates), see the original repository. The original README follows below this section.

**Reference:** `FC-20261027` · based on Gielz configuration `v20261007` · available in Dutch (NL) and Global (EN).

### What the mode does

The battery charges at the cheapest moments, but **only as much as is actually needed**, taking into account your solar forecast, your usage and tomorrow's prices.

- Calculates a charging plan every minute (`sensor.zendure_forecast_plan`) with the state *Charge / Waiting / Not needed / Not favorable*.
- **Scenario A** (tomorrow cheaper or equal, or prices not yet known): charges enough to bridge until tomorrow's cheap moment or until there is enough sun, plus an adjustable margin.
- **Scenario B** (tomorrow more expensive): charges as full as possible, as long as the price now is lower than tomorrow's charging moment.
- Takes expected solar (today and tomorrow) into account, with a reliability percentage.
- **Solar self-consumption** is calculated from the last 7 days in kWh per day (on a dull day the percentage is higher than on a sunny one), with a manual override.
- **Average daily usage** comes from 7 days of history (import, export, production, battery in/out), with an adjustable starting value.
- **Efficiency filter:** a charge slot must be cheaper than the value of the stored energy after round-trip loss, and in scenario A below the day average.
- **Path check:** calculates when the battery runs empty and when energy comes in again: the first charge slot or the moment solar covers usage (from the Solcast detailed forecast, otherwise sunrise + 3 hours). If there is a gap, extra charge slots are planned before it, even when nothing else needs to be charged. Only the expensive slots in the gap count: a charge slot must lie before the expensive slot it replaces and be cheaper after round-trip loss.
- **Usage profile per hour**, separately for workdays and weekends: every full hour your actual house usage is measured and folded into a moving average per hour of the day (`sensor.forecast_usage_profile`). The planner uses it per quarter for the path check, the moment the battery runs empty, solar coverage and the bridge. Until an hour has enough measurements (workday 3, weekend 2), the day average applies. Holidays follow `binary_sensor.workday_sensor` (Workday integration) if it exists.
- **Measured charge power** is used to determine the number of slots.
- Optional: **hold discharging in a cheap dip** (save the battery).
- **Plan Timeline** on the dashboard: for the next 36 hours per price slot the price (green/orange/red), solar, battery charge and discharge, expected state of charge, grid import and export and house usage. Only apexcharts-card needed. Tip: exclude `sensor.zendure_forecast_chart` from the recorder (`recorder: exclude: entities:`), its attributes exceed the recorder's 16 kB limit.
- Dashboard: a Forecasting section on the Zendure tab (plan for today and tomorrow, tiles, collected 7-day data, recalculate button) and a Configuration (Forecasting) block with all input fields. Both can be shown or hidden with **Show Forecasting On Dashboard**.

### What changed compared with the original

| File (NL / Global) | Change |
|---|---|
| `packages/zendure_forecasting.yaml` / `packages/zendure_forecasting_global.yaml` | **New.** Helpers, counters, 7-day statistics, the planner and derived sensors. |
| `packages/zendure_gielz1986_nl.yaml` / `packages/zendure_gielz1986_global.yaml` | Only one extra option in the mode selector. |
| `automation_nl.yaml` / `automation_global.yaml` | The new mode in the mode selection and in the 6 existing Smart Matching lists (zero-on-the-meter, SOC protection, emergency stop), its own charging block that only charges when the plan says *Charge*, and a discharge hold for the cheap dip. Existing modes are unchanged. |
| `dashboard_nl.yaml` / `dashboard_global.yaml` | New Forecasting section, new Configuration (Forecasting) block and a switch in Configuration (Dashboard). |

Each changed file starts with a two-line header with the reference and the original author.

### Installation

First install the original integration as described below (packages file, automation, dashboard). Then:

1. Put `zendure_forecasting_global.yaml` (Global) or `zendure_forecasting.yaml` (NL) in the same `packages` folder as the Gielz package, and replace the Gielz package with the version from this fork.
2. Replace the automation and the dashboard with the versions from this fork (or merge the changes into your own version).
3. Restart Home Assistant.
4. On the Configuration tab, under **Configuration (Forecasting)**, enter: the sensor for solar remaining today, solar tomorrow (kWh, e.g. Forecast.Solar or Solcast) and a total counter of your solar panels (kWh). Optionally set the default daily usage and the charge margin.
5. Select the mode **Dynamic Smart Matching + Forecasting**.

**Requires:** the Gielz package, Nord Pool (as already set up in Gielz), a P1/home energy meter, a solar forecast integration and apexcharts-card for the Gielz dashboard. The planner becomes more accurate after about a week of history.

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
| **Configuration (Basic)** | **Information** |
| `zendure_setting_ip_address` | **e.g. 192.168.0.172** – Found in the Zendure app under device information. |
| `homewizard_setting_p1_ip_address` | **e.g. 192.168.0.192** – Enable local API in the Homewizard app |
| `zendure_setting_standby_delay` | **(Recommended: 15 minutes) 5–30 minutes** – Defines how quickly the inverter goes into full standby at 0 activity. Prevents ~19W idle consumption. |
| `zendure_setting_set_default_settings` | Once the battery is running, you can use this to apply the recommended settings below. |
| **Configuration (Charging)** | **Information** |
| `zendure_setting_max_charge_power` | **400–2400W** – Maximum charging power (up to 7200W with multiple inverters via Node-RED). |
| `zendure_setting_start_charging_at` | **(Recommended: -300W) -1000 to -80W** – Defines when charging starts. |
| `zendure_setting_charge_buffer` | **(Recommended: 50W) 0–250W** – Determines how much less to include during charging. In summer you can increase this (e.g. 200W) to prevent daytime grid import. |
| **Configuration (Discharging)** | **Information** |
| `zendure_setting_max_discharge_power` | **400–2400W** – Maximum discharge power (up to 7200W with multiple inverters via Node-RED). |
| `zendure_setting_start_discharging_at` | **(Recommended: 100W) 80–500W** – Defines when discharging starts. |
| `zendure_setting_discharge_buffer` | **(Recommended: 5W) 0–250W** – Extra margin for discharging. |
| **Configuration (State Of Charge)** |**Information**|  
| `zendure_setting_soc_protection_disabled`    | Check this to disable the dual SOC protection. When the battery drops below the minimum allowed charge percentage, it will no longer automatically recharge. It will wait until the BMS (Battery Management System) takes action. |  
| `zendure_setting_minimum_allowed_state_of_charge` | **(Recommended: 10%) 5% to 50%** – Set the minimum allowed state of charge percentage here. | 
| `zendure_setting_maximum_allowed_state_of_charge` | **(Recommended: 100%) 70% to 100%** – Set the maximum allowed state of charge percentage here. At 100%, an SOC calibration is performed to accurately estimate the state of charge level. | 
| **Configuration (PV)** |**Information**|  
| `zendure_setting_pv_export_disabled`    | Check this to disable the pv export. When the battery is full it will no longer export the energy of connected solarpanels. | 
| **Configuration (Optional)** | **Information** |
| `home_energy_setting_meter_sensor` | **e.g. sensor.custom_energy** – Add your own home energy sensor (+watt import / -watt export). This will take priority. [Go to WIKI](https://github.com/Gielz1986/Zendure-HA-zenSDK/wiki/Global-and-NL-%E2%80%90-P1-CT-meters-(API's))) for P1/CT API's. |
| `zendure_setting_battery_order` | **e.g. 1;5;3;4;2** – Manually define battery order based on serial numbers and physical stacking. |
| **Configuration (Dynamic)** | **Information** |
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
