---
title: "Guida ai flussi Node-RED"
description: "Importazione dei flussi e descrizione tab per tab"
---


## Panoramica

`flows-sanitized.json` contiene l'intera logica di controllo Node-RED del terrario, distribuita su 7 tab. Le credenziali sono sostituite da placeholder.

## Prima dell'importazione

### 1. Installa Node-RED

```bash
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)
sudo systemctl enable nodered
sudo systemctl start nodered
```

### 2. Installa i pacchetti nodi richiesti

Tutti i pacchetti vanno installati nella directory utente di Node-RED (`~/.node-red/`):

```bash
cd ~/.node-red

npm install \
  node-red-contrib-bigtimer \
  node-red-node-openweathermap \
  node-red-contrib-influxdb \
  node-red-node-smooth \
  node-red-contrib-python-function-ps \
  node-red-contrib-dynamic-dimmer \
  node-red-contrib-sun-position \
  node-red-node-rbe \
  node-red-contrib-stoptimer-varidelay \
  node-red-contrib-aggregator \
  node-red-contrib-hysteresis \
  node-red-contrib-ui-led \
  node-red-contrib-ui-statetrail \
  node-red-dashboard \
  node-red-node-serialport
```

Nota: `node-red-contrib-ioplugin` non serve più (il protocollo Firmata è stato rimpiazzato da seriale custom).

### 3. Installa le dipendenze Python

Il controllo delle smart plug Tapo usa function node Python, e il daemon di monitoraggio Meross richiede la libreria `meross-iot`:

```bash
pip3 install PyP100 meross-iot paho-mqtt
```

### 4. Installa i servizi esterni

- **InfluxDB 1.8.x**: database time-series per il logging
- **Broker MQTT** (es. Mosquitto): per l'ingestion dei dati sensore
- **Grafana 10.x** (opzionale): per le dashboard

```bash
sudo apt install influxdb mosquitto
influx -execute "CREATE DATABASE highland"
influx -execute "CREATE RETENTION POLICY standard_highland_retention ON highland DURATION 365d REPLICATION 1 DEFAULT"
```

## Importazione dei flussi

1. Apri Node-RED nel browser: `http://<ip-del-tuo-pi>:1880`
2. Click sul menu a hamburger (☰) → **Import**
3. Seleziona il tab **Clipboard**
4. Click su **select a file to import** e scegli `flows-sanitized.json`
5. Seleziona **Import to: new flow** (consigliato) o **current flow**
6. Click su **Import**
7. Click su **Deploy** per attivare

## Configurazione post-import

### Credenziali (OBBLIGATORIO)

Tre function node Python contengono i placeholder `YOUR_EMAIL` e `YOUR_PASSWORD`. Devono essere sostituiti con le credenziali del tuo account TP-Link Tapo:

1. Tab **Lights** → Python function node (controlla la presa delle luci)
2. Tab **Humidity** → Python function node (controlla la presa del nebulizzatore)
3. Tab **Temperature** → Python function node (controlla la presa del compressore)

Doppio click su ogni nodo, trova le variabili `email` e `password` e sostituisci i placeholder. Aggiorna anche la variabile `ip` con l'indirizzo IP della tua presa Tapo.

### Porta seriale

Il nodo della porta seriale è configurato per `/dev/ttyACM0` a 115200 baud con delimitatore newline. Carica lo sketch `arduino-terrarium.ino` sul tuo Arduino Mega con `arduino-cli`:

```bash
arduino-cli compile --fqbn arduino:avr:mega ~/arduino-terrarium/
arduino-cli upload --fqbn arduino:avr:mega -p /dev/ttyACM0 ~/arduino-terrarium/
```

### Connessione InfluxDB

Il nodo server InfluxDB punta a `localhost:8086`, database `highland`. Se il tuo InfluxDB è su un altro host o con un nome di database diverso, aggiorna il nodo di configurazione InfluxDB (visibile nella sidebar di config).

### Broker MQTT

Il nodo broker MQTT punta a `localhost:1883`. Aggiornalo se il tuo broker è altrove. Verifica anche che il topic MQTT coincida con quello che pubblica il tuo ESP.

### API OpenWeatherMap

I nodi meteo richiedono una API key gratuita di OpenWeatherMap. Doppio click su un nodo OpenWeatherMap e inserisci la chiave nella configurazione.

### Configurazione della posizione

Il nodo `position-config` usa:

- Latitudine: 5.19485 (tepui venezuelano come riferimento per i calcoli astronomici)
- Longitudine: 8.944381 (Genova, Italia, per alba/tramonto locali)

