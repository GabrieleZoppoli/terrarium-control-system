#!/usr/bin/env Rscript
# Time-series review of the terrarium data: structure of the daily cycle,
# thermal inference, anomaly detection and forecast back-testing.
#
#   Rscript run_analysis.R --snapshots <terrarium-analysis repo> \
#                          --ledger <ledger_history.csv> --out <dir>
#   Rscript run_analysis.R --export <dir from scripts/export-history.sh> --out <dir>
#
# Writes <out>/results.json (every number and chart series the report uses)
# and <out>/*.csv tables.

suppressPackageStartupMessages({
  library(data.table); library(jsonlite); library(forecast)
  library(robustbase); library(strucchange)
})
args <- commandArgs(trailingOnly = TRUE)
arg <- function(flag, default = NULL) {
  i <- match(flag, args); if (is.na(i)) default else args[i + 1]
}
here <- dirname(normalizePath(sub("--file=", "", grep("--file=", commandArgs(), value = TRUE)[1])))
source(file.path(here, "load_data.R"))
out_dir <- arg("--out", "ts_out"); dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

LIGHTS_ON <- 6.55; LIGHTS_OFF <- 19.95       # local hours (06:33 / 19:57)
SAT_DUTY <- 0.90                             # night freezer duty that counts as "flat out"
NIGHT_TARGET <- 14                           # °C, night setpoint seen in the data
r2 <- function(x, d = 2) if (is.null(x)) NULL else round(x, d)
iso <- function(t) format(t, "%Y-%m-%dT%H:%M:%SZ", tz = "UTC")
loc <- function(t, f = "%d %b %H:%M") format(t, f, tz = TZ_LOCAL)

# ── 1. Data ─────────────────────────────────────────────────────────────
add_mist <- function(g, ev, step) {
  if (!nrow(ev)) { g[, mist_n := NA_real_]; return(g) }
  b <- ev[, .N, by = .(time = as.POSIXct(floor(as.numeric(time) / step) * step,
                                         origin = "1970-01-01", tz = "UTC"))]
  g[, mist_n := 0]; g[b, mist_n := i.N, on = "time"]; g
}

if (!is.null(arg("--snapshots"))) {
  L <- load_snapshots(arg("--snapshots"))
  j1 <- L[source == "jun1"]; ev <- L[variable == "mist_event"]
  feb5  <- to_grid(L[source == "feb"], 300)
  feb30 <- to_grid(L[source == "feb"], 1800)
  jun5  <- to_grid(rbind(L[source == "jun5"], j1), 300)
  jun30 <- add_mist(to_grid(rbind(L[source == "jun30"], j1), 1800), ev, 1800)
  rm30 <- L[source == "jun30" & variable == "room_temperature"]
  jun5[, room_temperature := approx(as.numeric(rm30$time) + 900, rm30$value,
                                    as.numeric(time), rule = 1)$y]
  for (g in list(feb5, feb30)) g[, light_status := as.numeric(hour >= LIGHTS_ON & hour < LIGHTS_OFF)]
  segs <- list(
    feb = list(label = "4–18 Feb", season = "winter", g5 = feb5, g30 = feb30, mist = NULL),
    jun = list(label = "16 May–10 Jun", season = "early summer", g5 = jun5, g30 = jun30, mist = ev$time))
} else {
  L <- load_export_dir(arg("--export"))
  ev <- L[variable == "mist_event"]; L <- L[variable != "mist_event"]
  g5 <- to_grid(L, 300); g30 <- add_mist(to_grid(L, 1800), ev, 1800)
  for (g in list(g5, g30)) if (!"light_status" %in% names(g))
    g[, light_status := as.numeric(hour >= LIGHTS_ON & hour < LIGHTS_OFF)]
  months <- unique(format(g5$date, "%Y-%m"))
  segs <- lapply(setNames(months, months), function(m) list(
    label = format(as.Date(paste0(m, "-01")), "%b %Y"), season = m,
    g5 = g5[format(date, "%Y-%m") == m], g30 = g30[format(date, "%Y-%m") == m],
    mist = ev$time[format(ev$time, "%Y-%m", tz = TZ_LOCAL) == m]))
}
has <- function(g, v) v %in% names(g) && any(!is.na(g[[v]]))
R <- list(generated = iso(Sys.time()), segments = list())

