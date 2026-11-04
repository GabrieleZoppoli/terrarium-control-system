---
title: "Ripiani nebulizzati"
description: "Ripiani di vetro in soggiorno: nebulizzatori a ultrasuoni su loop a isteresi UR (~80 %) gestito da un secondo Raspberry Pi via Tapo P100, sensori BME280 + SHT35"
---

Non tutte le piante hanno bisogno di un terrario climatizzato da 1,5 m. Diverse specie della collezione vivono su una serie di ripiani di vetro in soggiorno. Ogni ripiano ha un nebulizzatore a ultrasuoni con serbatoio, collegato a una presa smart Tapo P100; un secondo Raspberry Pi legge un Bosch BME280 e un SHT35 sul ripiano e commuta la presa su un loop a isteresi intorno all'80 % UR. Niente compressore, niente PID, niente registrazione dati.

La stanza fa la temperatura da sola (18–24 °C tutto l'anno, clima mediterraneo genovese), la luce diurna più una semplice striscia LED full-spectrum fa il fotoperiodo.

Qui vivono le piante che stanno bene in un soggiorno genovese una volta aggiunto il vapore acqueo e lasciata stare la temperatura.

## Chi c'è sui ripiani

La composizione cambia. Le piante che crescono troppo per il loro posto o che chiedono notti più fresche passano nel terrario d'alta quota; le nuove arrivate che non hanno bisogno delle temperature da foresta nebulosa partono da qui e ci restano se stanno bene.

| Residente | Provenienza | Perché qui e non nel terrario |
|---|---|---|
| *Vanda coerulescens* | Celandroni Orchidee | Vandacea warm-intermediate; tollera le temperature della stanza. |
| *Neostylis* Lou Sneary (*N. falcata* × *Rhynchostylis coelestis* var. *coerulea*) | Celandroni Orchidee | L'ibrido eredita la tolleranza al caldo di *Rhynchostylis*. |
| *Darwinara* Charm 'Blue Moon' (*Neofinetia × Vanda × Rhynchostylis × Ascocentrum*) | Claessen Orchids & Plants | Fiori blu-violetti; la pigmentazione blu dipende in particolare da *notti* più fresche, che il microclima a nebbia fornisce senza dover raffreddare davvero. |
| *Pinguicula* messicane (*agnata*, *ehlersiae*, *esseriana*, *gypsicola* × *moctezumae*, *rotundiflora*, *rectifolia*, *Marciano*, *Apasionada*, *Red Starfish*, ecc.) | Un Angolo di Deserto · Giardino Carnivoro | Le ping messicane vogliono luce forte + radici asciutte + alta umidità in stagione piovosa; la nebbia dà umidità senza bagnare. |
| *Cephalotus follicularis* + f. 'Hummer's Giant' | Giardino Carnivoro · David Maccioni | Odia la minima notturna del terrario d'alta quota (13 °C) e l'aria ferma; preferisce un posto più asciutto, più luminoso e più ventilato. |
| *Phalaenopsis* botaniche (*finleyi*, *lowii*, *gibbosa*, *wilsonii*, *parishii*) | Celandroni Orchidee | *Phalaenopsis* botaniche warm-growing, di taglia miniatura. Stanno meglio in condizioni intermedie che nella foresta nebulosa. |
| *Angraecum didieri* | Growlist | Miniatura malgascia; intermediate-warm, non tollera la caduta notturna del terrario d'alta quota. |
| *Bulbophyllum makoyanum* | Regalo | Da quote basse-intermedie del Sud-est asiatico; il terrario è troppo fresco di notte per lui. |

## L'hardware

- **Nebulizzatore a ultrasuoni**: disco piezoelettrico generico a 24 V con serbatoio ricaricabile, comandato da una presa smart Tapo P100. Il disco si sostituisce ogni ~18 mesi; le cartucce costano poco, e l'unità stessa costa ancora meno.
- **Sensori**: un Bosch BME280 e un SHT35 affiancati sul ripiano. Due sensori perché quelli di umidità derivano nel tempo, e un setpoint sbagliato del 10 % è la differenza fra piante sane e muffa.
- **Controller**: un secondo Raspberry Pi (non quello del terrario d'alta quota) esegue un piccolo loop Python: legge i due sensori, fa la media e commuta la presa Tapo con la libreria PyP100 per tenere l'UR intorno all'80 % con isteresi. Niente InfluxDB, niente dashboard, niente Node-RED; un setpoint, una banda morta e un file di log.
- **Luce**: una semplice striscia LED full-spectrum in cima a ogni ripiano, su una presa con timer giornaliero stupido (niente rampe di alba, niente PID, niente Node-RED).
- **Il resto**: aria della stanza, temperatura della stanza, luce del davanzale dove serve.

L'allestimento completo costa una frazione del terrario d'alta quota, e la maggior parte delle piante che altrimenti finirebbero nel terrario non ne ha bisogno. Sui ripiani stanno quelle che non lo richiedono.
