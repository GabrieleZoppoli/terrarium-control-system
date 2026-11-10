# Cleaning and gap-tolerant decomposition.
#
# Rule used throughout the analysis: a reading is used to estimate anything
# (daily curve, thermal model, forecasts, thresholds) only if it is
#   1. actually measured (not missing, not a carried-forward value recorded
#      while the system was down, not a flat-lined sensor),
#   2. not inside a flagged anomaly, and
#   3. not on a day that is mostly abnormal.
# Nothing is filled in. Detection and estimation are iterated: fit on clean
# rows, flag, remove, refit, until the set of clean rows stops changing.

# ── Local linear smoother that ignores missing points ───────────────────
loclin <- function(x, y, x0, q, rw = NULL) {
  ok <- !is.na(y); xa <- x[ok]; ya <- y[ok]; n <- length(xa)
  ra <- if (is.null(rw)) rep(1, n) else rw[ok]
  if (n == 0) return(rep(NA_real_, length(x0)))
  if (n < 3) return(rep(mean(ya), length(x0)))
  vapply(x0, function(u) {
    d <- abs(xa - u)
    h <- if (q <= n) sort(d)[q] else max(d) * q / n
    h <- max(h, 1e-9); w <- pmax(0, 1 - (d / h)^3)^3
    if (sum(w * ra) > 1e-9) w <- w * ra                 # robustness weights, unless they cancel everything
    if (sum(w > 0) < 2) return(sum(w * ya) / max(sum(w), 1e-12))
    sw <- sum(w); mx <- sum(w * xa) / sw; my <- sum(w * ya) / sw
    sxx <- sum(w * (xa - mx)^2)
    if (sxx < 1e-12) my else my + sum(w * (xa - mx) * (ya - my)) / sxx * (u - mx)
  }, 0)
}

# ── STL that skips rows instead of needing a complete series ────────────
# Same structure as Cleveland's STL: smooth each time-of-day slot across days
# (cycle-subseries, span s.window days), remove its low-frequency part, then
# loess the de-seasonalised series for the trend. Rows with ok = FALSE carry
# no weight anywhere; components are still returned for every row.
stl_na <- function(y, slot, cyc, ok, period, s.window = 13, n_iter = 2, n_robust = 2) {
  n <- length(y); tt <- seq_len(n)
  yy <- ifelse(ok, y, NA_real_); rw <- rep(1, n)
  trend <- rep(median(yy, na.rm = TRUE), n); seas <- numeric(n)
  t.window <- ceiling(1.5 * period / (1 - 1.5 / s.window)); t.window <- t.window + (t.window %% 2 == 0)
  idx_by_slot <- split(tt, slot)
  for (pass in 0:n_robust) {          # pass 0 is plain; later passes down-weight large remainders
  for (it in seq_len(n_iter)) {
    detr <- yy - trend; C <- numeric(n)
    for (ix in idx_by_slot) C[ix] <- loclin(cyc[ix], detr[ix], cyc[ix], s.window, rw[ix])
    C[is.na(C)] <- 0
    L <- as.numeric(stats::filter(C, rep(1 / period, period), sides = 2))
    first <- which(!is.na(L))[1]; last <- tail(which(!is.na(L)), 1)
    if (is.na(first)) L[] <- mean(C) else { L[seq_len(first - 1)] <- L[first]; if (last < n) L[(last + 1):n] <- L[last] }
    seas <- C - L
    z <- yy - seas; k <- which(!is.na(z))
    lo <- stats::loess(z ~ tt, data = data.frame(z = z[k], tt = tt[k]), weights = pmax(rw[k], 1e-6),
                       span = min(1, t.window / length(k)), degree = 1, control = stats::loess.control(surface = "direct"))
    trend <- as.numeric(predict(lo, data.frame(tt = tt)))
  }
    u <- abs(yy - trend - seas) / (6 * median(abs(yy - trend - seas), na.rm = TRUE))
    rw <- ifelse(is.na(u), 0, ifelse(u < 1, (1 - u^2)^2, 0))        # bisquare, as in STL's outer loop
  }
  rem <- y - trend - seas
  list(trend = trend, seasonal = seas, remainder = rem)
}