coverage <- rbindlist(lapply(names(segs), function(s) {
  g <- segs[[s]]$g30
  data.table(segment = s, label = segs[[s]]$label, from = iso(min(g$time)), to = iso(max(g$time)),
             days = round(as.numeric(diff(range(g$time)), units = "days"), 1),
             temp_complete = round(mean(!is.na(g$local_temperature)), 3))
}))
R$coverage <- coverage

# ── 2. Structure of the daily cycle ─────────────────────────────────────
cosinor <- function(g, v, K = 3) {
  d <- g[!is.na(get(v))]; w <- 2 * pi * d$hour / 24
  X <- do.call(cbind, lapply(1:K, function(k) cbind(cos(k * w), sin(k * w))))
  m <- lm(d[[v]] ~ X); b <- coef(m)
  hh <- seq(0, 23.75, 0.25); wh <- 2 * pi * hh / 24
  fit <- b[1] + do.call(cbind, lapply(1:K, function(k) cbind(cos(k * wh), sin(k * wh)))) %*% b[-1]
  list(mesor = unname(b[1]), amp24 = sqrt(b[2]^2 + b[3]^2),
       acrophase_h = (atan2(b[3], b[2]) * 24 / (2 * pi)) %% 24,
       swing = diff(range(fit)), peak_h = hh[which.max(fit)], trough_h = hh[which.min(fit)],
       r2 = summary(m)$r.squared)
}
seasonal_fill <- function(y, slot) {           # fill gaps with the time-of-day median
  med <- ave(y, slot, FUN = function(x) median(x, na.rm = TRUE)); ifelse(is.na(y), med, y)
}
stl_fit <- function(g, v, period) {
  y <- g[[v]]; mask <- is.na(y); slot <- round(g$hour * period / 24)
  f <- stl(ts(seasonal_fill(y, slot), frequency = period), s.window = 13, robust = TRUE)$time.series
  rem <- as.numeric(f[, "remainder"]); rem[mask] <- NA
  list(trend = as.numeric(f[, "trend"]), seasonal = as.numeric(f[, "seasonal"]), remainder = rem,
       F_seasonal = max(0, 1 - var(rem, na.rm = TRUE) / var(f[, "seasonal"] + f[, "remainder"])),
       F_trend = max(0, 1 - var(rem, na.rm = TRUE) / var(f[, "trend"] + f[, "remainder"])),
       rem_sd = mad(rem, na.rm = TRUE))
}
profile <- function(g, v) g[!is.na(get(v)), .(value = mean(get(v))), by = .(hour = floor(hour * 2) / 2)][order(hour)]

# ── 3. Nights and the thermal model ─────────────────────────────────────
nightly <- function(g, step) {
  g <- copy(g); if (!has(g, "room_temperature")) g[, room_temperature := NA_real_]
  g[, night := as.Date(ifelse(hour < 12, date - 1, date), origin = "1970-01-01")]
  g[hour >= LIGHTS_OFF | hour < LIGHTS_ON, {
    ok <- !is.na(local_temperature)
    if (sum(ok) < 0.8 * (10.6 * 3600 / step)) NULL else {
      i <- which.min(local_temperature)
      .(T_start = local_temperature[which(ok)[1]], T_min = local_temperature[i], h_min = hour[i],
        frz_duty = mean(freezer_status, na.rm = TRUE), room = mean(room_temperature, na.rm = TRUE))
    }
  }, by = night]
}
thermal_night <- function(g5, B = 500) {
  # dT/dt = (T_room - T)/tau - k_F * freezer, lights off. Bootstrap resamples whole nights.
  d <- copy(g5)
  d[, dT := (shift(local_temperature, -1) - local_temperature) * 12]
  d[, gap := room_temperature - local_temperature]
  d[, night := as.Date(ifelse(hour < 12, date - 1, date), origin = "1970-01-01")]
  d <- d[light_status < 0.5 & !is.na(dT) & !is.na(gap) & !is.na(freezer_status)]
  if (nrow(d) < 200) return(NULL)
  est <- function(x) { co <- coef(lm(dT ~ 0 + gap + freezer_status, x))
    c(tau_min = 60 / co[[1]], kF = -co[[2]], dTmax = -co[[2]] / co[[1]]) }
  ns <- unique(d$night); set.seed(1)
  bs <- replicate(B, est(rbindlist(lapply(sample(ns, replace = TRUE), function(n) d[night == n]))))
  ci <- apply(bs, 1, quantile, c(.025, .975))
  e <- est(d)
  list(n = nrow(d), nights = length(ns), tau_min = e[["tau_min"]], tau_ci = ci[, "tau_min"],
       kF = e[["kF"]], dTmax = e[["dTmax"]], dTmax_ci = ci[, "dTmax"],
       r2 = summary(lm(dT ~ 0 + gap + freezer_status, d))$r.squared)
}

