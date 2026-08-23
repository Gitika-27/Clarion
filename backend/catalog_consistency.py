"""
Clarion - Member 3: Catalog Consistency & Statistical Outlier Detection

This module inspects extracted product records against the catalog to detect
statistical anomalies and physically implausible values (e.g. 2300V instead of 230V,
1200mm vs 12mm) using IQR (Interquartile Range) and Z-score (Mean +/- StdDev) metrics.
"""

from __future__ import annotations
import math
import re
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class OutlierAnomaly:
    record_id: str
    product_name: str
    field_name: str
    raw_value: str
    numeric_value: float
    unit: str
    method: str  # "IQR" or "Z-SCORE"
    severity: str  # "high", "medium", "warning"
    explanation: str
    catalog_stats: dict[str, float]
    suggested_fix: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def extract_numeric_value(raw: Any) -> tuple[float | None, str]:
    """
    Extracts numerical value and recognized unit from string or numeric input.
    Examples:
      "230V" -> (230.0, "V")
      "12.5 mm" -> (12.5, "mm")
      "47 dBA" -> (47.0, "dBA")
      "120" -> (120.0, "")
    """
    if raw is None:
        return None, ""

    if isinstance(raw, (int, float)):
        return float(raw), ""

    text = str(raw).strip()
    match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
    if not match:
        return None, ""

    num_str = match.group(0)
    try:
        val = float(num_str)
    except ValueError:
        return None, ""

    after_match = text[match.end():].strip()
    unit = re.sub(r"[^a-zA-Z%]", "", after_match)
    if not unit:
        before_match = text[:match.start()].strip()
        if "$" in before_match:
            unit = "$"

    return val, unit


