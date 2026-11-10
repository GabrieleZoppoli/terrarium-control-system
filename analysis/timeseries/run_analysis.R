#!/usr/bin/env Rscript
# Time-series review of the terrarium data.
#
# Order of work (clean.R has the rules):
#   1. load        every source onto regular 5- and 30-minute grids
#   2. clean       mark missing rows and artefacts, detect anomalies, remove
#                  them, refit, repeat; drop days that are mostly abnormal
#   3. analyse     daily cycle, thermal model, night floor, forecast
#                  back-test, threshold calibration: clean rows only
#   4. report      what was removed, the events found, and the estimates
#
#   Rscript run_analysis.R --snapshots <terrarium-analysis repo> \
#                          --ledger data/ledger_history.csv --out <dir>
#   Rscript run_analysis.R --export <dir from scripts/export-history.sh> --out <dir>
#   add --no-clean to skip step 2 (missing rows are still never filled in);
#   used to show what the cleaning changes.

suppressPackageStartupMessages({
  library(data.table); library(jsonlite); library(forecast)
  library(robustbase); library(strucchange)
})
args <- commandArgs(trailingOnly = TRUE)
arg <- function(flag, default = NULL) { i <- match(flag, args); if (is.na(i)) default else args[i + 1] }
here <- dirname(normalizePath(sub("--file=", "", grep("--file=", commandArgs(), value = TRUE)[1])))
source(file.path(here, "load_data.R")); source(file.path(here, "clean.R"))
out_dir <- arg("--out", "ts_out"); dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)
CLEAN <- !("--no-clean" %in% args)

LIGHTS_ON <- 6.55; LIGHTS_OFF <- 19.95       # local hours (06:33 / 19:57)
SAT_DUTY <- 0.90                             # night freezer duty that counts as "flat out"
NIGHT_TARGET <- 14                           # °C, night setpoint seen in the data
BAD_DAY_SHARE <- 0.15                        # a day with more than this share flagged is dropped whole
r2 <- function(x, d = 2) if (is.null(x)) NULL else round(x, d)
iso <- function(t) format(t, "%Y-%m-%dT%H:%M:%SZ", tz = "UTC")
loc <- function(t, f = "%d %b %H:%M") format(t, f, tz = TZ_LOCAL)
has <- function(g, v) v %in% names(g) && any(!is.na(g[[v]]))

# ── 1. Load ─────────────────────────────────────────────────────────────
add_mist <- function(g, ev, step) {
  if (!nrow(ev)) { g[, mist_n := NA_real_]; return(g) }
  b <- ev[, .N, by = .(time = as.POSIXct(floor(as.numeric(time) / step) * step, origin = "1970-01-01", tz = "UTC"))]
  g[, mist_n := 0]; g[b, mist_n := i.N, on = "time"]; g
}
if (!is.null(arg("--snapshots"))) {
  L <- load_snapshots(arg("--snapshots"))
  j1 <- L[source == "jun1"]; ev <- L[variable == "mist_event"]
  feb5 <- to_grid(L[source == "feb"], 300); feb30 <- to_grid(L[source == "feb"], 1800)
  jun5 <- to_grid(rbind(L[source == "jun5"], j1), 300)
  jun30 <- add_mist(to_grid(rbind(L[source == "jun30"], j1), 1800), ev, 1800)
  rm30 <- L[source == "jun30" & variable == "room_temperature"]
  jun5[, room_temperature := approx(as.numeric(rm30$time) + 900, rm30$value, as.numeric(time), rule = 1)$y]
  for (g in list(feb5, feb30)) g[, light_status := as.numeric(hour >= LIGHTS_ON & hour < LIGHTS_OFF)]
  segs <- list(
    feb = list(label = "4–18 Feb", g5 = feb5, g30 = feb30, mist = NULL),
    jun = list(label = "16 May–10 Jun", g5 = jun5, g30 = jun30, mist = ev$time))
} else {
  L <- load_export_dir(arg("--export"))
  ev <- L[variable == "mist_event"]; L <- L[variable != "mist_event"]
  g5 <- to_grid(L, 300); g30 <- add_mist(to_grid(L, 1800), ev, 1800)
  for (g in list(g5, g30)) if (!"light_status" %in% names(g))
    g[, light_status := as.numeric(hour >= LIGHTS_ON & hour < LIGHTS_OFF)]
  months <- unique(format(g5$date, "%Y-%m"))
  segs <- lapply(setNames(months, months), function(m) list(
    label = format(as.Date(paste0(m, "-01")), "%b %Y"),
    g5 = g5[format(date, "%Y-%m") == m], g30 = g30[format(date, "%Y-%m") == m],
    mist = ev$time[format(ev$time, "%Y-%m", tz = TZ_LOCAL) == m]))
}
R <- list(generated = iso(Sys.time()), cleaned = CLEAN, segments = list(), cleaning = list())

