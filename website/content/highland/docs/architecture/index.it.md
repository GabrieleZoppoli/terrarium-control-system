---
title: "Architettura del sistema"
description: "Livelli hardware, protocolli di comunicazione e stack software"
---


## Panoramica hardware

### Raspberry Pi (hub di controllo)

Il Raspberry Pi esegue tutti i servizi software e fa da controller centrale:

- **OS**: Linux Debian-based (kernel 6.1.0, ARMv8)
- **Servizi**: Node-RED, InfluxDB, Grafana, broker MQTT Mosquitto, arduino-watchdog
- **Rete**: Ethernet/WiFi per l'API meteo e il monitoraggio remoto

### Arduino Mega 2560 (interfaccia GPIO)

Collegato via USB seriale (`/dev/ttyACM0`) a 115200 baud, esegue un protocollo testuale custom (vedi `arduino-terrarium.ino`). Ha sostituito StandardFirmata a febbraio 2026 per maggiore affidabilità e debuggabilità.

**Protocollo seriale**:

- Pi → Arduino: `P<pin>,<value>` (PWM), `Q` (query stati), `H,<value>` (config heartbeat)
- Arduino → Pi: `READY` (boot), `H,<value>` (heartbeat ogni 2 s), `D<pin>,<0|1>` (stato porta), `OK,P<pin>,<value>` (ack), `S,P8=...,P12=...,P44=...,P45=...,P46=...` (stato)

**Assegnazione pin**:
| Pin | Tipo | Timer | Funzione |
|-----|------|-------|---------|
| 8 | PWM Output | Timer 4 (~490 Hz) | Dimmer LED (rampe alba/tramonto) |
| 12 | PWM Output | Timer 1 (25 kHz) | Ventole di circolazione interna (OC1B) |
| 44 | PWM Output | Timer 5 (25 kHz) | Ventole freezer/evaporatore (OC5C) |
| 45 | PWM Output | Timer 5 (25 kHz) | Ventola outlet — estrattore umidità (OC5B) |
| 46 | PWM Output | Timer 5 (25 kHz) | Ventola impeller — aspirazione aria (OC5A) |
| A0 | Analog Input | — | Riferimento heartbeat (analog read inviato ogni 2 s) |
| D22 | Digital Input | — | Reed switch porta sinistra (INPUT_PULLUP, LOW=aperta) |
| D24 | Digital Input | — | Reed switch porta destra (INPUT_PULLUP, LOW=aperta) |

**Percorso USB**: `/sys/bus/usb/devices/1-1.1` (vendor `2341:0042`)

**Frequenza PWM**: i pin 12, 44, 45, 46 usano PWM phase-correct a 25 kHz (ICRn=320, prescaler=1). Fuori dall'intervallo udibile e compatibile con l'input PWM a 4 pin delle ventole Noctua. Il pin 8 usa il default (~490 Hz), adeguato all'ingresso analogico di dimming del driver LED.

### ESP8266 + sensore SHT35

Pubblica le letture di temperatura e umidità sul broker MQTT circa ogni secondo. L'SHT35 garantisce ±0,1 °C e ±1,5 % UR. Lo stesso ESP8266 legge anche un sensore ultrasonico HC-SR04 per il livello dell'acqua.

**Struttura dei topic MQTT**: `[configurata per installazione]`

### Smart plug TP-Link Tapo P100 (×3)

Commutano l'alimentazione di rete per carichi ad alta corrente, controllate dalla libreria Python PyP100 da nodi function Python in Node-RED.

| Presa | IP | Controlla |
|-------|----|-----------|
| Luci | 192.168.1.55 | Array 4×100 W ChilLED Logic Puck V3 |
| Nebulizzatore | 192.168.1.199 | Pompa a diaframma MistKing |
| Compressore | 192.168.1.196 | Unità compressore Vitrifrigo ND50 |

### Smart plug Meross MSS310

