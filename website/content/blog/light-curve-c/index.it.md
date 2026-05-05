---
title: "Curva di luce C: un coseno rialzato per la vetrina di nuvola"
date: 2026-05-04T23:30:00+02:00
description: "Un'umidità che risale nel pomeriggio di una giornata serena di maggio mi ha spinto a sostituire lo schedule a tre gradini delle LED (40-60-40) con una curva a coseno rialzato che picca al 70 % al mezzogiorno solare. Circa il 23 % di luce giornaliera in più, ridistribuita per tenere la vetrina più calda nella finestra critica del tardo pomeriggio. Esperimento di tre settimane; questo post sarà aggiornato il 2026-05-25 con il risultato."
tags: ["build-log", "highland-terrarium", "lighting", "control-loops", "experiment"]
showReadingTime: true
---

Oggi ho notato un lento risalire dell'umidità pomeridiana. Il target era al pavimento del 75 % (curva colombiana, limitata) e la vetrina lo seguiva bene per tutta la mattina e il mezzogiorno — poi, verso le 15:00, l'UR ha ricominciato a salire nonostante il PID tenesse le ventole outlet a PWM 255. La caccia al "cosa diavolo sta limitando le ventole?" è stata una pista falsa: niente le limitava. Le ventole erano al massimo. Il PID stava facendo tutto il possibile.

Il problema, in realtà, è **a monte delle ventole, nello schedule delle LED.**

## Cosa stava succedendo davvero

Tirando fuori i dati per quella finestra (13:00–17:00 CEST):

```
CEST    UR vetr%   T vetr°C   stanza Genova
14:30   79.82      21.95      22.96 / 56.7%
15:00   80.32      21.70      23.08 / 56.8%
15:30   81.49      21.44   ←  23.11 / 57.2%   vetrina si raffredda
16:00   81.77      21.43      23.17 / 57.4%
16:30   81.88      21.47      23.26 / 57.4%
```

La vetrina si è *raffreddata* di 0.5 °C tra le 14:30 e le 16:00, mentre la stanza continuava a scaldarsi. Calcolando la pressione di vapore reale (formula di Magnus), l'umidità assoluta era essenzialmente piatta — anzi, in lieve *diminuzione*. Le ventole stavano facendo il loro lavoro. **L'aumento di UR era un artefatto termodinamico della temperatura in calo** a contenuto d'acqua quasi costante.

La domanda diventa: perché la vetrina si è raffreddata mentre le luci erano ancora accese?

La risposta è nello schedule LED. Lo schedule attuale è una funzione a gradini:

- 0 → 40 % sulla rampa dell'alba (06:39 → 07:09)
- 40 % di plateau per tutta la mattina
- 40 → 60 % a "midday-up" (oggi: 11:44)
- 60 % di plateau attraverso il mezzogiorno solare (11:44 → 14:47)
- 60 → 40 % a "midday-down" (oggi: 14:47)
- 40 % di plateau attraverso il pomeriggio
- 40 → 0 % alla rampa del crepuscolo (19:21 → 19:51)

Ogni passo è una rampa lineare di 30 minuti; i plateau sono piatti. Il plateau al 60 % dura circa 3 ore centrate sul mezzogiorno solare. **Nel momento in cui scende a 40 %, l'apporto di calore dalle LED cala — e la vetrina inizia a raffreddarsi.** È esattamente quello che ho visto oggi alle 14:47, con l'UR che ha seguito 30–60 minuti dopo, mentre il calo di temperatura si traduceva attraverso Magnus.

## La luce di una foresta nuvolosa non è una funzione a gradini

La curva solare naturale all'equatore è essenzialmente un mezzo coseno: zero all'alba, picco al mezzogiorno solare, zero al tramonto, con angoli zenitali ripidi delle basse latitudini che producono un picco netto piuttosto che un plateau piatto. Le piante della vetrina sono specialiste delle foreste nuvolose d'alta quota — *Heliamphora* dei tepui, *Dracula* e *Masdevallia* delle Ande, *Dendrobium cuthbertsonii* delle alture della Nuova Guinea — habitat tra i 1500 e i 2500 m a basse latitudini. Nessuna di queste piante sperimenta un plateau piatto a mezzogiorno nel proprio ambiente luminoso naturale. Ricevono una curva solare che sale dolcemente nella mattina, picca alto sopra lo zenit e decade dolcemente nel pomeriggio.

