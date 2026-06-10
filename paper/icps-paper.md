# A Distributed Ex-Situ Refugium Network for Cloud-Forest Flora: Open-Source Freeware Climate Control and the Climatic-Envelope Convergence That Makes It Possible

**Authors**: Gabriele Zoppoli — Department of Internal Medicine and Medical Specialties (DiMI), University of Genoa, Genoa, Italy; IRCCS Ospedale Policlinico San Martino, Genoa, Italy

**Corresponding author**: gabriele.zoppoli@unige.it

---

## Abstract

Cloud-forest endemics are among the most climate-threatened floras on Earth — warming compresses their narrow elevational bands faster than the species can track — yet institutional ex-situ capacity for them is limited and costly. We argue that a low-cost, open-source freeware controller can turn the world's many private cloud-forest growers into a distributed, standardized, citizen-science ex-situ refugium network, and that this is made horticulturally feasible by a specific biological fact: cloud forests worldwide converge on a bounded climatic envelope (cool ~10–22 °C, 80–100 % RH, frequent cloud immersion, moderate filtered light) despite deep geographic and phylogenetic separation. We demonstrate the principle with 75 living accessions across 31 plant genera, spanning four biogeographic regions — Neotropical highlands (Guayanan tepui, Andes, Brazilian Atlantic Forest), Southeast Asian highlands (Sumatra, Sulawesi, the Philippines), and Papua New Guinea / Oceania — co-cultivated for four years in a single ~1 m³ enclosure in Genoa, Italy. We state the convergence claim carefully: tepui summits are largely treeless *tepuiana* / Pantepui, not tropical montane cloud forest in the strict vegetation sense (Hamilton, Juvik & Scatena 1995; Bruijnzeel et al. 2011), so it is *climatic-envelope* overlap plus vertical micro-zoning, not vegetation-type identity, that permits co-cultivation. The enabling system — a Raspberry-Pi controller driven by real Colombian highland weather phase-shifted into Italian local time, and a marine compressor that reaches ≈13.5 °C in a 22 °C room, below the ≈16.6 °C evaporative wet-bulb floor — costs ≈€2,865 in hardware against €10,000–50,000+ for closed commercial chambers, draws ≈2.63 kWh/day, and runs on entirely free software. Full engineering, carnivore cultivation, and orchid cultivation outcomes are reported in the companion HardwareX, CPN, and *Orchids* (AoS) papers; all code, dashboards, build photographs, and live data are at https://highlandcloudforest.com. We make the case that open-source controlled-environment agriculture is a practical, under-used lever for plant conservation.

**Keywords**: ex-situ conservation, citizen science, cloud forest, climatic convergence, open-source hardware, freeware, controlled-environment agriculture, *Heliamphora*, *Nepenthes*, *Dracula*, *Dendrobium*, Pantepui, distributed refugia

---

## 1. Introduction — The Conservation Problem and the Freeware Thesis

### 1.1 Cloud-forest floras are acutely climate-threatened

Tropical highland environments — from the Guayanan tepui table-top mountains of Venezuela to the Andes, the highlands of Papua New Guinea, the Brazilian Atlantic Forest highlands, and the upper montane forests of Sumatra, Sulawesi, and the Philippines — harbour extraordinary, narrowly endemic plant diversity adapted to tight environmental envelopes: cool temperatures (10–22 °C), persistent high humidity (80–100 % RH), frequent fog or cloud immersion, and moderate light filtered through cloud. These floras are also among the most climate-vulnerable on the planet. Warming pushes the cloud condensation level and the species' thermal optima upslope; on isolated summits and table mountains there is no "upslope" left to migrate to, so the available habitat band is compressed rather than displaced. For the Neotropical Guayana Highlands specifically, Rull & Vegas-Vilarrúbia (2006) projected substantial, potentially unexpected biodiversity loss under even moderate warming scenarios, precisely because the endemic-rich summit flora cannot track its climate envelope across the surrounding lowlands. The same elevational-compression logic applies to the other regions co-cultivated here.

### 1.2 Institutional ex-situ capacity is limited and expensive

Conventional responses — in-situ protection and institutional ex-situ collections in botanic gardens — are essential but insufficient at the scale and specificity these floras demand. Maintaining cool, cloud-immersed conditions outside the native range requires active refrigeration and humidification, which at institutional scale means commercial plant growth chambers (e.g., Percival, Conviron). Such chambers are reliable but cost on the order of €10,000–50,000+ per unit, run proprietary closed-source firmware that the owner cannot inspect or extend, and are concentrated in a small number of well-funded institutions. The number of cloud-forest taxa that can be held this way is bounded by institutional budgets and floor space.