# ── 2. Clean ────────────────────────────────────────────────────────────
runs_to_events <- function(time, flag, z, dev, step, join = 3) {
  i <- which(flag); if (!length(i)) return(NULL)
  grp <- cumsum(c(1, diff(i) > join))
  rbindlist(lapply(split(i, grp), function(k) {
    p <- k[which.max(abs(z[k]))]
    data.table(start = time[k[1]], end = time[k[length(k)]] + step, minutes = (k[length(k)] - k[1] + 1) * step / 60,
               peak_z = z[p], peak_dev = dev[p], peak_time = time[p])
  }))
}
clean_segment <- function(sg) {
  g5 <- copy(sg$g5); g30 <- copy(sg$g30)
  g5 <- g5[time >= min(time[!is.na(local_temperature)])]
  g30 <- g30[time >= min(time[!is.na(local_temperature)])]
  a5 <- mark_artifacts(g5, 300); a30 <- mark_artifacts(g30, 1800)
  art5 <- a5$outage | a5$recovery | a5$flat; art30 <- a30$outage | a30$recovery | a30$flat
  base5 <- !is.na(g5$local_temperature) & !(CLEAN & art5)
  base30 <- !is.na(g30$local_temperature) & !(CLEAN & art30)

  # rows where the controller acted: freezer or lights switched, or a mist fired (±10 min)
  sw <- function(v) if (has(g5, v)) c(FALSE, abs(diff(g5[[v]])) >= 0.2) %in% TRUE else FALSE
  mist5 <- if (length(sg$mist)) as.numeric(g5$time) %in% (floor(as.numeric(sg$mist) / 300) * 300)
           else if (has(g5, "mister_status")) g5$mister_status %in% TRUE | (!is.na(g5$mister_status) & g5$mister_status > 0) else FALSE
  action <- pad_flags(sw("freezer_status") | sw("light_status") | mist5, 2)
  c5T <- clean_channel(g5, "local_temperature", 300, base5, remove = CLEAN, excuse = action)
  c5H <- if (has(g5, "local_humidity")) clean_channel(g5, "local_humidity", 300, base5, floor_level = 0.3, jumps = FALSE, remove = CLEAN)
  # 30-minute detectors cover what the 5-minute grid cannot: the stretch before it starts,
  # and humidity when it only exists at 30 minutes
  early <- g30$time < min(g5$time)
  c30T <- clean_channel(g30, "local_temperature", 1800, base30, min_run = 2, pad = 0, jumps = FALSE, remove = CLEAN)
  c30H <- if (is.null(c5H) && has(g30, "local_humidity")) clean_channel(g30, "local_humidity", 1800, base30, min_run = 2, pad = 0, floor_level = 0.3, jumps = FALSE, remove = CLEAN)
  flag30 <- (early & c30T$flagged) | (if (!is.null(c30H)) c30H$flagged else FALSE)
  # an anomaly in either channel marks the cabinet as abnormal for both
  bucket5 <- floor(as.numeric(g5$time) / 1800) * 1800
  flag5 <- c5T$flagged | (if (!is.null(c5H)) c5H$flagged else FALSE) | bucket5 %in% as.numeric(g30$time)[flag30]

  # days that are mostly abnormal go out whole (share of time flagged, on the finest grid available)
  day <- data.table(date = g30$date, flag = flag30 & base30, outage = a30$outage)[
    , .(outage_h = sum(outage) / 2, flagged_share = mean(flag)), by = date]
  d5 <- data.table(date = g5$date, flag = flag5 & base5)[, .(share5 = mean(flag)), by = date]
  day[d5, on = "date", flagged_share := i.share5]
  # (an outage alone does not condemn the rest of its day: the outage rows and the
  #  recovery hours after the restart are already out)
  day[, bad := CLEAN & flagged_share > BAD_DAY_SHARE]
  bad_dates <- day[bad == TRUE, date]

  g5[, `:=`(artifact = art5, flagged = flag5 & base5, bad_day = date %in% bad_dates)]
  g30[, `:=`(artifact = art30, bad_day = date %in% bad_dates, raw_T = local_temperature)]
  if (CLEAN) {
    g5[, clean := base5 & !flagged & !bad_day]
    # half-hour values are rebuilt from the clean 5-minute rows only (at least 4 of 6)
    hcol <- if (!is.null(c5H)) "local_humidity" else NULL
    agg <- g5[, c(list(nc = sum(clean), T = if (sum(clean) >= 4) mean(local_temperature[clean]) else NA_real_),
                  if (!is.null(hcol)) list(H = if (sum(clean) >= 4) mean(get(hcol)[clean], na.rm = TRUE) else NA_real_)),
              by = .(b = bucket5)]
    k <- match(as.numeric(g30$time), agg$b); cov5 <- !is.na(k)
    g30[cov5, local_temperature := agg$T[k[cov5]]]
    if (!is.null(hcol)) g30[cov5, local_humidity := agg$H[k[cov5]]]
    g30[, clean := ifelse(cov5, !is.na(local_temperature), base30) & !flag30 & !bad_day & !art30]
    # values recorded while the system was down are carried forward, not measured
    for (v in intersect(c("freezer_status", "light_status", "mist_n"), names(g30))) g30[a30$outage, (v) := NA_real_]
    for (v in intersect(c("freezer_status", "light_status"), names(g5))) g5[a5$outage, (v) := NA_real_]
  } else { g5[, clean := !is.na(local_temperature)]; g30[, clean := !is.na(local_temperature)] }

  n <- nrow(g30); miss <- is.na(g30$raw_T); meas <- !miss & !(art30 & CLEAN)
  summary <- list(
    rows = n, missing = sum(miss), artefact = sum(!miss & art30 & CLEAN),
    flagged = sum(meas & !g30$bad_day & !g30$clean), bad_day = sum(meas & g30$bad_day & CLEAN), clean = sum(g30$clean),
    flagged_5min_share = mean((flag5 & base5)[!g5$bad_day]),
    iterations = c(temperature = c5T$iters, humidity = if (!is.null(c5H)) c5H$iters else if (!is.null(c30H)) c30H$iters else NA),
    dropped_days = day[bad == TRUE, .(date = as.character(date), outage_h, flagged_share = r2(flagged_share))])

  ev <- list()
  add_ev <- function(e, variable, detector, unit) if (!is.null(e)) ev[[length(ev) + 1]] <<- e[, `:=`(variable = variable, detector = detector, unit = unit)]
  add_ev(runs_to_events(g5$time, c5T$level, c5T$z, c5T$fit$remainder, 300), "temperature", "level", "°C")
  jmp <- runs_to_events(g5$time, c5T$jump, c5T$jz, c5T$jdev, 300, join = 1)
  if (!is.null(jmp)) {
    i0 <- match(jmp$start, g5$time)
    jmp[, night := g5$light_status[i0] < 0.5]
    jmp[, control_action := action[i0] & abs(peak_dev) < 1]       # normal operation: kept in the data
    jmp[, near_mist := if (length(sg$mist)) vapply(as.numeric(start), function(t)
      any(as.numeric(sg$mist) > t - 600 & as.numeric(sg$mist) < t + 600), NA) else NA]
    jmp[, door_like := night & peak_dev >= 1 & !(near_mist %in% TRUE)]
    add_ev(jmp, "temperature", "jump", "°C")
  }
  if (!is.null(c5H)) add_ev(runs_to_events(g5$time, c5H$level, c5H$z, c5H$fit$remainder, 300), "humidity", "level", "%")
  else if (!is.null(c30H)) add_ev(runs_to_events(g30$time, c30H$level, c30H$z, c30H$fit$remainder, 1800, join = 1), "humidity", "level", "%")
  early <- g30$time < min(g5$time)                       # temperature only exists at 30 min here
  if (any(early)) add_ev(runs_to_events(g30$time, c30T$level & early, c30T$z, c30T$fit$remainder, 1800, join = 1), "temperature", "level", "°C")
  list(g5 = g5, g30 = g30, c5T = c5T, c5H = c5H, c30H = c30H, summary = summary, events = rbindlist(ev, fill = TRUE))
}

