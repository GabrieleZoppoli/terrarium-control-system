# Time-series review (R)

Structure of the daily cycle, a night-time thermal model, anomaly detection
and 24-hour forecast back-testing for the terrarium sensor history.

**Missing data and anomalies are removed before anything is estimated.**
Nothing is filled in.

```bash
# R >= 4.3 with data.table, jsonlite, forecast, robustbase, strucchange
# (Debian/Ubuntu: apt install r-base-core r-cran-data.table r-cran-jsonlite \
#   r-cran-forecast r-cran-robustbase r-cran-strucchange)

# A. Historical snapshots kept in the terrarium-analysis repository
Rscript run_analysis.R --snapshots ../../../terrarium-analysis \
        --ledger data/ledger_history.csv --out out

# B. A full export from the Pi (scripts/export-history.sh)
Rscript run_analysis.R --export path/to/export --out out

# Same analysis without the cleaning step, to see what cleaning changes
Rscript run_analysis.R --snapshots ... --out out_raw --no-clean
```

Outputs in `out/`: `results.json` (every number and chart series),
`nights.csv`, `days.csv`, `anomaly_events.csv`.

| File | What |
|---|---|
| `load_data.R` | Readers for Influx CSV/JSON dumps; regular-grid builder |
| `clean.R` | Cleaning rules, gap-tolerant STL, the detect-remove-refit loop |
| `run_analysis.R` | Load, clean, analyse, report |
| `data/ledger_history.csv` | Weekly running totals recovered from the git history of `website/data/ledger.json` |

## Order of work

1. **Load** every source onto regular 5- and 30-minute grids.
2. **Clean.** A reading is used only if it is
   * measured: not missing, not within 6 h after an outage of an hour or
     more, not a value carried forward while the system was down, not a
     sensor flat-lined for an hour;
   * not anomalous: outside every level anomaly (remainder / per-hour MAD,
     |z| >= 4.5 for 15 min, padded 10 min) and every unexplained jump
     (5-minute change minus the usual change for that half hour, |z| >= 7);
   * not on a day with more than 15 % of its time flagged.

   Detection and estimation are iterated: fit on clean rows, flag, remove,
   refit, until the clean set stops changing (3-4 passes here). Two guards
   keep the loop honest: spreads are always computed over all measured rows
   (a spread recomputed on trimmed data shrinks every pass and the flags run
   away), and a removed row is never re-admitted.

   Jumps under 1 °C within 10 minutes of a freezer or lights switch or a
   mist are **control actions**: normal operation, recorded but kept. They
   are also the rows that identify the freezer's strength.
3. **Analyse** clean rows only.
4. **Report** what was removed, the events found, and the estimates.

## Methods

* **Decomposition**: STL (seasonal-trend by loess) in a version that skips
  removed rows instead of needing a complete series, with STL's bisquare
  robustness passes. On gap-free data it matches `stats::stl(robust = TRUE)`
  (remainder correlation 0.98, trend within 0.02 °C); dropping 13 % of rows
  in blocks moves the expected curve by 0.08 °C on the rows kept.
* **Daily cycle**: three-harmonic cosinor on clean half-hour means;
  strength = 1 - Var(remainder) / Var(seasonal + remainder).
* **Thermal model (lights off)**: `dT/dt = (T_room - T)/tau - k * freezer`,
  least squares on 5-minute steps whose two ends are both clean. `k * tau`
  is the furthest the freezer can hold the cabinet below the room.
  Intervals from a bootstrap over whole nights.
* **Night floor**: a night needs 80 % clean readings; nights with freezer
  duty >= 90 % count as flat out; `T_min = max(target, room - dT_sat)`.
* **Day check and regimes**: robust Mahalanobis distance (MCD) on clean
  daily features; least-squares break points on clean daily values.
* **Forecast back-test**: rolling origin, 24 h ahead in half-hour steps:
  yesterday; mean of the last 7 days; STL daily curve + latest trend;
  Fourier regression with ARMA errors (gaps left as gaps, the Kalman filter
  handles them). Removed rows are never scored.
* **Report thresholds**: the daily report's rule is replayed on clean hours
  and days to measure its false-alarm rate, which is what its floors are
  set from.
* **Weekly totals**: an interval whose rate is 3 robust sd from the others
  is left out; rates are duration-weighted.

## Findings on the data available (4-18 Feb, 16 May-10 Jun 2026)

After cleaning, 85 % of February and 73 % of May-June half-hours remain.

* Time constant about 150 min; cooling limit 8.5 °C (Feb) and 9.2 °C
  (May-Jun) below room, consistent with the earlier thermal-twin estimate.
* On flat-out nights the cabinet minimum sits 9.5 °C below the room's night
  average (4 clean nights; 10 nights without cleaning give the same value),
  so a 14 °C night target needs the room below about 23.5 °C.
* 24-hour temperature forecasts: mean absolute error 0.53-0.59 °C in
  May-June and about 1.0 °C in February; the 7-day same-time mean is within
  0.06 °C of the best model.
* Cleaning does not change any conclusion. It cuts the scatter around the
  daily curve (0.58 -> 0.44 °C in May-June), nearly doubles the thermal
  model's fit there (R² 0.32 -> 0.56) and lowers forecast error by 15-25 %.
