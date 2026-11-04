---
title: "Terrario in diretta"
description: "Vista quasi in diretta dell'interfaccia di controllo Node-RED: uno snapshot ogni 15 minuti, più la striscia delle condizioni live sulla pagina del terrario."
weight: 5
layout: "live"
snapshotURL:      "https://rei1.tail7cc014.ts.net/highland/ui-latest.png"
liveURL:          "http://rei1.tail7cc014.ts.net:1880/ui/"
snapshotInterval: 60
---

Un Chromium headless sul Raspberry Pi cattura l'interfaccia di controllo Node-RED ogni 15 minuti e pubblica il PNG su un endpoint Tailscale Funnel. È quello che si vede qui sotto: abbastanza vicino al tempo reale per la maggior parte degli usi, senza esporre la dashboard vera e propria su Internet (l'interfaccia ha pulsanti che comandano prese Tapo; un'immagine è il livello di accesso giusto per chiunque non sia io).

Per uno sguardo più rapido a cosa succede nel terrario c'è la striscia delle condizioni live sulla [pagina del terrario](../): temperatura, umidità, VPD e stato del compressore, aggiornati ogni pochi secondi da un endpoint JSON in sola lettura sul Pi.

Dalla mia tailnet anche la dashboard *interattiva* è a un clic: il link `liveURL` la apre direttamente in Node-RED, dove setpoint e grafici sono modificabili. Altrimenti l'immagine qui sotto si aggiorna da sola.
