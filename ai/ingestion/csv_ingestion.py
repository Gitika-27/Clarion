"""
Reads the real UniHack input CSV (Mfg_Part_Num, Part_Desc, E1_Brand,
Unilog_Brand, DIB_Brand, Part_Manuf) and produces cleaned, structured
records ready for the classification/attribute-extraction stage (Person 2)
and eventual mapping into the 252-column Delivery Format (Person 3 / final
export).

This replaces the PDF/image path as the PRIMARY ingestion path for the
actual graded task -- the real dataset has no PDFs or images in it.
"""

import csv
import json
import re

# These strings mean "this field is empty" -- not real brand data.
# Filter them out immediately so nothing downstream treats them as values.
PLACEHOLDER_VALUES = {
    "-- unbranded --",
    "-- no unilog brand --",
    "-- no dib brand --",
    "",
}


def clean_field(value):
    """Returns None for empty/placeholder values, otherwise a trimmed string."""
    if value is None:
        return None
    v = value.strip()
    if v.lower() in PLACEHOLDER_VALUES:
        return None
    return v


def clean_description(desc):
    """Collapses irregular whitespace in the raw description."""
    if not desc:
        return None
    return re.sub(r"\s+", " ", desc.strip())


def parse_manufacturer_field(raw):
    """
    'Freud Inc (2435)' -> {"name": "Freud Inc", "code": "2435"}
    'Jam Industrial Supply LLC (JAMIN)' -> {"name": "Jam Industrial Supply LLC", "code": "JAMIN"}
    A raw value with no parentheses just becomes the name, with no code.
    """
    if not raw or not raw.strip():
        return {"name": None, "code": None}

    match = re.match(r"^(.*)\((.*)\)\s*$", raw.strip())
    if match:
        return {"name": match.group(1).strip(), "code": match.group(2).strip()}

    return {"name": raw.strip(), "code": None}


def ingest_csv(input_path: str, output_path: str) -> list[dict]:
    records = []

    with open(input_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            manuf = parse_manufacturer_field(row.get("Part_Manuf"))

            record = {
                "row_id": f"row_{i}",
                "mfg_part_num": clean_field(row.get("Mfg_Part_Num")),
                "raw_description": row.get("Part_Desc"),
                "clean_description": clean_description(row.get("Part_Desc")),
                "e1_brand": clean_field(row.get("E1_Brand")),
                "unilog_brand": clean_field(row.get("Unilog_Brand")),
                "dib_brand": clean_field(row.get("DIB_Brand")),
                "part_manuf_raw": row.get("Part_Manuf"),
                "manufacturer_name_candidate": manuf["name"],
                "manufacturer_code_candidate": manuf["code"],
            }
            records.append(record)

    with open(output_path, "w") as f:
        json.dump(records, f, indent=2)

    print(f"Ingested {len(records)} rows -> {output_path}")
    return records


if __name__ == "__main__":
    import sys
    input_path = sys.argv[1] if len(sys.argv) > 1 else "../../data/samples/Unihack_Sample_Dataset_Input.csv"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "../../data/processed/ingested_records.json"
    ingest_csv(input_path, output_path)