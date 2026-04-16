---
title: "Self-watering Zeer Pot for Darlingtonia"
description: "Passive evaporative cooling for the California Pitcher Plant's root zone"
status: "building"
layout: "zeer-pot"
weight: 10
tags: ["carnivorous", "invention", "esp32"]
---

*Darlingtonia californica* — the California Pitcher Plant — needs cold roots while tolerating warm air. In its native habitat, underground springs keep the rhizome below ~18 °C even when air above hits 30 °C. The standard hobbyist solution is a daily flush of cold water or ice cubes in summer, both of which fail quietly on the day you forget.

A Zeer pot (pot-in-pot evaporative cooler) solves the same physics problem the plant already does: water evaporating from an unglazed outer surface pulls heat out of the inner chamber. With a self-topping water reservoir, a pair of thermistors, a capacitive soil probe, and an ESP32-C3 SuperMini pulling it all together, the whole assembly runs unattended for a month at a time.

The full project — CAD sketches, wiring, firmware, bill of materials, build sequence — is below. It's served as a self-contained page retoned to the site's palette; open it fullscreen for comfort.