# ── 4. Anomaly detectors ────────────────────────────────────────────────
runs_to_events <- function(time, flag, z, dev, step, join = 3) {
  i <- which(flag); if (!length(i)) return(NULL)
  grp <- cumsum(c(1, diff(i) > join))
  rbindlist(lapply(split(i, grp), function(k) {
    p <- k[which.max(abs(z[k]))]
    data.table(start = time[k[1]], end = time[k[length(k)]] + step,
               minutes = (k[length(k)] - k[1] + 1) * step / 60,
               peak_z = z[p], peak_dev = dev[p], peak_time = time[p])
  }))
}
# (a) Level detector: robust STL remainder, scaled by a MAD per hour of the day
#     (switching hours are naturally noisier and get a wider band).
detect_level <- function(g, v, period, step, k = 4.5, floor_sd = 0.05) {
  f <- stl_fit(g, v, period); blk <- floor(g$hour)
  s <- pmax(ave(f$remainder, blk, FUN = function(x) mad(x, na.rm = TRUE)), floor_sd)
  z <- f$remainder / s
  ev <- runs_to_events(g$time, !is.na(z) & abs(z) >= k, z, f$remainder, step)
  if (!is.null(ev)) ev <- ev[minutes >= 3 * step / 60 | abs(peak_z) >= 1.5 * k]
  list(fit = f, z = z, band = k * s, events = ev)
}
# (b) Jump detector: step-to-step change, minus the usual change at that time of day.
detect_jump <- function(g, v, step, k = 7, floor_sd = 0.02) {
  d <- c(NA, diff(g[[v]])); slot <- floor(g$hour * 2)
  dd <- d - ave(d, slot, FUN = function(x) median(x, na.rm = TRUE))
  s <- pmax(ave(dd, slot, FUN = function(x) mad(x, na.rm = TRUE)), floor_sd)
  z <- dd / s
  runs_to_events(g$time, !is.na(z) & abs(z) >= k, z, dd, step, join = 1)
}
gaps <- function(g, v, step, min_h = 1) {
  na <- is.na(g[[v]]); r <- rle(na); e <- cumsum(r$lengths); s <- e - r$lengths + 1
  k <- which(r$values & r$lengths * step / 3600 >= min_h & s > 1)
  if (!length(k)) return(NULL)
  data.table(variable = v, from = g$time[s[k]], to = g$time[e[k]] + step, hours = r$lengths[k] * step / 3600)
}
daily_features <- function(g, step) {
  per_day <- 86400 / step
  g[, .(coverage = sum(!is.na(local_temperature)) / per_day,
        T_min = min(local_temperature, na.rm = TRUE), T_max = max(local_temperature, na.rm = TRUE),
        T_mean = mean(local_temperature, na.rm = TRUE),
        RH_mean = if (has(.SD, "local_humidity")) mean(local_humidity, na.rm = TRUE) else NA_real_,
        RH_min = if (has(.SD, "local_humidity")) min(local_humidity, na.rm = TRUE) else NA_real_,
        fog_h = if (has(.SD, "local_humidity")) sum(local_humidity >= 95, na.rm = TRUE) * step / 3600 else NA_real_,
        duty = if (has(.SD, "freezer_status")) mean(freezer_status, na.rm = TRUE) else NA_real_,
        room = if (has(.SD, "room_temperature")) mean(room_temperature, na.rm = TRUE) else NA_real_,
        mist_n = if (has(.SD, "mist_n")) sum(mist_n, na.rm = TRUE) else NA_real_), by = date]
}

