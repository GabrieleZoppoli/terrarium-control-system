---
title: "Documentazione tecnica"
description: "Architettura, schema dati, controllore PID e guide ai flussi"
showTableOfContents: true
---

Documentazione tecnica del sistema di controllo del terrario: architettura, schema dei dati, algoritmi di controllo e struttura dei flussi Node-RED.

## Indice

- **[Architettura](architecture/)**: panoramica del sistema, livelli hardware, protocolli di comunicazione
- **[Schema InfluxDB](schema/)**: tutte le 32 misure registrate dal sistema
- **[Controllore PID](pid-controller/)**: algoritmo PID con gain scheduling e controllo ventola a tre regimi
- **[Flussi Node-RED](flows/)**: guida all'import dei flussi e descrizione tab per tab