run_flags <- function(flag, min_run) {              # keep only runs of TRUE at least min_run long
  r <- rle(flag); r$values <- r$values & r$lengths >= min_run; inverse.rle(r)
}
pad_flags <- function(flag, pad) {
  if (pad <= 0 || !any(flag)) return(flag)
  i <- which(flag); out <- flag
  for (k in seq_len(pad)) { out[pmin(i + k, length(flag))] <- TRUE; out[pmax(i - k, 1)] <- TRUE }
  out
}
scale_by <- function(x, grp, use, floor_sd) {       # robust spread per group, from usable rows only
  g_all <- mad(x[use], na.rm = TRUE)
  s <- tapply(x[use], grp[use], function(v) if (sum(!is.na(v)) >= 20) mad(v, na.rm = TRUE) else NA_real_)
  out <- s[as.character(grp)]; out[is.na(out)] <- g_all
  pmax(as.numeric(out), floor_sd)
}

# ── Rows that are not measurements ──────────────────────────────────────
mark_artifacts <- function(g, step, recovery_h = 6) {
  na <- is.na(g$local_temperature); r <- rle(na); e <- cumsum(r$lengths); s <- e - r$lengths + 1
  outage <- inverse.rle(list(values = r$values & r$lengths * step >= 1800, lengths = r$lengths))
  recovery <- rep(FALSE, nrow(g))
  for (k in which(r$values & r$lengths * step >= 3600 & s > 1)) {   # restart after >= 1 h down
    a <- e[k] + 1; b <- min(nrow(g), e[k] + recovery_h * 3600 / step); if (a <= b) recovery[a:b] <- TRUE
  }
  rv <- rle(g$local_temperature)
  flat <- inverse.rle(list(values = !is.na(rv$values) & rv$lengths * step >= 3600, lengths = rv$lengths))
  list(outage = outage, recovery = recovery, flat = flat)
}

# ── Iterative detect → remove → refit for one channel ───────────────────
clean_channel <- function(g, v, step, base_ok, k_level = 4.5, k_jump = 7, min_run = 3, pad = 2,
                          floor_level = 0.05, floor_jump = 0.02, jumps = TRUE, remove = TRUE, max_iter = 8,
                          excuse = NULL, excuse_max = 1) {
  # excuse: rows where the controller did something (freezer or lights switched, a mist fired).
  # A jump there smaller than excuse_max is normal operation: recorded, but not removed.
  period <- 86400 / step; y <- g[[v]]
  slot <- as.integer(round(g$hour * period / 24)) %% period
  cyc <- as.integer(g$date - min(g$date)); hr <- floor(g$hour); half <- floor(g$hour * 2)
  meas <- base_ok & !is.na(y)        # every measured row. Spreads are always taken over these:
  ok <- meas; iters <- 0; removed <- rep(FALSE, length(y))   # a spread recomputed on trimmed data shrinks every
  repeat {                           # pass and the flags run away. MAD is robust enough as is.
    iters <- iters + 1
    f <- stl_na(y, slot, cyc, ok, period)
    z <- f$remainder / scale_by(f$remainder, hr, meas, floor_level)
    lev <- run_flags(!is.na(z) & abs(z) >= k_level, min_run) | (!is.na(z) & abs(z) >= 1.5 * k_level)
    jz <- rep(NA_real_, length(y)); jmp <- rep(FALSE, length(y)); dd <- jz; jmp_rm <- jmp
    if (jumps) {
      d <- c(NA, diff(y)); okd <- ok & c(FALSE, head(ok, -1)); measd <- meas & c(FALSE, head(meas, -1))
      med <- tapply(d[okd], half[okd], median, na.rm = TRUE)       # usual change in that half hour
      dd <- d - ifelse(is.na(med[as.character(half)]), 0, med[as.character(half)])
      jz <- dd / scale_by(dd, half, measd, floor_jump)
      jmp <- !is.na(jz) & abs(jz) >= k_jump
      jmp_rm <- if (is.null(excuse)) jmp else jmp & !(excuse & abs(dd) < excuse_max)
    }
    flagged <- pad_flags(lev | jmp_rm, pad)
    removed <- removed | flagged     # once out, a row stays out, so the loop cannot oscillate
    new_ok <- meas & !(remove & removed)
    changed <- mean(new_ok != ok)
    ok <- new_ok
    if (!remove || changed < 0.002 || iters >= max_iter) break
  }
  list(fit = f, z = z, band = k_level * scale_by(f$remainder, hr, meas, floor_level), level = lev, jump = jmp,
       jump_removed = jmp_rm, jz = jz, jdev = dd, flagged = if (remove) removed else flagged, ok = ok, iters = iters)
}
