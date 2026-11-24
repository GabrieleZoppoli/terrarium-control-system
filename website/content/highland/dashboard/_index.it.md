---
title: "Dashboard live"
description: "Le ultime 24 ore nel terrario: temperatura, umidità, VPD, consumo, compressore e nebulizzatore"
weight: 6
---

Un piccolo script sul Pi ridisegna questi grafici ogni minuto direttamente dal database dei sensori (InfluxDB) e li pubblica su un endpoint Tailscale Funnel, in una versione per desktop e una per telefono. Il sistema di controllo resta privato; solo queste immagini in sola lettura arrivano sull'Internet pubblica.

<picture>
  <source media="(max-width: 600px)" srcset="https://rei1.tail7cc014.ts.net/highland/dashboard-mobile.png">
  <img src="https://rei1.tail7cc014.ts.net/highland/dashboard-desktop.png" data-refresh="60"
       onerror="this.onerror=null;this.src='https://rei1.tail7cc014.ts.net/highland/grafana-latest-desktop.png'"
       alt="Le ultime 24 ore nel terrario d'alta quota" loading="eager"
       style="width:100%;max-width:1400px;height:auto;border-radius:8px;">
</picture>
<script>
setInterval(function () {
  if (document.visibilityState !== 'visible') return;
  var pic = document.querySelector('picture img[data-refresh]');
  if (!pic) return;
  var t = '?t=' + Date.now();
  var src = pic.parentNode.querySelector('source');
  if (src) src.srcset = 'https://rei1.tail7cc014.ts.net/highland/dashboard-mobile.png' + t;
  pic.src = 'https://rei1.tail7cc014.ts.net/highland/dashboard-desktop.png' + t;
}, 60000);
</script>

<p style="font-size:0.85em;opacity:0.6;margin-top:0.5em;">
Ridisegnata ogni minuto · ultime 24 h · fuso orario Europa/Roma · la notte (luci spente) è ombreggiata
</p>

## Cosa mostrano i grafici

- **Riga in alto**: la stanza attorno al terrario (temperatura e UR), il livello della tanica e l'assorbimento elettrico del sistema in questo momento.
- **Temperatura e umidità**: la linea colorata è il terrario; la tratteggiata è il setpoint d'alta quota colombiano (sfasato di 15 h perché l'alba genovese coincida con quella del tepui); la linea grigia è la stanza, come contesto. La notte è ombreggiata, così il raffreddamento notturno e l'aumento dell'umidità si vedono subito.
- **VPD**: il deficit di pressione di vapore, quanto l'aria sottrae acqua alle foglie. Basso è ciò che vogliono le piante di foresta nebulosa.
- **Consumo**: l'assorbimento dell'intero sistema (Meross MSS310); il plateau notturno è il compressore.
- **Compressore e nebulizzatore**: strisce acceso/spento sulla stessa linea temporale.
