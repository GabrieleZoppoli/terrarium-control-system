---
title: "Dashboard live"
description: "Snapshot Grafana delle ultime 24 ore — temperatura, umidità, VPD, stato degli attuatori"
weight: 6
---

Un Chromium headless sul Pi renderizza la dashboard Grafana in PNG ogni 15 minuti — una versione ottimizzata per desktop, una per telefono — e la pubblica su un endpoint Tailscale Funnel. La dashboard vera e propria resta sulla tailnet; solo questi snapshot in sola lettura arrivano sull'Internet pubblica.

<picture>
  <source media="(max-width: 500px)"
          srcset="https://rei1.tail7cc014.ts.net/highland/grafana-latest-mobile.png">
  <img src="https://rei1.tail7cc014.ts.net/highland/grafana-latest-desktop.png"
       alt="Ultimo snapshot Grafana del terrario su 24 ore"
       loading="lazy"
       style="width:100%;max-width:1200px;height:auto;border-radius:8px;">
</picture>

<p style="font-size:0.85em;opacity:0.6;margin-top:0.5em;">
Aggiornata ogni 15 min · dati delle ultime 24 h · fuso orario Europa/Roma.
</p>

## Cosa mostrano i pannelli

- **Riga hero** — temperatura, umidità e VPD attuali, ciascuno con la sua sparkline su 24 ore.
- **Target vs misurato** — la linea viola è il valore misurato; la linea tratteggiata ambra è il setpoint d'alta quota colombiano (sfasato di 15 h per far coincidere l'alba genovese con quella del tepui equivalente); la linea verde è la stanza, come contesto.
- **Stato attuatori** — storico on/off delle luci, del compressore e del nebulizzatore come grafico ad area sulle ultime 24 h.
- **Footer** — temperatura della stanza, UR della stanza e assorbimento elettrico del sistema (Meross MSS310).