Quindi sia *fisiologicamente* (curva morbida = naturale, plateau = artificiale) sia *ingegneristicamente* (plateau-poi-discesa crea il dirupo di UR che ho appena osservato), lo schedule a gradini è subottimale.

## Tre curve candidate

Ho valutato tre forme:

{{< figure src="curve-comparison.png" caption="Tre schedule slider candidati sul fotoperiodo di oggi (alba 07:09 — tramonto 19:21, durata del giorno 12,2 h). A è lo schedule a gradini attuale. B è un mezzo coseno puro che picca al 70 % al mezzogiorno solare, scendendo a 0 ai bordi. C è un 'coseno rialzato' con un pavimento al 35 % e un picco al 70 % a mezzogiorno — la forma morbida ma senza la mattina/sera buia di B." >}}

| Curva | Forma | Picco | Min | Dose giornaliera (slider·h) | Δ vs attuale |
|---|---|---|---|---|---|
| **A** | gradini | 60 | 40 | 569 | baseline |
| **B** | coseno puro | 70 | 0 | 544 | **−4,5 %** |
| **C₆₀** | coseno rialzato | 60 | 35 | 621 | +9 % |
| **C₆₅** | coseno rialzato | 65 | 35 | 660 | +16 % |
| **C₇₀** *(adottata)* | coseno rialzato | 70 | 35 | 699 | **+23 %** |

{{< figure src="delta-auc.png" caption="Dose giornaliera di luce (area sotto la curva slider) per ogni variante. La variante scelta — coseno rialzato con pavimento 35 %, picco 70 % — fornisce circa il 23 % in più di luce giornaliera totale rispetto allo schedule a gradini, ridistribuita in modo che la spalla del tardo pomeriggio resti molto più alta del plateau attuale al 40 %." >}}

Il +23 % può sembrare allarmante sulla carta, ma il flusso fotonico effettivo resta ben sotto l'irraggiamento di un mezzogiorno tropicale — i driver Mean Well della vetrina hanno un cap hardware al ~60 % della corrente nominale (vite di regolazione), quindi uno slider di 70 vale circa 70 % × 60 % = 42 % dell'output nominale dei LED. Le piante ricevono una dose generosa ma non estrema, e le specie in vetrina (Heliamphora in alto sotto il puck più luminoso, Dracula e Masdevallia nello strato basso ombreggiato) tollerano in natura quantità decisamente superiori.

Ho considerato seriamente B (coseno puro) perché è la forma più fedele fisicamente, ma la mattina buia era un problema: alle 09:00 sta a slider 32, *sotto* il plateau attuale di 40, e le piante in vetrina sono chiaramente più contente con almeno una baseline a 40. Quindi C — mantenere la baseline mattutina a 35 (leggermente *sotto* l'attuale, l'ho abbassata di proposito per contenere il cambiamento di AUC) e salire dolcemente fino a un picco di 70 a mezzogiorno — è il compromesso che meglio si adatta sia all'obiettivo ingegneristico sia all'analogia di foresta nuvolosa.

## Da dove parte la vetrina

Per dare contesto, ecco la baseline recente da 21 giorni di telemetria:

{{< figure src="temperature-3w.png" caption="Temperatura della vetrina vs target (curva colombiana, lat 4,98°N) per ora del giorno, media ± 95 % CI sulle ultime 3 settimane. La vetrina segue il target ragionevolmente bene durante la notte, sotto-rispetta nella mattina presto (si scalda più velocemente del target), e il plateau diurno si attesta intorno ai 21 °C — ben sotto il target diurno di 24 °C." >}}

{{< figure src="humidity-3w.png" caption="Umidità della vetrina vs target per ora del giorno, media ± 95 % CI sulle ultime 3 settimane. I limiti (pavimento 75 %, cap 95 %, entrambi impostati questa settimana) sono visibili come linee tratteggiate. La vetrina sta 5–8 % sopra il target per la maggior parte del giorno — la banda che la nuova curva di luce sta cercando di comprimere." >}}

{{< figure src="pwm-outlet-3w.png" caption="PWM ventola outlet (P45) per ora del giorno, media ± 95 % CI sulle ultime 3 settimane. Il blast mattutino (04:00–07:00 = MAX 255) è visibile, poi attività guidata dal PID per tutto il giorno con una media diurna chiara intorno a 80–120 PWM. Dopo le 20:00 il gate di lights-off forza l'outlet a 0." >}}

