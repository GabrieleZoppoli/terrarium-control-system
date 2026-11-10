# Time-series review (R)

Structure of the daily cycle, a night-time thermal model, anomaly detection
and 24-hour forecast back-testing for the terrarium sensor history.

```bash
# R >= 4.3 with data.table, jsonlite, forecast, robustbase, strucchange
# (Debian/Ubuntu: apt install r-base-core r-cran-data.table r-cran-jsonlite \
#   r-cran-forecast r-cran-robustbase r-cran-strucchange)

# A. Historical snapshots kept in the terrarium-analysis repository
Rscript run_analysis.R --snapshots ../../../terrarium-analysis \
        --ledger data/ledger_history.csv --out out

# B. A full export from the Pi (scripts/export-history.sh)
Rscript run_analysis.R --export path/to/export --out out
```

Outputs in `out/`: `results.json` (every number and chart series),
`nights.csv`, `days.csv`, `anomaly_events.csv`.

| File | What |
|---|---|
| `load_data.R` | Readers for Influx CSV/JSON dumps; regular-grid builder |
| `run_analysis.R` | The analysis |
| `data/ledger_history.csv` | Weekly running totals recovered from the git history of `website/data/ledger.json` |

## Methods

* **Daily cycle**: three-harmonic cosinor on half-hour means; robust STL
  (period 288) on 5-minute data; strength = 1 - Var(remainder) / Var(seasonal + remainder).
* **Thermal model (lights off)**: `dT/dt = (T_room - T)/tau - k * freezer`,
  least squares on 5-minute steps. `k * tau` is the furthest the freezer can
  hold the cabinet below the room. Intervals from a bootstrap over whole nights.
* **Night floor**: nights with freezer duty >= 90 % count as flat out;
  `T_min = max(target, room - dT_sat)` with a 90 % t-interval.
* **Anomalies**: level detector (STL remainder / per-hour MAD, |z| >= 4.5 for
  15 min); jump detector (5-minute change minus the usual change for that
  half-hour, |z| >= 7; jumps near a mist event are labelled, sharp warm-ups in
  the dark with no mist are labelled door-like); day detector (robust
  Mahalanobis distance, MCD, on daily min/max temperature, mean/min humidity
  and freezer duty); regime shifts by least-squares break points.
* **Forecast back-test**: rolling origin, 24 h ahead in half-hour steps:
  yesterday; mean of the last 7 days; Fourier regression with ARMA errors;
  STL + ETS. Also reports how often the daily report's rule would flag
  ordinary hours, which is what its thresholds are calibrated on.

## Findings on the data available (4-18 Feb, 16 May-10 Jun 2026)

* Time constant about 150 min; cooling limit 8.6 °C (Feb) and 8.9 °C (Jun)
  below room, matching the earlier thermal-twin estimate.
* On flat-out nights the cabinet minimum sits 9.5 °C (sd 0.5) below the room's
  night average, so a 14 °C night target needs the room below about 23.5 °C.
* 24-hour temperature forecasts: mean absolute error about 0.65 °C; the
  7-day same-time mean is as good as the heavier models.