### 1.3 Private growers already hold the collections — but ad hoc

In parallel, a large, dispersed community of private specialist growers already maintains substantial living collections of exactly these taxa — *Heliamphora*, highland *Nepenthes*, *Dracula* and other cool-growing Pleurothallidinae, miniature highland *Dendrobium*, rupicolous Brazilian orchids. Collectively this represents a globally distributed living gene-bank of conservation interest. But it is undocumented and unstandardized: each grower runs a bespoke setup with no shared data model, no auditable environmental record, and no reproducible control logic. Provenance is often informal, husbandry is tacit, and a collection's contents and conditions typically vanish when the grower stops.

### 1.4 Thesis

We propose that the gap between expensive-but-rigorous institutional chambers and cheap-but-ad-hoc private collections can be closed with **open-source freeware**. A reproducible controller costing ≈€2,865 in commodity hardware, running entirely free software on a Raspberry Pi, can standardize and de-risk private holdings: it gives every replicate the same auditable environmental record, the same inspectable and extensible control logic, and the same naturalistic, weather-referenced climate. Standardization is what converts a scattered set of private terraria into a coherent **distributed, citizen-science ex-situ refugium network** — many independent, geographically dispersed nodes holding overlapping and complementary accessions under a documented, reproducible regime, complementing (not replacing) institutional and in-situ conservation.

The remainder of this paper makes the biological and practical case for that thesis. Section 2 develops the convergence principle that makes a *single* low-cost envelope viable for taxa from four biogeographic regions at once — the signature contribution of this paper. Section 3 summarizes the enabling freeware system briefly and cites the companion engineering paper for depth. Section 4 develops the conservation argument for distributed refugia, including honest limitations. We do not re-derive the engineering or re-list the cultivation outcomes here; those are the subjects of the three companion papers and the public website, and are cited rather than reproduced.

---

## 2. The Convergence Principle

The horticultural premise of a distributed refugium network is that one bounded, low-cost climate can host taxa from many disjunct cloud forests simultaneously. If each biogeographic region required its own chamber and its own bespoke regime, the cost-and-complexity barrier the freeware thesis is meant to remove would simply reappear. The premise holds because of climatic convergence — and stating that claim precisely is essential to its credibility.

### 2.1 What converges, and what does not

Cloud forests worldwide occupy a remarkably bounded climatic envelope despite their geographic and phylogenetic isolation: cool mean temperatures, persistent near-saturation humidity, frequent fog or cloud immersion, and moderate, cloud-filtered light. The proximate cause is physics, not biogeography. The saturated adiabatic lapse rate in the tropics is approximately 0.5–0.6 °C per 100 m of elevation gain, so at the 2,000–2,800 m band occupied by most of the taxa discussed here, mean temperatures fall to roughly 10–18 °C regardless of longitude. Cloud-immersion frequencies of 50–80 % of nighttime hours are typical of tropical montane cloud environments globally (Jarvis & Mulligan 2011), driving 80–100 % RH at these elevations. Two equatorial mountains 15,000 km apart therefore present strikingly similar temperature, humidity, and vapour-pressure-deficit regimes.

This is the claim — and only this claim. We are deliberately careful about its boundaries:

- **It is climatic-envelope overlap, not vegetation-type identity.** In the strict Hamilton–Juvik–Scatena (1995) and Bruijnzeel et al. (2011) sense, tropical montane cloud forest (TMCF) is a *forest* with cloud-immersion-dependent structure. Several of our source habitats are not TMCF at all: the tepui summits are largely treeless *tepuiana* / Pantepui shrubland and meadow with a physiognomy bearing no resemblance to a Sumatran mossy forest. We therefore claim convergence of the *bounded T / RH / VPD climatic envelope*, not that these are the same vegetation type or interchangeable ecosystems. A tepui summit, an Andean understory, a Brazilian inselberg, and a Papuan ridge differ in substrate, pH, nutrient status, wind, UV, and seasonal water regime; they overlap in the daily temperature, humidity, and VPD ranges that a terrarium controller can target.
- **Co-cultivation also requires vertical micro-zoning, not a single uniform climate.** The shared envelope is necessary but not sufficient. A single overhead light source produces an inverse-square irradiance gradient and a mild thermal gradient from top to bottom of the enclosure; high-light, warmth-tolerant taxa occupy the upper tier and shade- and cool-favouring taxa the lower tier. The result is one enclosure with vertical microhabitat zoning, not one point-identical climate experienced by every plant.

