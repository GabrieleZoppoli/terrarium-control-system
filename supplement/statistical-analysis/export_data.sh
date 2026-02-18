#!/bin/bash
# Export InfluxDB data for analysis scripts
# Run this before the Python scripts if CSVs are missing/stale

DIR="/home/pi/terrarium-analysis/data"
DAYS="${1:-14}"
mkdir -p "$DIR"

echo "Exporting last ${DAYS} days from InfluxDB..."

measurements=(
    "local_humidity"
    "local_temperature"
    "room_temperature"
    "room_humidity"
    "fan_speed"
    "freezer_status"
    "mister_status"
    "target_humidity_computed:target_humidity"
    "target_temperature_computed:target_temperature"
    "vpd"
    "night_test_mode"
)

for entry in "${measurements[@]}"; do
    # Support "influx_name:file_name" or just "name"
    IFS=':' read -r meas fname <<< "$entry"
    fname="${fname:-$meas}"
    influx -database highland -execute \
        "SELECT mean(value) FROM ${meas} WHERE time > now() - ${DAYS}d GROUP BY time(5m) fill(none)" \
        -format csv > "${DIR}/${fname}.csv" 2>/dev/null &
done

wait
echo "Done. Exported to ${DIR}/:"
wc -l "${DIR}"/*.csv
