import csv
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ingestion"))
from csv_ingestion import ingest_csv
from enrich_row import enrich_record


def load_headers(headers_csv_path: str) -> list[str]:
    with open(headers_csv_path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        return next(reader)


def build_output_row(headers: list[str], record: dict, enriched: dict) -> dict:
    row = {h: "" for h in headers}

    passthrough = {
        "Mfg_Part_Num": record.get("mfg_part_num"),
        "Part_Desc": record.get("raw_description"),
        "E1_Brand": record.get("e1_brand"),
        "Unilog_Brand": record.get("unilog_brand"),
        "DIB_Brand": record.get("dib_brand"),
        "Part_Manuf": record.get("part_manuf_raw"),
        "MANUFACTURER_PART_NUMBER": record.get("mfg_part_num"),
    }
    for k, v in passthrough.items():
        if k in row:
            row[k] = v or ""

    for key in ["MANUFACTURER_NAME", "BRAND_NAME", "Classpath", "SHORT_DESC",
                "INVOICE_DESC", "MOBILE_DESC", "LONG_DESC1"]:
        if key in row:
            row[key] = enriched.get(key, "")

    for i, attr in enumerate(enriched.get("attributes", []), start=1):
        label_col, value_col, uom_col = f"ATTRIBUTE_LABEL {i}", f"ATTRIBUTE_VALUE {i}", f"ATTRIBUTE_UOM {i}"
        if label_col in row:
            row[label_col] = attr.get("label", "")
        if value_col in row:
            row[value_col] = attr.get("value", "")
        if uom_col in row:
            row[uom_col] = attr.get("uom", "")

    return row


def run(input_csv, headers_csv, output_csv, limit=None):
    headers = load_headers(headers_csv)
    records = ingest_csv(input_csv, "../../data/processed/ingested_records.json")

    if limit:
        records = records[:limit]

    output_rows = []
    for i, record in enumerate(records, start=1):
        print(f"Enriching row {i}/{len(records)}: {record.get('clean_description')}")
        enriched = enrich_record(record)
        output_rows.append(build_output_row(headers, record, enriched))

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Wrote {len(output_rows)} rows to {output_csv}")


if __name__ == "__main__":
    input_csv = sys.argv[1] if len(sys.argv) > 1 else "../../data/samples/Unihack_Sample_Dataset_Input.csv"
    headers_csv = sys.argv[2] if len(sys.argv) > 2 else "../../data/samples/Unihack_Expected_Output_Delivery_Format.csv"
    output_csv = sys.argv[3] if len(sys.argv) > 3 else "../../data/outputs/final_output.csv"
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 20

    run(input_csv, headers_csv, output_csv, limit=limit)