Presa con monitoraggio energia a 192.168.1.92 sulla linea principale. Un daemon Python persistente (`meross_daemon.py`) mantiene una singola sessione autenticata con l'API cloud Meross (iotx-eu.meross.com) e pubblica le letture istantanee sul broker MQTT locale (`meross/power/watts`) ogni 2 secondi. Ha sostituito l'approccio precedente che faceva spawning di un nuovo processo ogni 120 secondi, con un ciclo completo login/discover/logout. Il daemon accetta anche comandi on/off via MQTT (`meross/power/command`), abilitando risposta sub-secondo al pulsante di panico sulla dashboard. Gira come servizio systemd (`meross-daemon`) con restart automatico al fallimento.

### Reed switch porte (×2)

Reed switch magnetici sui due pannelli frontali scorrevoli, collegati ad Arduino D22 (sinistra) e D24 (destra) con resistori di pull-up interni. Porta aperta = LOW. L'Arduino fa polling a 100 ms, riporta al cambio di stato più un heartbeat periodico ogni 10 s. Un debounce software di 3 secondi in Node-RED sopprime il rimbalzo dei contatti.

## Stack software

### Node-RED v3.1.3 (motore di controllo)

**Porta**: 1880
**Servizio**: `systemctl status nodered`
**Directory di config**: `~/.node-red/`

Sette tab di flusso organizzano la logica di controllo:

#### Tab Lights
- **Photoperiod Calculator** (function): calcola la durata del giorno per Chinchiná (4,98° N) usando la declinazione solare. Limitata a 10–14 h, centrata sulle 13:15 ora di Genova. Parte allo startup (delay 5 s) e quotidianamente alle 00:05.
- **Unified Light Scheduler** (function): riceve tick ogni minuto, legge le variabili globali del fotoperiodo. Controlla on/off Tapo e i trigger delle rampe dimmer a tempi calcolati dinamicamente.
- **Dynamic Dimmer #1**: rampa PWM 30 min per alba/tramonto, slider 0↔40
- **Dynamic Dimmer #2**: rampa mezzogiorno 30 min (proporzionale alla durata del giorno), slider 40↔60
- **Startup brightness**: rileva restart nella finestra di rampa usando i tempi dinamici del fotoperiodo, emette uno "start parziale" per completare in orario
- **Writer pin 8**: invia `P8,<valore>` via seriale; memorizza `last_dimmer_pwm`, forza PWM 102 durante la door safety
- **Python function**: controllo Tapo P100 per la presa luci (con door-safety gate)
- *Disabilitati*: BigTimer (schedule fisso), 4 time-inject, 4 function di rampa — sostituiti dallo scheduler dinamico

#### Tab Humidity
- **MQTT In**: riceve temperatura + umidità SHT35 dall'ESP
- **VPD Calculator** (function): calcola il Vapor Pressure Deficit con la formula di Magnus
- **Target humidity**: derivato dai dati meteo colombiani (cap massimo 95 % UR)
- **Humidity difference**: target − misurata, alimenta il PID sul tab Fans
- **Hysteresis**: controlla on/off del nebulizzatore attorno al target
- **Python function**: controllo Tapo P100 del nebulizzatore (con door-safety gate)

#### Tab Temperature
- **Target temperature**: derivata dai dati meteo colombiani (limitata 12–24 °C)
- **Temperature difference**: target − misurata
- **Hysteresis**: controlla on/off del compressore sull'errore
- **Python function**: controllo Tapo P100 del compressore (con door-safety gate)

#### Tab Fans
- **PID Controller** (function): controllo ventola con gain scheduling a tre regimi (Kp=50, Ki=0,5, Kd=10). Normal (T<24 °C): PID umidità. Warm (24–25 °C, freezer off): PID temperatura per raffreddamento evaporativo. Hot (≥25 °C): PID umidità con freezer attivo.
- **Day/Night Check**: within-time-switch 04:00–00:00 (mezzanotte)
- **Night Mode (A/B sospeso)**: sempre output 0 (codice A/B preservato nei commenti per la riattivazione)
- **Mister Interlock** (function): ferma tutte le ventole quando il nebulizzatore è attivo
- **Manual Override**: slider Dashboard, controllo a priorità massima
- **Fan writers**: 4 nodi seriale (outlet pin 45, impeller pin 46, evaporatore pin 44, circolazione pin 12), tutti door-safety gated
- **RBE nodes**: logging report-by-exception per i cambi PWM
- **Door safety controller**: fa OR delle due porte con debounce 3 s, attiva la safety mode
- **Door safety outputs**: 4 uscite (stop ventole, compressore off, nebulizzatore off, luci al 60 %)