With those two qualifications, the principle is defensible and load-bearing: a single controller tuned to the shared envelope, with a vertical light/temperature gradient to spread irradiance and warmth requirements, can host cloud-forest taxa from multiple continents at once. That is what makes a low-cost distributed network feasible — each node is one cabinet, not four.

### 2.2 Evidence: 75 accessions, 31 genera, four biogeographic regions, one envelope

The convergence principle is evidenced here by four years of continuous co-cultivation of 75 living accessions across 31 plant genera in a single ~1 m³ enclosure, all under one weather-referenced envelope with vertical zoning. The cohort spans **four biogeographic regions on three continents**: the Neotropical highlands (subdivided into Guayanan tepui, the Andes, and the Brazilian Atlantic Forest), the Southeast Asian highlands (Sumatra, Sulawesi, the Philippines), and Papua New Guinea / Oceania. Cabinet residence times within the cohort range from roughly ten years (the longest-tenured *Nepenthes* and *Heliamphora*, transferred in from the previous-generation enclosure) to a few months (recent acquisitions); the "four years" framing refers to continuous operation of the present cabinet, not to each accession's tenure.

A small minority of the 75 accessions are companion taxa from neighbouring biomes (for example *Sophronitis pygmaea*-allied rupicoles with strongly seasonal native regimes, or a few miniature *Holcoglossum* spanning seasonally drier habitats) that tolerate the envelope without being part of the cloud-forest convergence cohort proper; the convergence claim is grounded on the cloud-forest majority. Conversely, taxa whose flowering biology demands a pronounced dry rest (most of the *Cattleya* alliance with strong dry-rest cues; *Dendrobium* section *Callista*) were excluded from the cabinet pre-emptively, because the continuous high humidity is fundamentally incompatible with their cycle — climate-envelope compatibility is a *pre-condition for inclusion in the cohort*, not a post-hoc explanation of survival within it.

Table 1 gives the cross-biome cohabitation matrix: which genera, from which region, occupy which vertical tier, under the single shared envelope. This is the signature evidence of the paper. The taxon-by-taxon cultivation outcomes — pitcher production and division in *Heliamphora*, the first cabinet flowering of *Utricularia quelchii*, *Nepenthes* pitcher development, *Dracula* / *Masdevallia* / *Restrepia* bloom records, the Brazilian rupicolous orchids — are reported in detail in the companion CPN (carnivores) and *Orchids* / AoS (orchids) papers and are not reproduced here; Table 1 cites them for each row.

**Table 1. Cross-biome cohabitation matrix.** Genera (alive, in the highland cabinet; filtered from `collection.csv` on `location = highland AND status = alive`, *Aerangis somalensis* excluded as a non-cohort fog-shelf plant) grouped by biogeographic region, with the vertical tier each occupies under the single shared climatic envelope, and the companion paper carrying its cultivation outcomes. Counts are living accessions.