# ── 3. Analyses (clean rows only) ───────────────────────────────────────
cosinor <- function(g, v, K = 3) {
  d <- g[clean == TRUE & !is.na(get(v))]; w <- 2 * pi * d$hour / 24
  X <- do.call(cbind, lapply(1:K, function(k) cbind(cos(k * w), sin(k * w))))
  m <- lm(d[[v]] ~ X); b <- coef(m)
  hh <- seq(0, 23.75, 0.25); wh <- 2 * pi * hh / 24
  fit <- b[1] + do.call(cbind, lapply(1:K, function(k) cbind(cos(k * wh), sin(k * wh)))) %*% b[-1]
  list(mesor = unname(b[1]), amp24 = sqrt(b[2]^2 + b[3]^2), swing = diff(range(fit)),
       peak_h = hh[which.max(fit)], trough_h = hh[which.min(fit)], r2 = summary(m)$r.squared, n = nrow(d))
}
profile <- function(g, v) g[clean == TRUE & !is.na(get(v)), .(value = mean(get(v))), by = .(hour = floor(hour * 2) / 2)][order(hour)]
strength <- function(cc) {
  k <- cc$ok; rem <- cc$fit$remainder[k]
  list(F_seasonal = max(0, 1 - var(rem) / var(cc$fit$seasonal[k] + rem)),
       F_trend = max(0, 1 - var(rem) / var(cc$fit$trend[k] + rem)), rem_sd = sd(rem), rem_mad = mad(rem))
}
nightly <- function(g, step) {
  g <- copy(g); if (!has(g, "room_temperature")) g[, room_temperature := NA_real_]
  g[, night := as.Date(ifelse(hour < 12, date - 1, date), origin = "1970-01-01")]
  g[hour >= LIGHTS_OFF | hour < LIGHTS_ON, {
    if (sum(clean) < 0.8 * (10.6 * 3600 / step)) NULL else {
      tt <- ifelse(clean, local_temperature, NA_real_); i <- which.min(tt)
      .(T_min = tt[i], h_min = hour[i], frz_duty = mean(freezer_status, na.rm = TRUE),
        room = mean(room_temperature, na.rm = TRUE), clean_share = mean(clean))
    }
  }, by = night]
}
thermal_night <- function(g5, B = 500) {
  # dT/dt = (T_room - T)/tau - k_F * freezer, lights off; both ends of each step must be clean
  d <- copy(g5)
  d[, dT := (shift(local_temperature, -1) - local_temperature) * 12]
  d[, pair_ok := clean & shift(clean, -1, fill = FALSE)]
  d[, gap := room_temperature - local_temperature]
  d[, night := as.Date(ifelse(hour < 12, date - 1, date), origin = "1970-01-01")]
  d <- d[pair_ok & light_status < 0.5 & !is.na(dT) & !is.na(gap) & !is.na(freezer_status)]
  if (nrow(d) < 200) return(NULL)
  est <- function(x) { co <- coef(lm(dT ~ 0 + gap + freezer_status, x))
    c(tau_min = 60 / co[[1]], kF = -co[[2]], dTmax = -co[[2]] / co[[1]]) }
  ns <- unique(d$night); set.seed(1)
  bs <- replicate(B, est(rbindlist(lapply(sample(ns, replace = TRUE), function(n) d[night == n]))))
  ci <- apply(bs, 1, quantile, c(.025, .975)); e <- est(d)
  list(n = nrow(d), nights = length(ns), tau_min = e[["tau_min"]], tau_ci = ci[, "tau_min"], kF = e[["kF"]],
       dTmax = e[["dTmax"]], dTmax_ci = ci[, "dTmax"], r2 = summary(lm(dT ~ 0 + gap + freezer_status, d))$r.squared)
}
daily_features <- function(g, step) {
  per_day <- 86400 / step
  g[, {
    k <- clean; hk <- k & if (has(.SD, "local_humidity")) !is.na(local_humidity) else FALSE
    .(coverage = sum(k) / per_day,
      T_min = if (any(k)) min(local_temperature[k]) else NA_real_, T_max = if (any(k)) max(local_temperature[k]) else NA_real_,
      T_mean = if (any(k)) mean(local_temperature[k]) else NA_real_,
      RH_mean = if (any(hk)) mean(local_humidity[hk]) else NA_real_, RH_min = if (any(hk)) min(local_humidity[hk]) else NA_real_,
      fog_h = if (any(hk)) sum(local_humidity[hk] >= 95) * step / 3600 else NA_real_,
      duty = if (has(.SD, "freezer_status")) mean(freezer_status, na.rm = TRUE) else NA_real_,
      room = if (has(.SD, "room_temperature")) mean(room_temperature, na.rm = TRUE) else NA_real_,
      mist_n = if (has(.SD, "mist_n")) sum(mist_n, na.rm = TRUE) else NA_real_)
  }, by = date]
}