#### Tab Weather
- **OpenWeatherMap**: 4 istanze per Chinchiná, Medellín, Bogotá, Sonsón
- **Aggregator/Smooth**: media e smoothing dei valori meteo (finestra InfluxDB 30 min + rolling 15 min su 4 città)
- **Position config**: lat=5,19485 (riferimento tepui), lon=8,944381 (Genova) per i calcoli astronomici
- **Weather fallback**: curva storica 14 giorni (288 slot, smooth a due passaggi) quando l'API non è raggiungibile; fallback finale (giorno T=24/UR=85, notte T=14/UR=90) se non ci sono dati storici
- **Historical curve builder**: ricostruisce ogni 6 ore dai dati InfluxDB; applica uno shift temporale di 15 ore baked nelle slot della curva

#### Tab Charts
- Componenti **Dashboard UI**: gauge (T, UR, VPD), grafici time-series, LED di stato
- **Grafici a 3 serie**: temperatura e umidità mostrano misurata (blu), target (rossa), stanza (verde)
- **Room data inject**: repeat 60 s, legge `room_temperature`/`room_humidity` globali
- **Chart persistence**: dati salvati in flow context, ripristinati allo startup via nodi inject
- Visualizzazione in tempo reale e storica dentro la Dashboard Node-RED

#### Tab Utilities
- **Data Logger**: function node con 16 uscite, triggerato ogni 60 s
- Ogni uscita si collega a un singolo nodo InfluxDB out
- Legge tutte le variabili del global context e scrive nel database `highland`
- **Serial config**: porta seriale 115200 baud, delimitatore \n
- **Serial parser**: fa il parsing di heartbeat (H,val), stati porte (D22/D24), messaggi di errore
- **Monitoraggio Meross**: sottoscrizione MQTT (`meross/power/watts`) dal daemon persistente → parse → UI + InfluxDB (aggiornamenti 2 s)
- **Mist counter persistence**: salva/ripristina i conteggi nebulizzazione di oggi e ieri fra riavvii
- **Resend PWM**: re-invio periodico delle velocità ventola correnti per evitare stato seriale stantio

### Dipendenze dei nodi Node-RED

Pacchetti npm richiesti (installali in `~/.node-red/`):

| Pacchetto | Tipi di nodo usati |
|-----------|---------------------|
| `node-red-contrib-bigtimer` | bigtimer |
| `node-red-node-openweathermap` | openweathermap |
| `node-red-contrib-influxdb` | influxdb out, influxdb in |
| `node-red-node-smooth` | smooth |
| `node-red-contrib-python-function-ps` | python-function-ps |
| `node-red-contrib-dynamic-dimmer` | dynamic-dimmer |
| `node-red-contrib-sun-position` | position-config, within-time-switch, time-inject |
| `node-red-node-rbe` | rbe |
| `node-red-contrib-stoptimer-varidelay` | stoptimer-varidelay |
| `node-red-contrib-aggregator` | aggregator |
| `node-red-contrib-hysteresis` | hysteresis |
| `node-red-contrib-ui-led` | ui_led |
| `node-red-contrib-ui-statetrail` | ui_statetrail |
| `node-red-dashboard` | ui_base, ui_tab, ui_group, ui_gauge, ui_chart, ui_text, ui_button, ui_slider, ui_spacer |
| `node-red-node-serialport` | serial in, serial out, serial port |

Nota: `node-red-contrib-ioplugin` non è più richiesto (Firmata rimosso).

### InfluxDB v1.8.10 (storage time-series)

**Porta**: 8086
**Database**: `highland`
**Retention**: 365 giorni (`standard_highland_retention`)
**Misure**: 32 (vedi `schema.md`)

