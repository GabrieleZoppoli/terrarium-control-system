# Loaders for the terrarium time-series analysis.
#
# Two kinds of input are understood:
#   1. An export directory written by scripts/export-history.sh on the Pi:
#      one CSV per measurement in `influx -format csv` shape
#      (name,time,<agg>) with nanosecond epoch times.
#   2. The historical snapshots kept in the terrarium-analysis repo
#      (data/, dawnmist-2026-06-11/, pidstats-2026-06-10/).
#
# Everything is returned as one long data.table:
#   source, variable, time (POSIXct, UTC), value, step_s
suppressPackageStartupMessages({
  library(data.table)
  library(jsonlite)
})

TZ_LOCAL <- "Europe/Rome"

read_influx_csv <- function(path, variable = NULL, source = "export") {
  d <- if (grepl("\\.gz$", path)) fread(cmd = paste("gzip -dc", shQuote(path)), showProgress = FALSE, integer64 = "double")
       else fread(path, showProgress = FALSE, integer64 = "double")
  if (!nrow(d)) return(NULL)
  setnames(d, c("name", "time", "value")[seq_len(ncol(d))])
  d <- d[!is.na(value)]
  t <- as.numeric(d$time)
  # influx writes ns; tolerate s / ms too
  div <- if (median(t) > 1e17) 1e9 else if (median(t) > 1e11) 1e3 else 1
  t <- t / div
  data.table(source = source,
             variable = if (is.null(variable)) sub("\\.csv(\\.gz)?$", "", basename(path)) else variable,
             time = as.POSIXct(t, origin = "1970-01-01", tz = "UTC"),
             value = suppressWarnings(as.numeric(d$value)),
             step_s = as.numeric(median(diff(t))))
}

read_influx_json <- function(path, variable, col = 2, source = "snapshot") {
  # files may hold several concatenated JSON documents (one per line)
  txt <- readLines(path, warn = FALSE)
  txt <- txt[nzchar(txt)]
  out <- rbindlist(lapply(txt, function(x) {
    j <- fromJSON(x, simplifyVector = FALSE)
    s <- j$results[[1]]$series
    if (is.null(s)) return(NULL)
    v <- s[[1]]$values
    tt <- vapply(v, function(r) as.character(r[[1]]), "")
    val <- vapply(v, function(r) if (is.null(r[[col]])) NA_real_ else as.numeric(r[[col]]), 0)
    t <- if (grepl("T", tt[1])) as.numeric(as.POSIXct(tt, format = "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"))
         else as.numeric(tt)
    data.table(time = t, value = val)
  }))
  out <- out[!is.na(value)]
  setorder(out, time)
  data.table(source = source, variable = variable,
             time = as.POSIXct(out$time, origin = "1970-01-01", tz = "UTC"),
             value = out$value, step_s = as.numeric(median(diff(out$time))))
}

load_export_dir <- function(dir, source = "export") {
  files <- list.files(dir, pattern = "\\.csv(\\.gz)?$", full.names = TRUE)
  rbindlist(lapply(files, read_influx_csv, source = source), fill = TRUE)
}

# Historical snapshots in the terrarium-analysis repo.
load_snapshots <- function(repo) {
  rename <- c(target_temperature = "target_temperature_computed",
              target_humidity = "target_humidity_computed")
  feb <- load_export_dir(file.path(repo, "data"), source = "feb")
  feb[variable %in% names(rename), variable := rename[variable]]

  dm <- file.path(repo, "dawnmist-2026-06-11")
  jun <- rbindlist(list(
    read_influx_json(file.path(dm, "cabT.txt"),    "local_temperature", source = "jun30"),
    read_influx_json(file.path(dm, "cabRH.txt"),   "local_humidity",    source = "jun30"),
    read_influx_json(file.path(dm, "roomT.txt"),   "room_temperature",  source = "jun30"),
    read_influx_json(file.path(dm, "roomRH.txt"),  "room_humidity",     source = "jun30"),
    read_influx_json(file.path(dm, "freezer.txt"), "freezer_status",    source = "jun1"),
    read_influx_json(file.path(dm, "lights.txt"),  "light_status",      source = "jun1"),
    read_influx_json(file.path(dm, "mist.txt"),    "mist_event",        source = "junev")
  ))
  ps <- file.path(repo, "pidstats-2026-06-10")
  jun5 <- rbindlist(list(
    read_influx_json(file.path(ps, "lt5m.json"),  "local_temperature",     source = "jun5"),
    read_influx_json(file.path(ps, "lt5m.json"),  "local_temperature_max", col = 3, source = "jun5"),
    read_influx_json(file.path(ps, "dh5m.json"),  "difference_humidity",   source = "jun5"),
    read_influx_json(file.path(ps, "fs5m.json"),  "fan_speed",             source = "jun5"),
    read_influx_json(file.path(ps, "pm5m.json"),  "pid_control_mode",      source = "jun5"),
    read_influx_json(file.path(ps, "wbt5m.json"), "wbt_shutdown_active",   source = "jun5")
  ))
  rbindlist(list(feb, jun, jun5), fill = TRUE)
}

# Regular grid: average `value` into `step`-second buckets, one column per variable.
to_grid <- function(long, step = 300, vars = NULL, fun = mean) {
  d <- if (is.null(vars)) long else long[variable %in% vars]
  d <- d[, .(value = fun(value)),
         by = .(variable, time = as.POSIXct(floor(as.numeric(time) / step) * step,
                                            origin = "1970-01-01", tz = "UTC"))]
  w <- dcast(d, time ~ variable, value.var = "value")
  full <- data.table(time = seq(min(w$time), max(w$time), by = step))
  w <- w[full, on = "time"]
  w[, local := as.POSIXct(format(time, tz = TZ_LOCAL, usetz = FALSE), tz = "UTC")]  # wall clock
  w[, hour := as.numeric(format(time, "%H", tz = TZ_LOCAL)) +
              as.numeric(format(time, "%M", tz = TZ_LOCAL)) / 60]
  w[, date := as.Date(format(time, "%Y-%m-%d", tz = TZ_LOCAL))]
  w[]
}