# 24 h ahead, rolling origin, half-hour steps. Removed rows are NA: never filled, never scored.
backtest <- function(y, time, freq = 48, min_days = 6, h = 48, max_days = 12) {
  n <- length(y); origins <- seq(min_days * freq, n - h, by = freq)
  res <- list(); example <- NULL
  for (o in origins) {
    tr <- y[max(1, o - max_days * freq + 1):o]; te <- y[(o + 1):(o + h)]; nt <- length(tr)
    if (mean(!is.na(te)) < 0.75 || mean(!is.na(tail(tr, 7 * freq))) < 0.6) next
    trs <- ts(tr, frequency = freq)
    last7 <- matrix(tail(tr, min(7, nt %/% freq) * freq), nrow = freq)
    f_naive <- as.numeric(tail(tr, freq))
    f_mean7 <- rowMeans(last7, na.rm = TRUE); n7 <- rowSums(!is.na(last7))
    f_mean7[n7 < 3] <- NA
    sd7 <- apply(last7, 1, sd, na.rm = TRUE) * sqrt(1 + 1 / pmax(n7, 1))
    m <- tryCatch(auto.arima(trs, xreg = fourier(trs, K = 6), seasonal = FALSE, d = 0, max.p = 3, max.q = 3),
                  error = function(e) NULL)
    fd <- if (!is.null(m)) forecast(m, xreg = fourier(trs, K = 6, h = h), level = c(80, 95)) else NULL
    slot <- (seq_len(nt) - 1) %% freq; cyc <- (seq_len(nt) - 1) %/% freq
    st <- stl_na(tr, slot, cyc, !is.na(tr), freq)
    f_stl <- tail(st$trend, 1) + st$seasonal[(nt - freq + 1):nt]
    row <- function(model, f, lo80 = NA, hi80 = NA, lo95 = NA, hi95 = NA)
      data.table(origin = o, step = 1:h, model = model, err = as.numeric(f) - te,
                 in80 = as.logical(te >= as.numeric(lo80) & te <= as.numeric(hi80)),
                 in95 = as.logical(te >= as.numeric(lo95) & te <= as.numeric(hi95)))
    res[[length(res) + 1]] <- rbind(
      row("Yesterday, same time", f_naive),
      row("Mean of last 7 days", f_mean7, f_mean7 - 1.28 * sd7, f_mean7 + 1.28 * sd7, f_mean7 - 1.96 * sd7, f_mean7 + 1.96 * sd7),
      row("Daily curve + latest trend", f_stl),
      if (!is.null(fd)) row("Harmonics + ARMA", as.numeric(fd$mean), fd$lower[, 1], fd$upper[, 1], fd$lower[, 2], fd$upper[, 2]))
    if (!is.null(fd)) example <- list(t0 = iso(time[o - freq + 1]), history = as.numeric(tail(tr, freq)), actual = te,
                                      mean = as.numeric(fd$mean), lo = as.numeric(fd$lower[, 2]), hi = as.numeric(fd$upper[, 2]))
  }
  if (!length(res)) return(NULL)
  res <- rbindlist(res)[!is.na(err)]
  list(n_origins = uniqueN(res$origin), example = example,
       summary = res[, .(mae = mean(abs(err)), rmse = sqrt(mean(err^2)), mae_0_6h = mean(abs(err[step <= 12])),
                         mae_6_24h = mean(abs(err[step > 12])), cover80 = mean(in80, na.rm = TRUE),
                         cover95 = mean(in95, na.rm = TRUE), n = .N), by = model])
}
# How often would the daily report's rule fire on ordinary (clean) data?
rule_rate <- function(t, x, lag, floor_sd, min_delta, z_warn = 3) {
  by_t <- setNames(x, t)
  out <- vapply(seq_along(x), function(i) {
    ref <- by_t[as.character(t[i] - (1:7) * lag)]; ref <- ref[!is.na(ref)]
    if (is.na(x[i]) || length(ref) < 3) return(NA)
    m <- median(ref); abs(x[i] - m) / max(mad(ref), floor_sd) >= z_warn && abs(x[i] - m) >= min_delta
  }, NA)
  c(tested = sum(!is.na(out)), flagged = sum(out, na.rm = TRUE))
}