# ── 5. Forecast back-test (24 h ahead, rolling origin, 30-min steps) ────
backtest <- function(y, freq = 48, min_days = 6, h = 48, max_days = 12) {
  n <- length(y); origins <- seq(min_days * freq, n - h, by = freq)
  res <- list(); example <- NULL
  for (o in origins) {
    tr <- y[max(1, o - max_days * freq + 1):o]; te <- y[(o + 1):(o + h)]
    if (anyNA(te) || mean(is.na(tr)) > 0.05) next
    slot <- (seq_along(tr) - 1) %% freq
    tr <- ts(seasonal_fill(tr, slot), frequency = freq); nt <- length(tr)
    last7 <- matrix(tail(tr, min(7, nt %/% freq) * freq), nrow = freq)
    f_naive <- as.numeric(tail(tr, freq)); f_mean7 <- rowMeans(last7)
    sd7 <- apply(last7, 1, sd) * sqrt(1 + 1 / ncol(last7))
    X <- fourier(tr, K = 6)
    m <- tryCatch(auto.arima(tr, xreg = X, seasonal = FALSE, d = 0, max.p = 3, max.q = 3),
                  error = function(e) NULL)
    fd <- if (!is.null(m)) forecast(m, xreg = fourier(tr, K = 6, h = h), level = c(80, 95)) else NULL
    fs <- tryCatch(stlf(tr, h = h, s.window = 13, robust = TRUE, method = "ets", level = c(80, 95)),
                   error = function(e) NULL)
    row <- function(model, f, lo80 = NA, hi80 = NA, lo95 = NA, hi95 = NA)
      data.table(origin = o, step = 1:h, model = model, err = as.numeric(f) - te,
                 in80 = as.logical(te >= as.numeric(lo80) & te <= as.numeric(hi80)),
                 in95 = as.logical(te >= as.numeric(lo95) & te <= as.numeric(hi95)))
    res[[length(res) + 1]] <- rbind(
      row("Yesterday, same time", f_naive),
      row("Mean of last 7 days", f_mean7, f_mean7 - 1.28 * sd7, f_mean7 + 1.28 * sd7,
          f_mean7 - 1.96 * sd7, f_mean7 + 1.96 * sd7),
      if (!is.null(fd)) row("Harmonics + ARMA", as.numeric(fd$mean), fd$lower[, 1], fd$upper[, 1],
                            fd$lower[, 2], fd$upper[, 2]),
      if (!is.null(fs)) row("STL + ETS", as.numeric(fs$mean), fs$lower[, 1], fs$upper[, 1],
                            fs$lower[, 2], fs$upper[, 2]))
    if (!is.null(fd)) example <- list(origin = o, history = as.numeric(tail(tr, freq)), actual = te,
                                      mean = as.numeric(fd$mean), lo = as.numeric(fd$lower[, 2]),
                                      hi = as.numeric(fd$upper[, 2]))
  }
  res <- rbindlist(res)
  list(n_origins = uniqueN(res$origin), example = example,
       summary = res[, .(mae = mean(abs(err)), rmse = sqrt(mean(err^2)),
                         mae_0_6h = mean(abs(err[step <= 12])), mae_6_24h = mean(abs(err[step > 12])),
                         cover80 = mean(in80), cover95 = mean(in95)), by = model])
}
# How often would the daily report's hour-level rule fire on this data?
report_rule_rate <- function(g30, v, floor_sd, min_delta, z_warn = 3) {
  h <- g30[, .(value = mean(get(v), na.rm = TRUE)), by = .(t = as.numeric(time) %/% 3600 * 3600)]
  h <- h[!is.na(value)]; by_t <- setNames(h$value, h$t)
  out <- vapply(seq_len(nrow(h)), function(i) {
    ref <- by_t[as.character(h$t[i] - (1:7) * 86400)]; ref <- ref[!is.na(ref)]
    if (length(ref) < 3) return(NA)
    m <- median(ref); s <- max(mad(ref), floor_sd)
    abs(h$value[i] - m) / s >= z_warn && abs(h$value[i] - m) >= min_delta
  }, NA)
  list(hours_tested = sum(!is.na(out)), flagged = sum(out, na.rm = TRUE), rate = mean(out, na.rm = TRUE))
}