| Region | Genus (accessions) | Family / group | Vertical tier | Cultivation detail in |
|---|---|---|---|---|
| **Neotropics — Guayanan tepui / Guiana Shield** | *Heliamphora* (9) | Sarraceniaceae | Upper (high light) | CPN |
| | *Brocchinia reducta* (1) | Bromeliaceae (carnivorous) | Upper (high light) | CPN |
| | *Utricularia quelchii* (1) | Lentibulariaceae, sect. *Orchidioides* | Middle (kokedama) | CPN |
| **Neotropics — Andes** | *Dracula* (6) | Orchidaceae, Pleurothallidinae | Lower (deep shade, coolest) | AoS |
| | *Masdevallia* (5) | Orchidaceae, Pleurothallidinae | Lower–middle | AoS |
| | *Restrepia* (3) | Orchidaceae, Pleurothallidinae | Lower | AoS |
| | Misc. miniature Pleurothallidinae & allies — *Lepanthopsis* (2), *Platystele* (1), *Pleurothallis* (1), *Nageliella* (1), *Oerstedella* (1), *Comparettia* (1), *Macroclinium* (1), *Phymatidium* (1), *Oncidium* (1), *Ceratochilus* (1), *Maxillaria* (1) | Orchidaceae | Throughout (mounted) | AoS |
| | *Phragmipedium kovachii* (1) | Orchidaceae (CITES App. I) | Middle | AoS |
| **Neotropics — Brazilian Atlantic Forest** | *Sophronitis* (5) | Orchidaceae (rupicolous *Cattleya* alliance) | Upper–middle | AoS |
| | *Cattleya* (3) | Orchidaceae | Upper–middle | AoS |
| | *Laelia* (3) | Orchidaceae | Upper–middle | AoS |
| | *Leptotes* (2), *Isabelia* (1), *Ornitophora* (1) | Orchidaceae | Upper–middle (mounted) | AoS |
| **SE Asian highlands — Sumatra / Sulawesi / Philippines** | *Nepenthes* (9) | Nepenthaceae | Lower (floor, coolest) | CPN |
| | *Holcoglossum* (3), *Schoenorchis* (1), *Chiloschista* (1) | Orchidaceae (vandaceous miniatures) | Middle–upper (mounted) | AoS |
| **PNG / Oceania (with Philippine & Vietnamese highland members)** | *Dendrobium* (5) — incl. PNG sect. *Oxyglossum* (*D. cuthbertsonii* 'Yellow', *D. cyanocentrum*, *D. hellwigianum*), Philippine sect. *Calcarifera* (*D. victoriae-reginae*), Vietnamese (*D. trantuanii*) | Orchidaceae | Upper (tree-fern plaques) | AoS |
| | *Mediocalcar* (1) | Orchidaceae | Upper (mounted) | AoS |
| **Companion (all regions)** | *Sphagnum* (2 spp.) | living moss — substrate & moisture indicator | Throughout | — |

Notes on Table 1, for taxonomic and biogeographic precision (each cross-checked against POWO/IOSPE and detailed in the cited companions):