# ── Run ─────────────────────────────────────────────────────────────────
all_nights <- list(); all_days <- list(); all_events <- list(); all_hours <- list()
for (s in names(segs)) {
  message("segment ", s)
  cs <- clean_segment(segs[[s]]); g5 <- cs$g5; g30 <- cs$g30
  out <- list(label = segs[[s]]$label)
  R$cleaning[[s]] <- cs$summary
  if (nrow(cs$events)) all_events[[s]] <- cs$events[, segment := s]

  out$cosinor <- list(temperature = cosinor(g30, "local_temperature"),
                      humidity = if (has(g30, "local_humidity")) cosinor(g30, "local_humidity"))
  out$profile <- list(temperature = profile(g30, "local_temperature"),
                      humidity = if (has(g30, "local_humidity")) profile(g30, "local_humidity"))
  out$stl <- list(temperature = strength(cs$c5T),
                  humidity = if (!is.null(cs$c5H)) strength(cs$c5H) else if (!is.null(cs$c30H)) strength(cs$c30H))

  ix <- seq(1, nrow(g5), by = 3)                    # chart series, every 15 min
  status <- ifelse(is.na(g5$local_temperature), "missing", ifelse(g5$clean, "ok",
            ifelse(g5$artifact, "artefact", ifelse(g5$flagged, "anomaly", "bad_day"))))
  out$series <- data.table(t = iso(g5$time[ix]), value = r2(g5$local_temperature[ix]),
                           expected = r2((cs$c5T$fit$trend + cs$c5T$fit$seasonal)[ix]), band = r2(cs$c5T$band[ix]),
                           status = status[ix])
  lev <- cs$events[variable == "temperature" & detector == "level" & start >= min(g5$time)]
  out$level_events <- if (nrow(lev)) lev[, .(start = iso(start), peak_time = iso(peak_time), peak_dev = r2(peak_dev),
                                             minutes = round(minutes), value = r2(g5$local_temperature[match(peak_time, g5$time)]))]
  dl <- cs$events[door_like %in% TRUE]
  out$door_like <- if (nrow(dl)) dl[, .(peak_time = iso(peak_time), rise = r2(peak_dev),
                                        value = r2(g5$local_temperature[pmin(match(peak_time, g5$time) + 1, nrow(g5))]))]

  if (length(segs[[s]]$mist)) {                     # response to a mist, on measured rows
    hv <- if (has(g5, "local_humidity")) "local_humidity" else if (has(g5, "difference_humidity")) "difference_humidity"
    sgn <- if (identical(hv, "difference_humidity")) -1 else 1
    resp <- rbindlist(lapply(as.numeric(segs[[s]]$mist), function(m) {
      i <- match(floor(m / 300) * 300, as.numeric(g5$time)); if (is.na(i) || i < 2 || i + 6 > nrow(g5)) return(NULL)
      if (any(g5$artifact[(i - 1):(i + 4)])) return(NULL)
      data.table(night = g5$light_status[i] < 0.5, dT = g5$local_temperature[i + 4] - g5$local_temperature[i - 1],
                 dRH = if (is.null(hv)) NA_real_ else sgn * (g5[[hv]][i + 4] - g5[[hv]][i - 1]))
    }))
    out$mist_response <- resp[!is.na(dT), .(n = .N, dT_20min = mean(dT), dRH_20min = mean(dRH, na.rm = TRUE)), by = night]
  }

  ni <- nightly(g5, 300); n30 <- nightly(g30, 1800); n30 <- n30[!night %in% ni$night]
  nn <- rbind(ni, n30, fill = TRUE)[order(night)]; nn[, segment := s]; all_nights[[s]] <- nn
  if (has(g5, "room_temperature")) out$thermal <- thermal_night(g5)
  dd <- daily_features(g30, 1800); dd[, segment := s]; all_days[[s]] <- dd

  out$backtest <- backtest(ifelse(g30$clean, g30$local_temperature, NA_real_), g30$time)
  hrs <- g30[, .(temp = if (sum(clean) == 2) mean(local_temperature) else NA_real_,
                 humi = if (sum(clean) == 2 && has(.SD, "local_humidity")) mean(local_humidity) else NA_real_),
             by = .(t = as.numeric(time) %/% 3600 * 3600)]
  all_hours[[s]] <- hrs
  R$segments[[s]] <- out
}
nights <- rbindlist(all_nights, fill = TRUE); days <- rbindlist(all_days, fill = TRUE)
events <- rbindlist(all_events, fill = TRUE); hours <- rbindlist(all_hours)