La banda interessante sul grafico dell'umidità è **15:00–18:00** — il picco supera leggermente la linea del 90 % proprio quando lo schedule a gradini delle LED è appena sceso da 60 a 40. Quello è precisamente l'artefatto che la nuova curva mira a correggere.

## Cosa ho implementato

Un singolo function node sulla tab Lights, attivato da un inject ogni 60 secondi (e una volta all'avvio NR). Legge `payload.photo_sunrise` e `payload.photo_sunset` dal Photoperiod Calculator, poi per il minuto corrente calcola:

```
slider(t) = max(35, 35 + 35 × cos(π × (t − solar_noon) / day_length))
```

…ed emette il valore PWM invertito (mappatura 255 → 0) al `pin8_writer_001` esistente, che gestisce l'output seriale e l'override door-safety. I due vecchi nodi `dynamic-dimmer` sono disabilitati (non cancellati — facile rollback). Gli eventi Tapo on/off ai bordi del fotoperiodo sono invariati: la presa intelligente continua a ciclare l'alimentazione ai driver LED su schedule giornaliero, la curva gestisce solo il segnale dim PWM *all'interno* di quella finestra di accensione.

L'intero cambiamento è una function nuova, un inject nuovo, due nodi disabilitati e un backup di `flows.json` per rollback. Nessuna nuova dipendenza, nessun cambio di schema, nessun lavoro su Grafana.

## Cosa mi aspetto di vedere

Se la diagnosi è corretta, tre cose dovrebbero cambiare nei prossimi 21 giorni di telemetria:

1. **La gobba di umidità delle 15:00–18:00 si comprime.** La vetrina dovrebbe restare più vicina al target durante la spalla pomeridiana.
2. **La temperatura della vetrina resta leggermente più alta nel tardo pomeriggio** (le LED stanno ancora alimentando calore oltre il vecchio momento di midday-down).
3. **Il PWM della ventola outlet aumenta leggermente durante le 14:00–17:00** perché il PID ha più carico termico da smaltire — ma è un prezzo che vale la pena pagare per evitare la deriva dell'UR.

Cose da tenere d'occhio che indicherebbero che il cambiamento è stato un errore:

- **Temperatura diurna della vetrina supera il target di 24 °C** più spesso. Con il +23 % di dose luminosa giornaliera, il freezer potrebbe dover lavorare di più, e nelle giornate più calde la vetrina potrebbe superare il target diurno. Se `target_temperature_computed` è regolarmente tenuto sotto la temperatura locale per >30 % della finestra diurna, il picco è troppo alto.
- **Le piante dello strato basso mostrano stress da luce** — sbiancamento sulle foglie di Dracula, arrotolamento delle foglie di Masdevallia. Lo strato basso d'ombra dovrebbe essere inalterato dal cambiamento dello slider (vivono sotto il ripiano in policarbonato), ma una sorveglianza è opportuna.
- **Le temperature dei driver salgono**. I quattro Logic Puck V3 hanno ciascuno dissipatori a perno da 140 mm con ventole 12 V; sono stati comodi al cap del 60 %. Uno slider di 70 li tiene entro il margine del cap ma gireranno un po' più caldi.

## Tra tre settimane: come apparirà questo post

Questo è un esperimento, non un cambiamento finito. **Il 2026-05-25 ri-eseguirò lo script di generazione grafici con tre settimane di telemetria post-curva** e aggiornerò questo post con:

- Gli stessi grafici di media-e-CI per ora del giorno, *post*-curva, affiancati alla baseline pre-curva qui sopra.
- Se la gobba UR delle 15:00–18:00 si è compressa.
- Se la temperatura diurna della vetrina è rimasta entro il target.
- Se è apparso qualcosa di brutto sulle piante.

Se la risposta è genericamente "sì, funziona", la curva resta. Altrimenti, abbasserò il picco (proverò C₆₅), aggiusterò il pavimento, o tornerò allo schedule a gradini con un plateau al 60 % più ampio.

I dati per quella decisione esistono già in InfluxDB; lo script vive in `~/terrarium-analysis/light_curve_charts.py` sul Pi. Lo scopo della struttura post-by-post è rendere l'esperimento leggibile — *ecco l'ipotesi, ecco i dati, ecco cosa mi aspetto, ecco cosa è successo davvero* — invece di lasciarlo sepolto nei messaggi di commit.

A tra tre settimane.

---

## Aggiornamento Day-1 — 2026-05-05

Un piccolo aggiornamento intermedio prima del followup del 2026-05-25, perché oggi è il primo giorno completo sotto la Curva C e nel frattempo sono atterrate alcune piccole correzioni utili.

{{< figure src="day1-overview.png" caption="Giorno 1 della Curva C: temperatura della vetrina, umidità e traiettoria dello slider per il 2026-05-05 a Genova. Lo slider sale dolcemente da 0 attraverso la rampa dell'alba alle 06:39, sale lungo la cosinusoide fino al picco ~70 al mezzogiorno solare (13:15), e scenderà simmetricamente nella rampa del tramonto alle 19:21. Gli eventi di nebulizzazione sono segnati come linee verdi verticali sul pannello dell'umidità." >}}

Cosa dicono i numeri di oggi (00:00 → 13:53 CEST):

- **Temperatura vetrina**: minima notturna 14,6 °C → picco 22,4 °C. Media 18,7 °C. Il riscaldamento mattutino è più ripido che con la vecchia funzione a gradini perché la cosinusoide cade meno bruscamente su un floor del 35 % (vs il vecchio plateau del 40 % che atterrava prima e restava piatto).
- **Umidità vetrina**: minima notturna 78 % → picco 96,6 %. Media 88,6 %. La vetrina è entrata nel giorno più secca del solito (il pomeriggio caldo precedente ha lasciato meno umidità tamponata), e il PID ha nebulizzato 20 volte per inseguire il target.
- **Traiettoria slider** (calcolata, dato che la global non è loggata): 0 alle 06:39 → 35 alle 07:09 → sale la cosinusoide → 70,0 alle 13:15 → 69,6 ora.

Alcuni piccoli miglioramenti applicati oggi, in ordine di impatto:

**Rampe morbide all'alba e al tramonto, ripristinate.** La Curva C originale aveva un gradino netto da 0 (Tapo off) a 35 (FLOOR) all'alba, e lo stesso al contrario al tramonto. Le piante d'altura e i driver Mean Well preferiscono entrambi essere accompagnati gradualmente. La funzione ora rampa linearmente 0 → 35 nei 30 min prima dell'alba, poi subentra la cosinusoide — e simmetricamente 35 → 0 nei 30 min dopo il tramonto. La transizione è continua: all'alba il valore della cosinusoide è esattamente 35 (dove cos(–π/2) = 0), così la rampa dell'alba si raccorda alla cosinusoide senza salti. Stesso al tramonto.

**Il dashboard segue la curva live.** Fino a oggi lo slider widget "Intensity of light" del dashboard era pilotato da una vecchia funzione di startup-brightness ancora basata sullo schedule a gradini 40-60-40, quindi la UI mostrava ad esempio 40 mentre il PWM sottostante era a 70. Il widget è ora cablato alla seconda uscita della funzione curva e si aggiorna ogni 60 secondi; anche il gauge AU lo segue.

**Watchdog del segnale dim LED.** Una modifica separata pushata ieri: un function node monitora il consumo totale (Meross MSS310 sullo stesso circuito dei driver LED e del freezer) e fa scattare il Tapo delle luci se rileva i driver LED che si comportano male (linea PWM dim flottante → driver vanno a uscita massima). Il modello è `expected = 32 W base + 2,8 × slider + (170 W se freezer on)`; trip a expected + 60 W. Calibrato empiricamente — lo stato di guasto ieri era 311 W ≈ 280 W cap LED + 30 W base, quindi il cap del trimmer fornisce ~70 % del nominale, non il 60 % che avevo inizialmente assunto. Falsa partenza stamattina a 167 W con le costanti vecchie; corretta.

### Tuning della nebulizzazione, derivato da 21 giorni di dati di eventi mist

La mancata catch-up della notte 04 → 05 ha fatto emergere un pattern cronico: la vetrina veniva nebulizzata ~17-22 volte per notte, ogni evento atterrando l'UR un po' **sopra** target, poi rilassamento, poi ri-trigger. Un classico loop di hunting. E ogni ciclo aggiungeva calore latente, rendendo il lavoro del freezer più difficile.

Ho estratto 21 giorni di timestamp `mist_event` e stratificato per stato simultaneo, calcolando ΔRH per evento = peak[+30…+180 s] − baseline[−60…0 s]:

{{< figure src="mist-delta-distribution.png" caption="Distribuzione del guadagno UR per evento sugli ultimi 21 giorni, per strato. Eventi notturni con vetrina sigillata (ventole outlet+impeller spente via lights-off-fan-gate) si raggruppano intorno a +2 % per evento. Eventi diurni con il PID che scambia aria con la stanza si raggruppano intorno a +3-4 % per evento perché la stanza è significativamente più secca della vetrina (~50 % UR vs ~90 %), così ogni millilitro di mist passa più facilmente attraverso il sigillo." >}}

| strato | n | stato stanza | media Δ | meccanismo |
|---|---:|---|---:|---|
| Notte, freezer-ON, outlet+impeller off | 96 | T 22 °C, UR 60 % | **+2,1 %** | vetrina sigillata — il vapore resta ma combatte la condensazione sull'evaporatore |
| Giorno, freezer-OFF, slider ≈ 40, ventole on | ~10 | T 23 °C, UR 47 % | +4,0 % | mixing con stanza più secca — vapore sostituisce facilmente l'aria persa |
| Giorno, freezer-OFF, slider ≈ 60, ventole on | 17 | T 22 °C, UR 49 % | +3,1 % | stesso regime di mixing, più attività ventole guidate dai LED |

Due regimi, due meccanismi, due guadagni per evento diversi. Trattare entrambi con una singola regola fissa garantisce overshoot in almeno uno dei due. La regola pre-tuning sparava ogni volta che la vetrina era 1 % sotto target ed eseguiva un mist da 20 s indipendentemente dal regime — ma 20 s di atomizzazione sono +2 % di notte, +3-4 % di giorno, quindi la vetrina atterrava *sempre* sopra target a ogni evento e ri-triggerava poco dopo.

Quindi da oggi il trigger automatico nebulizzazione è regime-aware, gated su `wbt_shutdown_active` (la finestra lights-off / vetrina sigillata):

```
wbt_shutdown_active == 1 (notte, sigillata):  spara a  Δ ≥ 2,  mist on-time 20 s
wbt_shutdown_active == 0 (giorno, mixing):    spara a  Δ ≥ 1,  mist on-time 10 s
```

La soglia ora corrisponde al guadagno in entrambi i regimi. Di notte la vetrina deriva di ~2 % tra eventi, il trigger spara, e il mist da +2 % atterra l'UR proprio sul target — niente overshoot, niente ri-trigger immediato. Il giorno mantiene la stessa frequenza di trigger ma dimezza l'iniezione di acqua + calore latente per evento, dato che ogni evento diurno stava comunque facendo overshoot di 2-3 %.

Una nota metodologica che devo ai dati: il mio primo istinto era "aggiustare via regressione" gli strati diurni a uno stato comune della stanza e concludere che il guadagno per evento fosse segretamente lo stesso (~+2,3 %) in tutti e tre i regimi. Avrebbe giustificato una regola unica. Ma aggiustare B e C a una stanza al 58 % UR in cui non operano mai (vivono al 47-49 %) è estrapolazione, non interpretazione — la fisica sotto è davvero diversa tra regime sigillato e regime di mixing. Il numero onesto è la media grezza per strato nelle sue stesse condizioni di stanza, e quelle sono diverse. Da qui due regole.

Effetto atteso su una notte di cooling-fight: metà degli eventi × kJ latenti simili per evento ≈ ~13 W in meno di iniezione di calore medio durante le 9 ore più dure del freezer. Non abbastanza da solo per compensare la ventola P44 morta che ha innescato l'undershoot della notte 04→05, ma è un miglioramento gratuito che toglie uno dei due carichi sovrapposti al freezer.

### Cosa sto guardando ora

- La gobba UR delle 15:00–18:00 che ha innescato la Curva C in primis — le prossime tre settimane mostreranno se la spalla pomeridiana liscia chiuderà quel gap.
- Se il picco di temperatura diurna della vetrina sale sopra target. Oggi ha toccato 22,4 °C verso mezzogiorno — ben entro il target di 24 °C — ma con una ventola evaporatore in meno e Genova che si scalda stagionalmente, questa è la metrica system-side da tenere d'occhio.
- Lato piante: non mi aspetto di vedere niente su scala di 1 giorno, ma al followup del 2026-05-25 ispezionerò lo strato superiore (Heliamphora, Nepenthes d'altura) per eventuali sfumature da fotoinibizione o aborti di pitcher, e le orchidee dello strato basso per eventuali bruciature delle punte.

L'assessment completo post-curva per ora-del-giorno parte come previsto il 2026-05-25.