Interfaccia di query:
```bash
# CLI (consigliato)
influx -database highland -execute 'SELECT last("value") FROM "local_temperature"'

# HTTP POST
curl -s -XPOST 'http://localhost:8086/query' --data-urlencode "db=highland" --data-urlencode "q=SELECT last(\"value\") FROM \"local_temperature\""
```

Nota: `curl -sG` (GET) restituisce risultati vuoti — usa POST o la CLI.

### Grafana v10.2.3 (visualizzazione)

**Porta**: 3000
**Credenziali di default**: admin/admin (da cambiare al primo login in produzione)

Quattro dashboard:

| Dashboard | UID | Scopo |
|-----------|-----|-------|
| Terrarium — Roraima | `terrarium-roraima` | Monitoraggio primario: T, UR, VPD, stato attuatori |
| Colombian Weather Reference | `colombian-weather-ref` | Meteo grezzo dalle 4 città |
| System Performance | `system-performance` | Diagnostica PID, PWM ventole, qualità del controllo |
| Night A/B Fan Experiment | `night-ab-test` | Confronto storico A/B (esperimento sospeso) |

### Arduino Watchdog v7

**Script**: `/usr/local/bin/arduino-watchdog.sh`
**Servizio**: `arduino-watchdog.service`
**Log**: `/var/log/arduino-watchdog.log`
**Intervallo di check**: 60 secondi

Health check a quattro passi:

1. Dispositivo USB `/dev/ttyACM0` esiste
2. Servizio Node-RED attivo in systemd
3. Node-RED ha la porta seriale aperta (`lsof`)
4. Heartbeat GPIO vivo (ultimo `arduino_status` in InfluxDB entro 3 minuti)

Strategia di recovery:

- **Problemi di processo NR** (passi 2–3): fino a 2 restart NR in 30 min, poi reboot
- **Heartbeat morto** (passo 4): reboot diretto (i restart NR non risolvono lo stallo seriale)
- **Cooldown reboot**: skip se l'uptime è < 10 min
- **Periodo di grazia GPIO**: 5 min dopo l'avvio NR prima di controllare l'heartbeat
- **Diagnostica**: snapshot loggato prima di ogni reboot (PID, FD, memoria, dmesg)

## Flusso dati

```
Sensore SHT35
    │
    ▼ (MQTT)
ESP8266 ──────────► Broker MQTT (:1883)
                          │
                          ▼
                    Node-RED
                     │    │    │    │
    ┌────────────────┘    │    │    └──────────────────┐
    ▼                     ▼    ▼                       ▼
Tab Humidity         Tab Temp  Tab Fans            Tab Weather
  │ calcolo VPD        │       │ PID controller      │ 4 città
  │ Target umidità     │       │ Door safety          │ Media
  │ Mister control     │       │ Mister interlock     │ Fallback
  │ Calcolo diff       │       │ Manual override      │
  └──────────┬─────────┘       │                      │
             │                 │                      │
             ▼                 ▼                      │
          Tab Fans ◄───────────────────────────────────┘
           │
    ┌──────┼──────┬──────┐
    ▼      ▼      ▼      ▼
 Pin 12  Pin 44  Pin 45  Pin 46    (seriale custom → Arduino)
 Circ.   Freezer Outlet  Impel.

         Tutti i tab
           │
           ▼
      Tab Utilities
        Data Logger + Serial Parser + Meross
           │
           ▼
      InfluxDB (:8086)
           │
           ▼
      Grafana (:3000)

    Reed switch porte (D22, D24)
           │
           ▼ (seriale da Arduino)
      Serial Parser → Door Controller → Door Safety
                                            │
                                    ┌───────┼───────┬──────────┐
                                    ▼       ▼       ▼          ▼
                               Ventole OFF Compr. Mister    Luci
                              (P12-P46)   OFF    OFF        60 %
```

## Servizi systemd

| Servizio | Scopo | Policy di restart |
|----------|-------|-------------------|
| `nodered` | Motore di controllo Node-RED | Always, gestito dal watchdog |
| `influxdb` | Database time-series | on-failure |
| `grafana-server` | Visualizzazione | on-failure |
| `mosquitto` | Broker MQTT | on-failure |
| `arduino-watchdog` | Monitor salute seriale Arduino | Always, RestartSec=10 |