# ── Run per segment ─────────────────────────────────────────────────────
all_nights <- list(); all_days <- list(); all_events <- list(); all_gaps <- list()
for (s in names(segs)) {
  sg <- segs[[s]]; g5 <- sg$g5; g30 <- sg$g30; out <- list(label = sg$label, season = sg$season)
  g5 <- g5[time >= min(time[!is.na(local_temperature)])]      # other channels may start earlier
  message("segment ", s)
  # contiguous 30-min run with the most data (used for STL on RH and for back-testing)
  na30 <- is.na(g30$local_temperature); rl <- rle(na30)
  long_gap <- rl$values & rl$lengths >= 12; brk <- inverse.rle(list(values = long_gap, lengths = rl$lengths))
  run_id <- cumsum(c(FALSE, diff(brk) != 0)); keep <- !brk
  best <- as.integer(names(which.max(table(run_id[keep])))); run30 <- g30[run_id == best & keep]

  out$cosinor <- list(temperature = cosinor(g30, "local_temperature"),
                      humidity = if (has(g30, "local_humidity")) cosinor(g30, "local_humidity"))
  out$profile <- list(temperature = profile(g30, "local_temperature"),
                      humidity = if (has(g30, "local_humidity")) profile(g30, "local_humidity"),
                      room = if (has(g30, "room_temperature")) profile(g30, "room_temperature"),
                      freezer = if (has(g30, "freezer_status")) profile(g30, "freezer_status"))

  lev <- detect_level(g5, "local_temperature", 288, 300)
  out$stl <- list(temperature = lev$fit[c("F_seasonal", "F_trend", "rem_sd")])
  ev_T <- lev$events; if (!is.null(ev_T)) ev_T[, `:=`(variable = "temperature", detector = "level", unit = "°C")]
  jmp <- detect_jump(g5, "local_temperature", 300)
  if (!is.null(jmp)) jmp[, `:=`(variable = "temperature", detector = "jump", unit = "°C")]
  ev_H <- NULL
  if (has(g5, "local_humidity")) {
    lh <- detect_level(g5, "local_humidity", 288, 300, floor_sd = 0.3)
    out$stl$humidity <- lh$fit[c("F_seasonal", "F_trend", "rem_sd")]; ev_H <- lh$events
    if (!is.null(ev_H)) ev_H[, `:=`(variable = "humidity", detector = "level", unit = "%")]
  } else if (has(run30, "local_humidity")) {
    lh <- detect_level(run30, "local_humidity", 48, 1800, floor_sd = 0.3)
    out$stl$humidity <- lh$fit[c("F_seasonal", "F_trend", "rem_sd")]; ev_H <- lh$events
    if (!is.null(ev_H)) ev_H[, `:=`(variable = "humidity", detector = "level", unit = "%")]
  }
  if (!is.null(jmp)) {
    lights <- g5$light_status[match(jmp$start, g5$time)]
    jmp[, night := lights < 0.5]
    jmp[, near_mist := if (length(sg$mist)) vapply(as.numeric(start), function(t)
      any(as.numeric(sg$mist) > t - 600 & as.numeric(sg$mist) < t + 600), NA) else NA]
    # a sharp warm-up in the dark with no mist: what an opened door looks like
    jmp[, door_like := night & peak_dev >= 1 & !(near_mist %in% TRUE)]
  }
  if (length(sg$mist)) {
    hv <- if (has(g5, "local_humidity")) "local_humidity" else if (has(g5, "difference_humidity")) "difference_humidity"
    sgn <- if (identical(hv, "difference_humidity")) -1 else 1     # error = target - actual
    resp <- rbindlist(lapply(as.numeric(sg$mist), function(m) {
      i <- match(floor(m / 300) * 300, as.numeric(g5$time)); if (is.na(i) || i < 2 || i + 6 > nrow(g5)) return(NULL)
      data.table(night = g5$light_status[i] < 0.5,
                 dT = g5$local_temperature[i + 4] - g5$local_temperature[i - 1],
                 dRH = if (is.null(hv)) NA_real_ else sgn * (g5[[hv]][i + 4] - g5[[hv]][i - 1]))
    }))
    out$mist_response <- resp[!is.na(dT), .(n = .N, dT_20min = mean(dT), dRH_20min = mean(dRH, na.rm = TRUE)), by = night]
  }
  evs <- rbindlist(list(ev_T, jmp, ev_H), fill = TRUE)
  if (nrow(evs)) { evs[, segment := s]; all_events[[s]] <- evs }
  out$n_events <- if (nrow(evs)) evs[, .N, by = .(variable, detector)] else NULL

  # chart series: 15-min temperature with the expected band and flagged points
  ix <- seq(1, nrow(g5), by = 3)
  out$series <- data.table(t = iso(g5$time[ix]), value = r2(g5$local_temperature[ix]),
                           expected = r2(lev$fit$trend[ix] + lev$fit$seasonal[ix]),
                           band = r2(lev$band[ix]))

  ni <- nightly(g5, 300)
  n30 <- nightly(g30, 1800); n30 <- n30[!night %in% ni$night]     # nights only covered at 30 min
  nn <- rbind(ni, n30)[order(night)]; nn[, segment := s]; all_nights[[s]] <- nn
  if (has(g5, "room_temperature")) out$thermal <- thermal_night(g5)

  dd <- daily_features(g30, 1800); dd[, segment := s]; all_days[[s]] <- dd
  all_gaps[[s]] <- rbindlist(lapply(intersect(c("local_temperature", "room_temperature"), names(g30)),
                                    function(v) gaps(g30, v, 1800)))[, segment := s]

  out$backtest <- backtest(run30$local_temperature)
  out$backtest$run <- c(iso(min(run30$time)), iso(max(run30$time)))
  if (!is.null(out$backtest$example)) {
    o <- out$backtest$example$origin
    out$backtest$example$t0 <- iso(run30$time[o] - 47 * 1800)   # first history point
  }
  grid <- CJ(floor_sd = c(0.3, 0.6, 0.9, 1.2), min_delta = c(0.5, 1, 1.5, 2))
  grid[, rate := mapply(function(f, d) report_rule_rate(g30, "local_temperature", f, d)$rate, floor_sd, min_delta)]
  out$report_rule <- list(
    temperature = report_rule_rate(g30, "local_temperature", 0.3, 0.5), temperature_grid = grid,
    humidity = if (has(g30, "local_humidity")) report_rule_rate(g30, "local_humidity", 2, 3),
    humidity_grid = if (has(g30, "local_humidity")) {
      gh <- CJ(floor_sd = c(2, 3, 4, 5), min_delta = c(3, 5, 7, 9))
      gh[, rate := mapply(function(f, d) report_rule_rate(g30, "local_humidity", f, d)$rate, floor_sd, min_delta)]; gh })
  # two-day rhythm (e.g. an alternating-night experiment): lag-1 autocorrelation of night minima
  if (nrow(ni) >= 8) out$night_lag1 <- cor(head(ni$T_min, -1), ni$T_min[-1])
  out$level_events <- if (!is.null(ev_T)) ev_T[, .(start = iso(start), end = iso(end), peak_time = iso(peak_time),
                                                    peak_dev = r2(peak_dev), minutes = round(minutes),
                                                    value = r2(g5$local_temperature[match(peak_time, g5$time)]))]
  out$door_like <- if (!is.null(jmp) && any(jmp$door_like)) jmp[door_like == TRUE, .(
    peak_time = iso(peak_time), rise = r2(peak_dev),
    value = r2(g5$local_temperature[pmin(match(peak_time, g5$time) + 1, nrow(g5))]))]
  R$segments[[s]] <- out
}
nights <- rbindlist(all_nights, fill = TRUE); days <- rbindlist(all_days, fill = TRUE)
events <- rbindlist(all_events, fill = TRUE); gap_tab <- rbindlist(all_gaps, fill = TRUE)

