"""Export Plant_Inventory.xlsx → website/static/data/collection.csv.

Schema per website/HANDOFF.md:
  id, taxon, genus, species, infraspecific, source, price_eur,
  acquired_date, status, location, notes
"""
import csv
import re
import sys
from pathlib import Path

import openpyxl

EXCEL = Path("/Users/gabrielezoppoli/Documents/documenti personali/botanica/dendrogram/Plant_Inventory.xlsx")
CSV = Path("/Users/gabrielezoppoli/Desktop/terrarium-paper/website/static/data/collection.csv")

STATUS = {"✓": "alive", "†": "lost", "➜": "given"}

INFRA_MARKERS = [" var. ", " subsp. ", " ssp. ", " f. ", " forma ", " subvar. "]


def split_species(raw: str) -> tuple[str, str]:
    """Return (species, infraspecific) from a raw 'Species / Cultivar' cell.

    Covers the common shapes in this inventory:
      'vesiculosa'                     → ('vesiculosa', '')
      'minor var. pilosa'              → ('minor', 'var. pilosa')
      "minor 'Burgundy Black'"         → ('minor', "'Burgundy Black'")
      "'Godzilla'"                     → ('', "'Godzilla'")
      '× ampla'                        → ('× ampla', '')
    """
    s = (raw or "").strip()
    if not s:
        return "", ""
    for marker in INFRA_MARKERS:
        if marker in s:
            head, tail = s.split(marker, 1)
            return head.strip(), (marker.strip() + " " + tail.strip()).strip()
    m = re.search(r"'[^']+'|\"[^\"]+\"", s)
    if m:
        head = s[: m.start()].strip()
        return head, s[m.start():].strip()
    return s, ""


def main() -> int:
    wb = openpyxl.load_workbook(EXCEL, data_only=True)
    ws = wb["Plant Inventory"]
    CSV.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped = 0
    with CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "id", "taxon", "genus", "species", "infraspecific",
            "source", "price_eur", "acquired_date", "status", "location", "notes",
        ])
        for row in ws.iter_rows(min_row=2, values_only=True):
            idx, genus, sp_cv, vendor, order_date, price, order_no, notes, status_sym, _photo = row
            if not genus and not sp_cv:
                skipped += 1
                continue
            genus = (genus or "").strip()
            sp_cv = (sp_cv or "").strip()
            species, infra = split_species(sp_cv)
            taxon = " ".join(p for p in [genus, sp_cv] if p).strip()
            status = STATUS.get(status_sym, "")
            price_str = f"{price}" if price is not None else ""
            writer.writerow([
                idx if idx is not None else "",
                taxon,
                genus,
                species,
                infra,
                (vendor or "").strip(),
                price_str,
                (order_date or "").strip() if isinstance(order_date, str) else (order_date or ""),
                status,
                "",
                (notes or "").strip() if isinstance(notes, str) else "",
            ])
            written += 1
    print(f"wrote {written} rows → {CSV} (skipped {skipped} empty rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