# ── Night floor vs room temperature ─────────────────────────────────────
nights[, saturated := frz_duty >= SAT_DUTY]
nr <- nights[!is.na(room)]; sat <- nr[saturated == TRUE]; sat[, dT := room - T_min]
ref <- sat[segment == tail(names(segs), 1)]; if (nrow(ref) < 4) ref <- sat      # most recent configuration
dT_sat <- mean(ref$dT); sd_sat <- sd(ref$dT); n_sat <- nrow(ref)
tq <- qt(0.95, n_sat - 1) * sd_sat * sqrt(1 + 1 / n_sat); room_grid <- seq(20, 30, 1)
warm <- nr[room >= NIGHT_TARGET + dT_sat]; cool <- nr[room < NIGHT_TARGET + dT_sat]
R$night_floor <- list(
  nights = nights[, .(night = as.character(night), segment, T_min = r2(T_min), room = r2(room), duty = r2(frz_duty), saturated)],
  n_nights = nrow(nights), n_with_room = nrow(nr), n_saturated_with_room = nrow(sat),
  by_segment = sat[, .(n = .N, dT = mean(dT), sd = sd(dT)), by = segment],
  dT_sat = dT_sat, dT_sd = sd_sat, n_ref = n_sat, pi90 = tq, target = NIGHT_TARGET, break_even_room = NIGHT_TARGET + dT_sat,
  warm = c(nights = nrow(warm), saturated = sum(warm$saturated)), cool = c(nights = nrow(cool), saturated = sum(cool$saturated)),
  predict = data.table(room = room_grid, floor = pmax(NIGHT_TARGET, room_grid - dT_sat),
                       lo = pmax(NIGHT_TARGET, room_grid - dT_sat - tq), hi = pmax(NIGHT_TARGET, room_grid - dT_sat + tq)),
  sat_share = nights[, .(nights = .N, saturated = sum(saturated)), by = segment],
  last_sat_streak = { r <- rle(nights[order(night)]$saturated); if (tail(r$values, 1)) tail(r$lengths, 1) else 0 })