# ── 6. Night floor vs room temperature ──────────────────────────────────
nights[, saturated := frz_duty >= SAT_DUTY]
nr <- nights[!is.na(room)]
sat <- nr[saturated == TRUE]; sat[, dT := room - T_min]
by_seg <- sat[, .(n = .N, dT = mean(dT), sd = sd(dT)), by = segment]
ref <- sat[segment == tail(names(segs), 1)]                 # most recent configuration
if (nrow(ref) < 4) ref <- sat
dT_sat <- mean(ref$dT); sd_sat <- sd(ref$dT); n_sat <- nrow(ref)
tq <- qt(0.95, n_sat - 1) * sd_sat * sqrt(1 + 1 / n_sat)
room_grid <- seq(20, 30, 1)
R$night_floor <- list(
  nights = nights[, .(night = as.character(night), segment, T_min = r2(T_min), room = r2(room),
                      duty = r2(frz_duty), saturated)],
  n_nights = nrow(nights), n_with_room = nrow(nr), n_saturated = nrow(sat),
  by_segment = by_seg, dT_sat = dT_sat, dT_sd = sd_sat, n_ref = n_sat, pi90 = tq,
  target = NIGHT_TARGET, break_even_room = NIGHT_TARGET + dT_sat,
  slope_all = unname(coef(lm(T_min ~ room, nr))[2]),
  predict = data.table(room = room_grid, floor = pmax(NIGHT_TARGET, room_grid - dT_sat),
                       lo = pmax(NIGHT_TARGET, room_grid - dT_sat - tq), hi = pmax(NIGHT_TARGET, room_grid - dT_sat + tq)),
  sat_share = nights[, .(nights = .N, saturated = sum(saturated)), by = segment],
  last_sat_streak = { r <- rle(nights[order(night)]$saturated); if (tail(r$values, 1)) tail(r$lengths, 1) else 0 })

