# Changelog – Forecasting (EN)

Versions follow `year.month.sequence`; the sequence restarts at 1 every month. Each version states which Gielz version it is based on. [Nederlands](CHANGELOG.nl.md)

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
