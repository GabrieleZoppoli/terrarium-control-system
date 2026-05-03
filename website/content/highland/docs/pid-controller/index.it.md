---
title: "Controllore PID"
description: "Algoritmo PID con gain scheduling e controllo ventola a tre regimi"
---


## Panoramica

Il terrario usa un controllore PID discreto (Proporzionale-Integrativo-Derivativo) con gain scheduling per modulare la velocità della ventola in base alla differenza fra umidità target e misurata. È una risposta fluida rispetto al semplice on/off (bang-bang), e il gain scheduling previene l'oscillazione attorno al setpoint.

## Convenzione sull'errore

```
humidity_diff = target_humidity − current_humidity    (dal tab Humidity)
error = −humidity_diff = current_humidity − target_humidity
```

- **Errore positivo** (misurata > target = troppo umido) → ventola più veloce
- **Errore negativo** (misurata < target = troppo secco) → ventola più lenta (ci pensa il nebulizzatore)

## Equazione PID

L'output a ogni passo temporale:

```
u(t) = g × Kp × e(t)  +  Ki × ∫₀ᵗ e(τ)dτ  +  g × Kd × de/dt
```

dove *g* è il fattore di guadagno dal gain scheduling (vedi sotto).

In forma discreta (calcolato a ogni ciclo di controllo, tipicamente ~10–15 secondi):

```
P = g × Kp × error
I = Ki × integral_accumulator
D = g × Kd × filtered_derivative

fan_speed = BASE_SPEED + P + I + D
```

## Parametri di tuning

| Parametro | Valore | Effetto |
|-----------|--------|---------|
| **Kp** | 50 | Guadagno proporzionale — risposta primaria alla deviazione |
| **Ki** | 0,5 | Guadagno integrale — corregge l'offset di stato stazionario nel tempo |
| **Kd** | 10 | Guadagno derivativo — smorza le oscillazioni, reagisce al tasso di variazione |
| **BASE_SPEED** | 50 | Velocità di riposo con errore zero (~20 % duty cycle) |
| **MIN_SPEED** | 40 | PWM minimo ventola (~16 %) — mantiene circolazione costante |
| **MAX_SPEED** | 255 | Tetto uniforme — fino al 2026-04-30 era variabile per fascia oraria (180/230/255), ora rimosso |

Questi guadagni sono memorizzati nel flow context (persistono fra restart di Node-RED) e modificabili a runtime dal text input della Dashboard Node-RED (formato: `Kp,Ki,Kd`).

## Gain scheduling

Con Kp=50 fisso, il controllore oscillava rapidamente di ±25 PWM quando l'umidità restava entro ±0,5 % dal setpoint. Il solo termine proporzionale produceva oscillazioni abbastanza grandi da sovrascorrere in direzioni alternate.

La funzione di gain scheduling scala Kp e Kd effettivi in base all'entità dell'errore:

```
|error| ≤ 1,5 %:  gainFactor = 0,15    (Kp effettivo = 7,5)
|error| ≥ 4,0 %:  gainFactor = 1,0     (Kp effettivo = 50)
fra i due:         gainFactor = 0,15 + (|error| − 1,5) × (0,85 / 2,5)
                              = interpolazione lineare
```

Questo produce:

- **Controllo dolce vicino al target** (g=0,15): aggiustamenti piccoli e morbidi quando l'umidità è entro l'1,5 % dal setpoint
- **Risposta aggressiva a grandi deviazioni** (g=1,0): piena autorità PID quando l'umidità è oltre il 4 % dal target
- **Transizione fluida**: l'interpolazione lineare evita salti discontinui dell'azione di controllo

Il termine integrale (Ki) NON è scalato dal gain factor — così l'integrale continua ad accumulare normalmente e corregge l'offset di stato stazionario a prescindere dall'errore corrente.

Lo stato del nodo mostra il gain factor attuale come `g:0.15` … `g:1.00` per il monitoraggio in tempo reale.

## Protezione anti-windup

Il windup integrale avviene quando errori grandi e prolungati fanno accumulare il termine integrale a valori estremi, provocando un grosso overshoot al momento dell'inversione. Due meccanismi lo prevengono:

### 1. Clamping dell'integrale

```
I_MAX = 120 / Ki     (= 240 con Ki=0,5)

integral = clamp(integral, −I_MAX, +I_MAX)
```

Il contributo dell'integrale è quindi limitato a ±120 unità PWM.

### 2. Decadimento vicino al target

Quando |errore| < 2,0 % UR, l'integrale decade del 5 % al secondo:

```
if |error| < 2.0:
    integral *= (1 − 0.05 × dt)
```

Impedisce all'integrale di spostare lentamente la ventola dall'ottimale quando le condizioni sono stabili. Il tasso del 5 %/s (aumentato rispetto al 2 %/s precedente) garantisce un rientro più rapido dopo un picco di umidità.

## Filtraggio derivativo

Le derivate grezze amplificano il rumore del sensore. Un filtro passa-basso esponenziale del primo ordine liscia il termine derivativo:

```
α = 0,12    (fattore di smoothing: 0=filtro pesante, 1=nessun filtro)

filtered_derivative = α × raw_derivative + (1−α) × previous_filtered_derivative

dove:
    raw_derivative = (error − previous_error) / dt
```

Il valore α = 0,12 offre una riduzione pesante del rumore (più aggressiva del 0,25 precedente) pur mantenendo la reattività a vere variazioni rapide (nebulizzazione, apertura porta).

## Rate limiting

Per evitare transizioni brusche che disturberebbero l'ambiente del terrario:

```
max_change = min(20, max(10, |error| × 3))

if |fan_speed − previous_speed| > max_change:
    fan_speed = previous_speed + sign(delta) × max_change
```

La variazione massima è limitata a 20 PWM per ciclo, anche per proteggere il link seriale dal flooding di comandi. Permette transizioni rapide durante grandi disturbi mantenendo fluidità vicino al setpoint.

## Mappatura dell'output

```
raw_output = BASE_SPEED + P + I + D
fan_speed  = clamp(round(raw_output), MIN_SPEED, MAX_SPEED)
           = clamp(round(raw_output), 40, 255)
```

`MAX_SPEED` è uniforme a 255 (dal 2026-04-30 — i precedenti cap orari per ore di silenzio a 180/230 sono stati rimossi perché non cambiavano in modo significativo la dinamica dell'umidità). Anche l'esperimento A/B mattutino che forzava la velocità ventola a 75 o 255 in base alla parità del giorno dell'anno è stato rimosso (2026-05-03) dopo 13 giorni di dati che mostravano un effetto del trattamento entro il rumore (≤0,5 %, p>0,9).

La velocità ventola è applicata contemporaneamente alla ventola outlet (pin 45) e alla ventola impeller (pin 46) tramite comandi seriali (`P45,<valore>` e `P46,<valore>`). La ventola evaporatore (pin 44) e quella di circolazione (pin 12) operano indipendentemente con controllo a isteresi basato sul compressore.

## Condizioni di guardia

L'output del PID è bloccato (restituisce null) quando:

1. **Door safety attiva** — tutte le ventole sono forzate a 0 dal controllore di sicurezza porta
2. **Modalità manuale attiva** — l'operatore ha fissato la velocità dalla Dashboard
3. **Nebulizzatore ON** — interblocco di sicurezza, ventole ferme durante la nebulizzazione
4. **Modalità notturna** — ventole off da mezzanotte alle 04:00 (PID attivo 04:00–00:00)
5. **Nessun dato** — la differenza di umidità è indefinita (sensore offline)
6. **Gap temporale** — dt > 120 s (restart di NR, evita picchi integrali da timestamp stantii)

## Gerarchia di controllo

```
Priorità 0 (massima): Door safety        → tutte le ventole a 0 PWM
Priorità 1:           Override manuale    → velocità fissa utente
Priorità 2:           Interlock mister    → tutte le ventole a 0 PWM
Priorità 3:           Modalità notturna   → ventole off (mezzanotte → 04:00)
Priorità 4 (minima):  PID automatico      → velocità calcolata
```

Nota: l'esperimento A/B notturno è sospeso — Night Mode produce sempre 0 fra mezzanotte e le 04:00. Il codice A/B è preservato nel function node come blocco commentato con le istruzioni per riattivarlo.

## Comportamento tipico

| Condizione | Errore | g | P | I (tipico) | D | Output | Fan Speed |
|-----------|--------|---|---|------------|---|--------|-----------|
| Sul setpoint | 0 | 0,15 | 0 | ~0 | 0 | 50 | 50 (~20 %) |
| Leggermente umido (+1 % UR) | +1 | 0,15 | +7,5 | ~+3 | ~0 | 60 | 60 (~24 %) |
| Umido moderato (+3 % UR) | +3 | 0,76 | +114 | ~+10 | ~+5 | 179 | 179 (~70 %) |
| Molto umido (+5 % UR) | +5 | 1,0 | +250 | ~+15 | ~+8 | 255 | 255 (MAX) |
| Leggermente secco (−1 % UR) | −1 | 0,15 | −7,5 | ~−3 | ~0 | 40 | 40 (MIN) |
| Salita rapida di umidità | +3, in salita | 0,76 | +114 | ~+8 | +16 | 188 | 188 (~74 %) |

## Monitoraggio

Il controllore PID pubblica lo stato sulla Dashboard Node-RED e imposta lo stato visivo del nodo:

```
Indicatore direzione: ▲ (ventola in aumento), ▼ (in diminuzione), ● (stabile)
Colore: verde (|diff| < 2 %), giallo (|diff| < 5 %), rosso (|diff| ≥ 5 %)
Testo: "▲ Δ3.2% → 55% [P:48 I:12 D:5] g:0.76"
```

Tutte le componenti PID (P, I, D, output totale, integrale accumulato, gain factor) sono visibili sulla Dashboard per diagnostica in tempo reale.