# ── Days: what still looks unusual, and regime shifts ───────────────────
R$days <- days[, .(date = as.character(date), segment, coverage = r2(coverage), T_min = r2(T_min, 1), T_max = r2(T_max, 1),
                   T_mean = r2(T_mean), RH_mean = r2(RH_mean, 1), fog_h = r2(fog_h, 1), duty = r2(duty, 3), room = r2(room, 1), mist_n)]
feat <- c("T_min", "T_max", "RH_mean", "RH_min", "duty")
ok <- days[coverage >= 0.8 & complete.cases(days[, feat, with = FALSE])]
floors <- c(T_min = 0.4, T_max = 0.5, RH_mean = 1.5, RH_min = 2.5, duty = 0.03)
Z <- ok[, Map(function(x, f) (x - median(x)) / max(mad(x), f), .SD, floors[feat]), by = segment, .SDcols = feat]
Zm <- as.matrix(Z[, feat, with = FALSE]); mcd <- covMcd(Zm, alpha = 0.75)
ok[, d2 := mahalanobis(Zm, mcd$center, mcd$cov)]; cut <- qchisq(0.975, length(feat))
zc <- sweep(Zm, 2, mcd$center) / sqrt(diag(mcd$cov))
ok[, driver := apply(zc, 1, function(r) { k <- order(-abs(r))[1:2]
  paste(sprintf("%s %s", feat[k], ifelse(r[k] > 0, "high", "low")), collapse = ", ") })]
R$day_anomalies <- list(n_days = nrow(ok), cutoff = cut,
  flagged = ok[d2 > cut][order(-d2), .(date = as.character(date), segment, d2 = r2(d2, 1), driver)])
breaks_of <- function(d, v, h = 4) {
  d <- d[coverage >= 0.8 & !is.na(get(v))]; if (nrow(d) < 2 * h + 2) return(NULL)
  bp <- breakpoints(d[[v]] ~ 1, h = h); if (all(is.na(bp$breakpoints))) return(NULL)
  cuts <- c(0, bp$breakpoints, nrow(d))
  lapply(seq_along(bp$breakpoints), function(i) list(
    variable = v, date = as.character(d$date[bp$breakpoints[i] + 1]),
    before = mean(d[[v]][(cuts[i] + 1):cuts[i + 1]]), after = mean(d[[v]][(cuts[i + 1] + 1):cuts[i + 2]])))
}
R$regime_changes <- unlist(lapply(names(segs), function(s) {
  d <- days[segment == s]
  lapply(c(breaks_of(d, "duty"), breaks_of(d, "T_max"), breaks_of(d, "RH_mean")), function(b) c(b, segment = s))
}), recursive = FALSE)

# ── Threshold calibration for the daily report, on clean data ───────────
dk <- days[coverage >= 0.8][order(segment, date)]; dk[, t := as.numeric(date) * 86400]
grid <- function(tt, x, lag, floors, deltas) {
  g <- CJ(floor_sd = floors, min_delta = deltas)
  rr <- t(mapply(function(f, d) rule_rate(tt, x, lag, f, d), g$floor_sd, g$min_delta))
  g[, `:=`(tested = rr[, "tested"], flagged = rr[, "flagged"])]; g[, rate := flagged / tested]; g[]
}
R$report_rule <- list(
  hour_temperature = grid(hours$t, hours$temp, 86400, c(0.3, 0.6, 0.9, 1.0, 1.2), c(0.5, 1, 1.5)),
  hour_humidity = grid(hours$t, hours$humi, 86400, c(2, 3, 4, 5), c(3, 4, 6)),
  day_temperature = grid(dk$t, dk$T_mean, 86400, c(0.3, 0.5, 0.7, 0.9), c(0.5, 1)),
  day_humidity = grid(dk$t, dk$RH_mean, 86400, c(2, 3, 4), c(3, 4)),
  day_freezer = grid(dk$t, dk$duty * 100, 86400, c(4, 6, 8), c(8)))