Modifica la longitudine se i tempi astronomici devono riflettere la tua posizione.

### Monitoraggio Meross (opzionale)

Il monitoraggio dell'assorbimento elettrico usa un daemon persistente (`meross_daemon.py`) che mantiene una singola sessione sull'API cloud Meross e pubblica letture su MQTT ogni 2 secondi. Molto più efficiente dell'approccio precedente (un processo Python ogni 120 s con login/logout completo).

**Setup:**

1. Modifica `scripts/meross_daemon.py` e imposta le credenziali:
   - `EMAIL`: email del tuo account Meross
   - `PASSWORD`: password del tuo account Meross
   - `PLUG_NAME`: nome della presa nell'app Meross

2. Installa e avvia il servizio systemd:
   ```bash
   sudo cp systemd/meross-daemon.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now meross-daemon
   ```

3. Verifica che stia pubblicando:
   ```bash
   mosquitto_sub -t meross/power/watts -C 3
   ```

Node-RED si abbona a `meross/power/watts` tramite un nodo MQTT-in sul tab Utilities. Il daemon accetta anche comandi `on`/`off` su `meross/power/command`. Se non hai una presa Meross, disabilita il nodo MQTT-in (`meross_mqtt_in_001`) sul tab Utilities.

## Descrizione dei tab di flusso

### Tab 1: Lights
Gestisce il fotoperiodo e il dimming dei LED con rampe alba/tramonto e variazione di intensità a metà giornata.

**Nodi chiave**:

- **BigTimer**: schedule fissa 06:25–20:05 (tempi in minuti-dalla-mezzanotte: starttime=385, endtime=1205)
- **Dynamic Dimmer #1**: rampa alba/tramonto (slider 0↔40, 40 step × 45 s = 30 min)
- **Dynamic Dimmer #2**: rampa di mezzogiorno (slider 40↔60, 20 step × 90 s = 30 min)
- **Function node**: Dawn/Dusk/Midday con `start=0`/`start=1` forzano la direzione della rampa
- **Startup brightness**: rileva riavvii a metà rampa ed emette uno "start parziale" per completare la rampa in orario
- **Writer Pin 8**: invia `P8,<valore>` via seriale; door-safety gated (forza PWM 102 con porte aperte)
- **Python function**: controllo presa Tapo P100 con door-safety gate

**Flusso**: BigTimer accende/spegne → la presa Tapo alimenta i LED → il dimmer fa la rampa PWM per alba/mezzogiorno/tramonto

### Tab 2: Humidity
Ingesta i dati dei sensori, calcola il VPD, gestisce il nebulizzatore.

**Nodi chiave**:

- **MQTT In**: riceve temperatura + umidità SHT35 dall'ESP
- **VPD Calculator** (function): calcola il Vapor Pressure Deficit con la formula di Magnus
- **Target humidity**: derivato dai dati meteo colombiani (cap massimo 95 % UR)
- **Humidity difference**: target − misurata, alimenta il PID del tab Fans
- **Hysteresis**: controlla on/off del nebulizzatore attorno al target
- **Python function**: controllo presa Tapo P100 per il nebulizzatore (con door-safety gate)
- **Mist counter**: conta gli eventi giornalieri con persistenza fra riavvii

### Tab 3: Temperature
Gestisce il raffreddamento a compressore.

**Nodi chiave**:

- **Target temperature**: derivata dai dati meteo colombiani (limitata 12–24 °C)
- **Temperature difference**: target − misurata
- **Hysteresis**: on/off del compressore in base all'errore
- **Python function**: controllo presa Tapo P100 per il compressore (con door-safety gate)

### Tab 4: Fans
Cuore del sistema: PID, door safety, gestione ventole.

**Nodi chiave**:

- **PID Controller** (function): ventola basata su umidità con gain scheduling (Kp=50, Ki=0,5, Kd=10)
- **Day/Night Check**: within-time-switch 04:00–00:00 (mezzanotte)
- **Night Mode (A/B sospeso)**: sempre output 0. Il codice A/B è preservato nei commenti con istruzioni per la riattivazione
- **Mister Interlock** (function): ferma tutte le ventole quando il nebulizzatore è attivo (cancella il topic per evitare conflitti RBE)
- **Manual Override**: slider Dashboard, bypassa tutto il controllo automatico
- **Fan writers**: 4 nodi seriale — outlet (P45), impeller (P46), freezer (P44), circulation (P12), tutti con door-safety gate
- **RBE nodes**: logging report-by-exception per i cambi di PWM
- **Door controller**: fa OR delle due porte con debounce di 3 secondi
- **Door safety**: 4 uscite — ventole off, gate compressore, gate mister, luci al 60 %
- **Tapo gates**: bloccano comandi Tapo inappropriati durante la door safety (compressore on, mister on, luci off)
- **High-humidity safety**: forza la ventola outlet a 40 PWM quando umidità > 90 % e le ventole sono a 0