# ── 7. Day-level multivariate anomalies and regime changes ──────────────
feat <- c("T_min", "T_max", "RH_mean", "RH_min", "duty")
ok <- days[coverage >= 0.9 & complete.cases(days[, feat, with = FALSE])]
floors <- c(T_min = 0.4, T_max = 0.5, RH_mean = 1.5, RH_min = 2.5, duty = 0.03)   # smallest spread worth scaling by
Z <- ok[, Map(function(x, f) (x - median(x)) / max(mad(x), f), .SD, floors[feat]), by = segment, .SDcols = feat]
Zm <- as.matrix(Z[, feat, with = FALSE]); mcd <- covMcd(Zm, alpha = 0.75)
ok[, d2 := mahalanobis(Zm, mcd$center, mcd$cov)]
cut <- qchisq(0.975, length(feat))
zc <- sweep(Zm, 2, mcd$center) / sqrt(diag(mcd$cov))
ok[, driver := apply(zc, 1, function(r) { k <- order(-abs(r))[1:2]
  paste(sprintf("%s %s", feat[k], ifelse(r[k] > 0, "high", "low")), collapse = ", ") })]
R$day_anomalies <- list(n_days = nrow(ok), cutoff = cut,
  flagged = ok[d2 > cut][order(-d2), .(date = as.character(date), segment, d2 = r2(d2, 1), driver,
                                      T_min = r2(T_min, 1), T_max = r2(T_max, 1), RH_mean = r2(RH_mean, 0),
                                      RH_min = r2(RH_min, 0), duty = r2(duty))],
  outage_days = days[coverage < 0.9, .(date = as.character(date), segment, coverage = r2(coverage))])
R$days <- days[, .(date = as.character(date), segment, coverage = r2(coverage), T_min = r2(T_min, 1),
                   T_max = r2(T_max, 1), RH_mean = r2(RH_mean, 1), fog_h = r2(fog_h, 1), duty = r2(duty, 3),
                   room = r2(room, 1), mist_n)]