class CatalogConsistencyChecker:
    """
    Analyzes numeric attributes across product catalog records to identify
    outliers, potential typos, and unit mismatches.
    """

    NUMERIC_FIELDS = [
        "rated_voltage",
        "voltage",
        "size",
        "sound_level",
        "length",
        "width",
        "height",
        "weight",
        "amperage",
        "list_price",
        "selling_qty"
    ]

    def __init__(self, records: list[dict[str, Any]] | None = None):
        self.records = records or []

    def set_records(self, records: list[dict[str, Any]]) -> None:
        self.records = records

    def compute_field_statistics(self, field_name: str) -> dict[str, Any]:
        """
        Calculates mean, standard deviation, Q1, median, Q3, IQR, min, max for a given field.
        """
        values: list[float] = []
        for rec in self.records:
            fields = rec.get("fields", {}) if "fields" in rec else rec
            val, _ = extract_numeric_value(fields.get(field_name))
            if val is not None and not math.isnan(val) and not math.isinf(val):
                values.append(val)

        if not values:
            return {
                "field": field_name,
                "count": 0,
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "q1": 0.0,
                "median": 0.0,
                "q3": 0.0,
                "max": 0.0,
                "iqr": 0.0,
                "lower_bound_iqr": 0.0,
                "upper_bound_iqr": 0.0,
            }

        values.sort()
        n = len(values)
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / max(n - 1, 1)
        std = math.sqrt(variance)

        def percentile(p: float) -> float:
            k = (n - 1) * p
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return values[int(k)]
            d0 = values[int(f)] * (c - k)
            d1 = values[int(c)] * (k - f)
            return d0 + d1

        q1 = percentile(0.25)
        median = percentile(0.50)
        q3 = percentile(0.75)
        iqr = q3 - q1
        lower_iqr = q1 - 1.5 * iqr
        upper_iqr = q3 + 1.5 * iqr

        return {
            "field": field_name,
            "count": n,
            "mean": round(mean, 2),
            "std": round(std, 2),
            "min": round(values[0], 2),
            "q1": round(q1, 2),
            "median": round(median, 2),
            "q3": round(q3, 2),
            "max": round(values[-1], 2),
            "iqr": round(iqr, 2),
            "lower_bound_iqr": round(lower_iqr, 2),
            "upper_bound_iqr": round(upper_iqr, 2),
        }

    def detect_outliers(
        self,
        z_threshold: float = 3.0,
        use_iqr: bool = True
    ) -> list[OutlierAnomaly]:
        """
        Scans all records for statistical and domain anomalies.
        """
        anomalies: list[OutlierAnomaly] = []
        if not self.records:
            return anomalies

        all_fields = set()
        for rec in self.records:
            fields = rec.get("fields", {}) if "fields" in rec else rec
            all_fields.update(fields.keys())

        target_fields = [f for f in all_fields if any(nf in f.lower() for nf in self.NUMERIC_FIELDS)]
        stats_map = {field: self.compute_field_statistics(field) for field in target_fields}

        for rec in self.records:
            rec_id = rec.get("record_id") or rec.get("id") or rec.get("row_id") or "unknown"
            prod_name = rec.get("product_name") or rec.get("mfg_part_num") or rec.get("clean_description") or "Product"
            fields = rec.get("fields", {}) if "fields" in rec else rec

            for field_name in target_fields:
                if field_name not in fields:
                    continue

                raw_val = fields[field_name]
                if isinstance(raw_val, dict):
                    raw_val = raw_val.get("value", "")

                num_val, unit = extract_numeric_value(raw_val)
                if num_val is None:
                    continue

                stats = stats_map.get(field_name)
                if not stats or stats["count"] < 3:
                    domain_anomaly = self._check_domain_heuristics(
                        rec_id=rec_id,
                        prod_name=str(prod_name),
                        field_name=field_name,
                        raw_val=str(raw_val),
                        num_val=num_val,
                        unit=unit,
                        stats=stats or {}
                    )
                    if domain_anomaly:
                        anomalies.append(domain_anomaly)
                    continue

                # 1. IQR Method
                is_iqr_outlier = False
                if use_iqr and stats["iqr"] > 0:
                    if num_val < stats["lower_bound_iqr"] or num_val > stats["upper_bound_iqr"]:
                        is_iqr_outlier = True

                # 2. Z-Score Method
                z_score = 0.0
                if stats["std"] > 0:
                    z_score = abs(num_val - stats["mean"]) / stats["std"]
                is_z_outlier = z_score >= z_threshold

                if is_iqr_outlier or is_z_outlier:
                    direction = "above" if num_val > stats["mean"] else "below"
                    severity = "high" if z_score >= 4.0 or (stats["iqr"] > 0 and (num_val > stats["q3"] + 3 * stats["iqr"] or num_val < stats["q1"] - 3 * stats["iqr"])) else "medium"

                    suggested_fix = None
                    base_ref = stats["median"] if stats.get("median", 0) > 0 else stats.get("mean", 0)
                    if base_ref > 0:
                        ratio = num_val / base_ref
                        if 8.0 <= ratio <= 12.0:
                            suggested_fix = f"{round(num_val / 10.0, 2)} {unit}".strip()
                        elif 80.0 <= ratio <= 120.0:
                            suggested_fix = f"{round(num_val / 100.0, 2)} {unit}".strip()

                    explanation = (
                        f"Value {num_val}{unit} is statistically anomalous ({direction} expected range). "
                        f"Catalog median is {stats['median']}{unit} (IQR: [{stats['q1']}, {stats['q3']}]). "
                        f"Z-score: {round(z_score, 2)}."
                    )
                    if suggested_fix:
                        explanation += f" Probable multiplier typo; suggested correction is {suggested_fix}."

                    anomalies.append(
                        OutlierAnomaly(
                            record_id=rec_id,
                            product_name=str(prod_name),
                            field_name=field_name,
                            raw_value=str(raw_val),
                            numeric_value=num_val,
                            unit=unit,
                            method="IQR + Z-Score" if (is_iqr_outlier and is_z_outlier) else ("IQR" if is_iqr_outlier else "Z-Score"),
                            severity=severity,
                            explanation=explanation,
                            catalog_stats=stats,
                            suggested_fix=suggested_fix,
                        )
                    )

        return anomalies

    def _check_domain_heuristics(
        self,
        rec_id: str,
        prod_name: str,
        field_name: str,
        raw_val: str,
        num_val: float,
        unit: str,
        stats: dict[str, float]
    ) -> OutlierAnomaly | None:
        field_lower = field_name.lower()

        if "voltage" in field_lower:
            if num_val > 1000 or (num_val > 0 and num_val < 3):
                suggested = f"{round(num_val / 10, 1)}V" if num_val >= 1000 and num_val <= 6000 else None
                return OutlierAnomaly(
                    record_id=rec_id,
                    product_name=prod_name,
                    field_name=field_name,
                    raw_value=raw_val,
                    numeric_value=num_val,
                    unit=unit or "V",
                    method="Domain Sanity Rule",
                    severity="high",
                    explanation=f"Rated voltage of {num_val}V is outside plausible industrial range (12V - 690V).",
                    catalog_stats=stats,
                    suggested_fix=suggested,
                )

        if "sound" in field_lower:
            if num_val > 140 or (num_val > 0 and num_val < 15):
                return OutlierAnomaly(
                    record_id=rec_id,
                    product_name=prod_name,
                    field_name=field_name,
                    raw_value=raw_val,
                    numeric_value=num_val,
                    unit=unit or "dBA",
                    method="Domain Sanity Rule",
                    severity="high",
                    explanation=f"Sound level of {num_val} dBA is outside normal physical limits (20 - 130 dBA).",
                    catalog_stats=stats,
                    suggested_fix=None,
                )

        return None