### Tab 5: Weather
Recupera e processa i dati meteo colombiani d'alta quota.

**Nodi chiave**:

- **OpenWeatherMap** (×4): Chinchiná, Medellín, Bogotá, Sonsón
- **Aggregator/Smooth**: finestra InfluxDB 30 min + media mobile 15 min (count=60 fra le 4 città)
- **Position config**: calcoli astronomici per alba/tramonto di riferimento
- **Weather fallback**: curva giornaliera storica 14-giorni (288 slot, smoothed a due passaggi) sostituisce i default piatti; fallback ultimo (giorno T=24/UR=85, notte T=14/UR=90) se non ci sono dati storici disponibili
- **Historical curve builder**: interroga i dati InfluxDB delle 4 città ogni 6 ore, costruisce un profilo diurno smussato con shift temporale di 15 ore

Lo shift di 15 ore fra Colombia (UTC−5) e Italia (UTC+1) fa coincidere il giorno colombiano con la notte italiana, producendo la variazione giornaliera naturale.

### Tab 6: Charts
UI Dashboard Node-RED per il monitoraggio locale.

**Nodi chiave**:

- **Gauges**: temperatura, umidità, VPD
- **Charts**: serie temporali con 3 serie ciascuno — misurata (blu), target (rossa), stanza (verde)
- **LED**: indicatori di stato per gli attuatori
- **State trails**: storico on/off
- **Room data inject**: repeat 60 s, spinge i dati del sensore stanza sui grafici
- **Chart persistence**: salva/ripristina via flow context per sopravvivere ai riavvii

Accesso a: `http://<ip-del-tuo-pi>:1880/ui`

### Tab 7: Utilities
Logging dei dati, comunicazione seriale, monitoraggio elettrico, diagnostica di sistema.

**Nodi chiave**:

- **Serial config**: 115200 baud, newline delimiter, `/dev/ttyACM0`
- **Serial parser**: inoltra i dati seriali in arrivo — heartbeat (→ arduino_status), porte (→ door controller)
- **Data Logger** (function): 14 uscite, legge il global context ogni 60 secondi
- **InfluxDB out** (×14+): una per misura, scrivendo sul database `highland`
- **Monitoraggio Meross**: sottoscrizione MQTT (`meross/power/watts`) dal daemon persistente → parsing → UI text + InfluxDB (aggiornamenti ogni 2 s)
- **Mist counter persistence**: startup inject → restore function → UI text node
- **Resend PWM**: re-invio periodico degli stati ventola attuali per evitare seriale stantio
- **Send to All Fans**: nodo a 4 uscite manuali per debugging (outlet, impeller, freezer, circulation)

## Troubleshooting

**I nodi mostrano "missing type"**: installa il pacchetto npm richiesto per quel tipo di nodo (vedi sezione installazione).

**Errori di scrittura InfluxDB**: verifica che InfluxDB sia in esecuzione (`systemctl status influxdb`) e che il database `highland` esista.

**Arduino non si connette**: controlla che `/dev/ttyACM0` esista, che lo sketch `arduino-terrarium.ino` sia stato caricato e che nessun altro processo stia occupando la porta seriale. Non aprire mai `/dev/ttyACM0` manualmente mentre Node-RED è in esecuzione.

**I nodi meteo danno errore**: verifica che l'API key di OpenWeatherMap sia configurata e che il piano gratuito non sia stato rate-limited.

**Il controllo delle prese Tapo fallisce**: verifica che `PyP100` sia installato, che le credenziali siano corrette e che gli IP delle prese siano raggiungibili dal Pi.

**La door safety non si disattiva**: controlla entrambi i reed switch — `door_safety_active` resta true finché sia D22 sia D24 leggono HIGH (porte chiuse). Il debounce richiede che le porte restino chiuse stabilmente.

**Ventole bloccate a 0 dopo nebulizzazione**: era un bug noto del topic RBE, ora risolto. Assicurati che la function "Stop All Fans" *cancelli* `msg.topic` invece di impostarlo a `"mister_override"`.