breaks_of <- function(d, v, h = 4) {
  d <- d[coverage >= 0.9 & !is.na(get(v))]; if (nrow(d) < 2 * h + 2) return(NULL)
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

# ── 8. Events table ─────────────────────────────────────────────────────
if (nrow(events)) {
  events[, score := abs(peak_z) * sqrt(pmax(minutes, 5) / 5)]
  setorder(events, -score)
  if (!"door_like" %in% names(events)) events[, `:=`(door_like = NA, near_mist = NA, night = NA)]
  R$events <- list(counts = events[, .N, by = .(segment, variable, detector)],
    jumps = events[detector == "jump", .(n = .N, near_mist = sum(near_mist %in% TRUE), door_like = sum(door_like %in% TRUE)), by = segment],
    door_like = events[door_like %in% TRUE][order(start), .(segment, start_local = loc(start), minutes = round(minutes), rise = r2(peak_dev))],
    top = events[, head(.SD, 6), by = .(segment, variable, detector)][
      , .(segment, variable, detector, start = iso(start), start_local = loc(start), minutes = round(minutes),
          peak_dev = r2(peak_dev), peak_z = r2(peak_z, 1), unit)])
  fwrite(events[, .(segment, variable, detector, start = iso(start), end = iso(end), minutes,
                    peak_dev, peak_z)], file.path(out_dir, "anomaly_events.csv"))
}
R$gaps <- gap_tab[, .(segment, variable, from = iso(from), from_local = loc(from), to_local = loc(to), hours = r2(hours, 1))]

# ── 9. Weekly running totals (ledger) ───────────────────────────────────
if (!is.null(arg("--ledger"))) {
  led <- fread(arg("--ledger"))
  led[, t := as.POSIXct(as_of, format = "%Y-%m-%dT%H:%M:%SZ", tz = "UTC")]
  led <- led[c(TRUE, diff(as.numeric(t)) > 1.5 * 86400)]         # drop same-day duplicates
  iv <- data.table(from = head(led$t, -1), to = led$t[-1])
  iv[, days := as.numeric(to - from, units = "days")]
  for (v in c("kwh", "mist_cycles", "fog_hours", "data_points"))
    set(iv, j = paste0(v, "_per_day"), value = diff(led[[v]]) / iv$days)
  bp <- breakpoints(iv$kwh_per_day ~ 1, h = 3); b <- bp$breakpoints[1]
  pre <- iv$kwh_per_day[1:b]; post <- iv$kwh_per_day[(b + 1):nrow(iv)]
  wt <- t.test(post, pre)
  today <- as.POSIXct(Sys.Date(), tz = "UTC"); last <- tail(led, 1)
  d_left <- as.numeric(today - last$t, units = "days")
  R$ledger <- list(
    intervals = iv[, .(from = iso(from), to = iso(to), days = r2(days, 1), kwh_per_day = r2(kwh_per_day),
                       mist_per_day = r2(mist_cycles_per_day, 1), fog_h_per_day = r2(fog_hours_per_day),
                       points_per_day = round(data_points_per_day))],
    kwh_break = list(date = iso(iv$from[b + 1]), before = mean(pre), after = mean(post),
                     step = unname(wt$estimate[1] - wt$estimate[2]), ci = as.numeric(wt$conf.int),
                     p = wt$p.value, after_sd = sd(post)),
    last = list(as_of = iso(last$t), kwh = last$kwh, mist_cycles = last$mist_cycles, fog_hours = last$fog_hours),
    projection = list(as_of = as.character(Sys.Date()), days_since = d_left,
      kwh_if_summer_rate_held = last$kwh + d_left * mean(post),
      kwh_if_back_to_spring_rate_from_october = last$kwh +
        as.numeric(as.POSIXct("2026-10-01", tz = "UTC") - last$t, units = "days") * mean(post) +
        as.numeric(today - as.POSIXct("2026-10-01", tz = "UTC"), units = "days") * mean(pre)))
}

write_json(R, file.path(out_dir, "results.json"), auto_unbox = TRUE, digits = 4, na = "null", null = "null")
fwrite(nights, file.path(out_dir, "nights.csv")); fwrite(days, file.path(out_dir, "days.csv"))
message("wrote ", file.path(out_dir, "results.json"))