- **Tepui provenance, carefully stated.** *Brocchinia reducta* is a **Guiana Shield** bromeliad (native range Venezuela–Guyana–Brazil within the wet tropical biome), not a tepui-summit endemic. *Utricularia quelchii* (sect. *Orchidioides*, Ilu Tepui provenance) is the **only** sect. *Orchidioides* accession currently alive in the cabinet; it produced its first cabinet flowering in April–May 2026 (detail in CPN).
- **Nepenthes** are from **Sumatra, Sulawesi, and the Philippines** (1,500–3,000 m); there is **no Bornean accession** in the current cabinet. Famous Bornean ultra-highlanders (*N. villosa*, *N. lowii*, *N. rajah*) are noted only for biogeographic context.
- **Dendrobium** is taxonomically mixed and must not be summarized as "PNG." Genuine PNG sect. *Oxyglossum* members alive in the cabinet are *D. cuthbertsonii* 'Yellow', *D. cyanocentrum*, and *D. hellwigianum* (the earlier *D. cuthbertsonii* clone was a documented loss, replaced). *D. victoriae-reginae* is **Philippine**, sect. *Calcarifera* per POWO/IOSPE — not PNG/*Oxyglossum*, despite its colloquial "blue dendrobium" reputation — and is retained as a Philippine highland representative. *D. trantuanii* is a Vietnamese highland species in yet another section. Its cultural requirements coincide with the *Oxyglossum* group, which is why all grow together.
- **Brazilian "rupicolous" orchids** are identified to species in the AoS companion; the *Cattleya* present (*C. aclandiae*, *C. walkeriana* clones) sit toward the seasonally-drier edge of the cohort and are companion rather than core cloud-forest taxa.

The single most important reading of Table 1 is structural: genera that evolved in complete geographic and phylogenetic isolation — Pantepui *Heliamphora*, Andean *Dracula*, Sumatran *Nepenthes*, Papuan *Oxyglossum* *Dendrobium* — share enough of the climatic envelope to be held, flowered, and propagated under one low-cost controller, provided dry-rest-demanding taxa are excluded and irradiance is spread vertically. That is the biological fact on which the distributed-refugium argument rests.

---

## 3. The Freeware System, Briefly

The enabling controller is described in full in the companion HardwareX paper, with build photographs, live data, and the complete bill of materials mirrored at https://highlandcloudforest.com; the source code, firmware, and dashboards are at https://github.com/GabrieleZoppoli/terrarium-control-system. We summarize here only what is needed to make the conservation argument, and cite the companion for everything quantitative.

**Naturalistic, weather-referenced setpoints.** Rather than fixed day/night schedules, the controller ingests real-time weather from four Colombian highland cities (1,300–2,640 m, ~5° N) and reconstructs a continuously varying, stochastic environmental signal — real rain events become real cooling and humidity spikes that stand in for cloud-immersion episodes. A 15-hour backward look against the locally archived Colombian time-series, combined with the 7-hour Italy-to-Colombia offset, phase-aligns the cabinet's diurnal cycle to Italian local time while preserving the weather's stochastic content (without the shift the cycle would invert). A dynamic photoperiod derived from the near-equatorial source latitude provides seasonally varying day length. The full derivation, cross-validation, and fallback behaviour are in the HardwareX companion.

**Cooling below the evaporative floor — the conservation-relevant capability.** A marine-refrigeration unit (Vitrifrigo ND50, factory-sealed R134a loop) with an internal stainless-steel evaporator plate routinely drives the cabinet to ≈13.5 °C in a 22 °C room — roughly 3 °C *below* the ≈16.6 °C evaporative wet-bulb floor that caps misting-and-fan methods. This matters for conservation specifically: it is the *cold nocturnal regime* — the 4–8 °C nighttime drops that cue and sustain cloud-forest physiology — that evaporative cooling fundamentally cannot reach, and that a marine compressor accesses cheaply (the unit ships pre-charged, so no F-gas certification is needed to install it). The heat-balance attribution (compressor ≈ −1.01 °C/hr when active; fan PWM as the humidity actuator, IV/2SLS ≈ −0.34 % RH per +10 PWM) is reported and fully specified in the HardwareX companion and is not re-derived here.

**Low power, commodity hardware, free software.** The complete control stack — Node-RED, InfluxDB, Grafana, Mosquitto — runs on a single Raspberry Pi with an Arduino Mega for hardware I/O; total measured draw is ≈2.63 kWh/day (≈€288/year at €0.30/kWh). Reliability over four years of continuous operation rests on an **eleven-layer safety chain** (door-open interlock, freezer daytime gate, manual-override timeout, power cross-check, LED-fault watchdog, serial-link integrity, mister water-gate, and others), each layer deployed in response to a specific observed failure mode; the operator is paged on any non-green condition via an automated Gmail/WhatsApp alert chain, so a node can run unattended for months. The full safety-chain deployment chronology and the reliability window are tabulated in the HardwareX companion.

The single conservation-relevant takeaway is the cost-and-capability contrast: ≈€2,865 of commodity hardware and entirely free software deliver the cool-nocturnal, high-humidity, weather-variable envelope that the convergence cohort requires — a regime otherwise available only from closed-source commercial chambers an order of magnitude more expensive.

---

## 4. Citizen-Science Ex-Situ Refugia

The convergence principle (§2) shows that one low-cost cabinet can hold a cross-biome cloud-forest cohort; the freeware system (§3) shows that the cabinet is cheap, reproducible, and inspectable. Together they support the central argument of this paper: that open-source controlled-environment agriculture can convert the dispersed private-grower community into a distributed ex-situ refugium network of genuine conservation value.

### 4.1 Distributed private refugia complement institutional and in-situ conservation

We do not claim that a network of hobbyist cabinets substitutes for habitat protection or for accredited botanic-garden programmes. We claim it *complements* them, filling gaps that the institutional model structurally cannot. Institutional ex-situ capacity for cool cloud-forest taxa is concentrated in a few well-funded centres and bounded by their budgets and floor space; a single catastrophic event (an equipment failure, a funding cut, a pathogen sweep) can remove an entire holding. A distributed network is, by contrast, resilient by construction: many independent nodes in many locations, holding overlapping and complementary accessions, with no single point of failure. The private-grower community already maintains, collectively, more living cloud-forest material than the institutions do — the deficit is not material, it is *standardization and documentation*.

### 4.2 Standardization makes private holdings reproducible and auditable

This is what the open-source freeware contributes that an ad-hoc setup cannot. Because every node runs the same inspectable control logic and logs the same auditable environmental record (continuous time-series of temperature, humidity, VPD, actuator states), a holding becomes reproducible: another grower can replicate the exact regime, and a future custodian can take over a collection with its full environmental and provenance history intact rather than as tacit knowledge that dies with the grower. Freeware specifically — as opposed to a cheaper-but-closed commercial controller — is what allows the network to be audited, extended, corrected, and forked by its own community. Standardization also makes the network's data scientifically useful in aggregate: distributed nodes generate a multi-site, multi-year record of what envelope actually sustains which taxa, which no single institution could assemble.

### 4.3 The no-dry-rest design choice as a deliberate conservation prioritization

The cabinet maintains continuous high humidity with no dry rest period. This is a conscious conservation trade-off, not an oversight: it sacrifices the dry-season flowering triggers of some taxa in order to protect the moisture-dependent species (*Heliamphora*, sect. *Orchidioides* *Utricularia*, *Dracula*) for which even a brief desiccation is lethal. The priority is survival of the most vulnerable accessions over maximal floral display across the cohort — exactly the priority a refugium should have. The horticultural detail of this choice, and which taxa it favours and disfavours, is developed in the AoS companion; we note here only that prioritizing the persistence of irreplaceable moisture-dependent material is the conservation-correct decision for an ex-situ refugium.

### 4.4 Accessibility versus closed commercial chambers

The economic argument is straightforward and is the lever that makes a *distributed* network possible. A closed-source commercial growth chamber costs €10,000–50,000+; the freeware cabinet costs ≈€2,865 in hardware and ≈€288/year to run. The order-of-magnitude cost reduction is what brings conservation-grade environmental control within reach of the existing private-grower community, and the open licensing is what lets that community improve and trust the system collectively. Cost is not the only barrier the design removes: the pre-charged marine-refrigeration loop removes the F-gas-certification skills barrier that historically confined DIY compressor cooling to chest-freezer conversions, and Node-RED's visual flow programming lowers the software barrier.

### 4.5 Honest limitations

A credible conservation argument must state its boundaries plainly:

- **Genetic provenance and documentation.** Much private material, including parts of this collection, carries informal or horticultural-trade provenance rather than wild-collection data with known locality and genetic backing. A distributed network improves *husbandry* documentation enormously, but it does not by itself supply rigorous provenance; realizing the conservation value will require pairing the freeware standard with disciplined accession recording (locality, source, propagation history). This is a community practice to build, not a property the hardware confers.
- **CITES and legal compliance.** Cloud-forest floras include CITES-listed taxa (the cabinet holds *Phragmipedium kovachii*, Appendix I, acquired under standard licensed-dealer paperwork for artificially-propagated specimens). A refugium network must operate strictly within CITES and national law; open-sourcing the *controller* does nothing to relax those obligations, and any network advocacy must foreground legal, ethical, artificially-propagated sourcing.
- **Not a substitute for habitat protection.** Ex-situ holdings, however distributed and well-documented, conserve genotypes, not ecosystems, pollinator relationships, or evolutionary context. The network is a complement and an insurance policy against extinction-in-the-wild, not a replacement for protecting the tepui summits, Andean cloud forests, and Papuan ridges themselves.
- **Single-cabinet evidence here.** The demonstration in this paper is one node over four years. The claim that this scales to a *network* is an argument from reproducibility and cost, not yet a demonstrated multi-site result; building and documenting that network is the work this paper calls for.

---

## 5. Conclusions

Cloud-forest endemics are losing their climate envelopes faster than they can track them, and the institutional ex-situ response, while essential, is too small and too concentrated to hold the breadth of threatened material on its own. We have argued — and demonstrated at the single-node scale over four years — that an open-source freeware controller can close the gap by turning the dispersed private-grower community into a standardized, auditable, distributed ex-situ refugium network.

Two facts make the argument work. The biological fact is **climatic-envelope convergence**: cloud forests worldwide, driven by the physics of tropical mountain meteorology rather than by biogeographic proximity, share a bounded cool/humid/cloud-immersed envelope, so a *single* low-cost cabinet — with vertical micro-zoning to spread irradiance, and dry-rest-demanding taxa excluded — can host a cohort of 75 accessions across 31 genera spanning four biogeographic regions. We have stated that claim carefully: it is convergence of the T/RH/VPD envelope, not of vegetation type, and tepui summits are *tepuiana*, not TMCF. The engineering fact is that **freeware plus commodity hardware** delivers conservation-grade environmental control — including the cold nocturnal regime below the evaporative wet-bulb floor — for ≈€2,865 against €10,000–50,000+ for closed commercial chambers, with every line of code inspectable, extensible, and free.

The call to action is for the plant-conservation and controlled-environment-agriculture communities to take open-source freeware seriously as a conservation lever. The components already exist: the threatened floras, the private collections that already hold them, the cheap hardware, and now a documented, reproducible, freely licensed control system. What remains is to connect them — to pair the freeware standard with disciplined provenance recording and lawful sourcing, and to grow the single demonstrated node into the distributed refugium network that cloud-forest conservation needs. The full engineering, the carnivore cultivation record, and the orchid cultivation record that underpin this argument are reported in the companion HardwareX, CPN, and *Orchids* papers, and the complete system — code, data, and photographs — is freely available at https://highlandcloudforest.com.

---

## Acknowledgments

I thank the specialist nurseries that supplied legally and ethically sourced, artificially-propagated material — including, for the cloud-forest taxa, Andreas Wistuba, Christian & Claudia Klein / Carnivors & More, and Ecuagenera — and the open-source software communities behind Node-RED, InfluxDB, Grafana, Mosquitto, and the Raspberry Pi and Arduino projects, on which the freely-licensed control system is built. I also thank the carnivorous-plant and orchid growing communities, whose shared cultivation experience shaped the species selection and the no-dry-rest design discussed here. *[Author to add or amend: institutional support, individual collaborators, and any reviewers or beta-testers of the open-source release the author wishes to thank.]*

Portions of this manuscript were prepared with the assistance of an AI language model (Anthropic Claude). The system design, construction, data collection, plant cultivation, and all horticultural and conservation arguments are entirely the work of the author(s).

---

## References

Bruijnzeel, L.A., Scatena, F.N. & Hamilton, L.S. (eds.) 2011. *Tropical Montane Cloud Forests: Science for Conservation and Management.* Cambridge University Press, Cambridge.

Hamilton, L.S., Juvik, J.O. & Scatena, F.N. (eds.) 1995. *Tropical Montane Cloud Forests.* Ecological Studies 110, Springer-Verlag, New York.

Jarvis, A. & Mulligan, M. 2011. The climate of cloud forests. In: Bruijnzeel, L.A., Scatena, F.N. & Hamilton, L.S. (eds.), *Tropical Montane Cloud Forests: Science for Conservation and Management.* Cambridge University Press, pp. 39–56.

Rull, V. & Vegas-Vilarrúbia, T. 2006. Unexpected biodiversity loss under global warming in the neotropical Guayana Highlands: a preliminary appraisal. *Global Change Biology* 12: 1–6.

Rull, V., Montoya, E., Nogué, S., Safont, E. & Vegas-Vilarrúbia, T. 2019. Climatic and ecological history of Pantepui and surrounding areas. In: Rull, V. & Vegas-Vilarrúbia, T. (eds.), *Biodiversity of Pantepui: The Pristine "Lost World" of the Neotropical Guiana Highlands.* Academic Press, pp. 37–57.

Zoppoli, G. (submitted-a). Weather-Mimicking Terrarium for Cloud Forest Species: An Open-Source Climate Simulation System Using Real-Time Meteorological Data. *HardwareX* (companion engineering paper). DOI on acceptance.

Zoppoli, G. (submitted-b). Weather-Mimicking Terrarium Cultivation of Highland Carnivorous Plants: Four Years of *Heliamphora*, *Nepenthes*, and *Utricularia* sect. *Orchidioides*. *Carnivorous Plant Newsletter* (companion paper).

Zoppoli, G. (submitted-c). Cloud Forest in a Box: Growing Highland Orchids with Real-Time Weather Simulation. *Orchids* (American Orchid Society) (companion paper).

*If a specific quantitative tepui microclimate figure is added to the convergence section beyond the lapse-rate/cloud-immersion generalities, cite Adlassnig et al. (2010), Roraima* Heliamphora nutans *microclimate, as in the companion CPN paper.*

---

## Supplementary Materials and Data Availability

All code, firmware, dashboards, analysis scripts, build photographs, the complete bill of materials, and live cabinet conditions are freely available:

- **Website (live data, build photos, blog, how-it-works):** https://highlandcloudforest.com
- **Source repository:** https://github.com/GabrieleZoppoli/terrarium-control-system

The engineering (hardware, control logic, heat-balance and IV/2SLS analyses, reliability), the carnivorous-plant cultivation record, and the orchid cultivation record are reported in full in the companion HardwareX, CPN, and *Orchids* (AoS) papers respectively, and are cited rather than reproduced in this synthesis.