# ── Events ──────────────────────────────────────────────────────────────
if (nrow(events)) {
  for (v in c("door_like", "near_mist", "night", "control_action")) if (!v %in% names(events)) events[, (v) := NA]
  events[, score := abs(peak_z) * sqrt(pmax(minutes, 5) / 5)]; setorder(events, -score)
  R$events <- list(counts = events[, .N, by = .(segment, variable, detector)],
    jumps = events[detector == "jump", .(n = .N, control_action = sum(control_action %in% TRUE), removed = sum(!(control_action %in% TRUE)),
                                         near_mist = sum(near_mist %in% TRUE), door_like = sum(door_like %in% TRUE)), by = segment],
    door_like = events[door_like %in% TRUE][order(start), .(segment, start_local = loc(start), minutes = round(minutes), rise = r2(peak_dev))],
    top = events[detector == "level", head(.SD, 7), by = .(segment, variable)][
      , .(segment, variable, start_local = loc(start), minutes = round(minutes), peak_dev = r2(peak_dev), peak_z = r2(peak_z, 1), unit)])
  fwrite(events[, .(segment, variable, detector, start = iso(start), end = iso(end), minutes, peak_dev, peak_z, near_mist, door_like)],
         file.path(out_dir, "anomaly_events.csv"))
}

# ── Weekly running totals ───────────────────────────────────────────────
if (!is.null(arg("--ledger"))) {
  led <- fread(arg("--ledger")); led[, t := as.POSIXct(as_of, format = "%Y-%m-%dT%H:%M:%SZ", tz = "UTC")]
  led <- led[c(TRUE, diff(as.numeric(t)) > 1.5 * 86400)]          # drop same-day duplicates
  iv <- data.table(from = head(led$t, -1), to = led$t[-1]); iv[, days := as.numeric(to - from, units = "days")]
  for (v in c("kwh", "mist_cycles", "fog_hours")) set(iv, j = paste0(v, "_per_day"), value = diff(led[[v]]) / iv$days)
  # an interval far from the others is an anomaly (an experiment week, a fault): leave it out of the rates
  rz <- (iv$kwh_per_day - median(iv$kwh_per_day)) / mad(iv$kwh_per_day)
  iv[, anomaly := CLEAN & abs(rz) >= 3]
  use <- iv[anomaly == FALSE]
  bp <- breakpoints(use$kwh_per_day ~ 1, h = 3); b <- bp$breakpoints[1]
  pre <- use[1:b]; post <- use[(b + 1):nrow(use)]; wt <- t.test(post$kwh_per_day, pre$kwh_per_day)
  wmean <- function(d) sum(d$kwh_per_day * d$days) / sum(d$days)
  today <- as.POSIXct(Sys.Date(), tz = "UTC"); last <- tail(led, 1); oct <- as.POSIXct("2026-10-01", tz = "UTC")
  R$ledger <- list(
    intervals = iv[, .(from = iso(from), to = iso(to), days = r2(days, 1), kwh_per_day = r2(kwh_per_day),
                       mist_per_day = r2(mist_cycles_per_day, 1), fog_h_per_day = r2(fog_hours_per_day), anomaly)],
    kwh_break = list(date = iso(post$from[1]), before = wmean(pre), after = wmean(post),
                     step = wmean(post) - wmean(pre), ci = as.numeric(wt$conf.int), p = wt$p.value),
    last = list(as_of = iso(last$t), kwh = last$kwh),
    projection = list(as_of = as.character(Sys.Date()),
      kwh_if_summer_rate_held = last$kwh + as.numeric(today - last$t, units = "days") * wmean(post),
      kwh_if_spring_rate_from_october = last$kwh + as.numeric(oct - last$t, units = "days") * wmean(post) +
        as.numeric(today - oct, units = "days") * wmean(pre)))
}

write_json(R, file.path(out_dir, "results.json"), auto_unbox = TRUE, digits = 4, na = "null", null = "null")
fwrite(nights, file.path(out_dir, "nights.csv")); fwrite(days, file.path(out_dir, "days.csv"))
message("wrote ", file.path(out_dir, "results.json"))
