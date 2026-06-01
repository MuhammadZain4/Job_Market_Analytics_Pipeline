import csv
import json
import os
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[1]

MANDATORY_COLUMNS = [
    "source", "job_id", "title", "company_name", "location_raw", "remote_status",
    "job_type", "category_raw", "tags_raw", "description", "publication_date",
    "job_url", "salary_text_raw", "salary_min_raw", "salary_max_raw", "currency_raw",
    "salary_min_usd", "salary_max_usd", "salary_mid_usd",
    "experience_years_min", "experience_years_max", "experience_bracket",
    "extracted_skills", "job_category_clean", "scrape_date",
]

def load_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def check_missing_percent(rows, field):
    total = len(rows)
    missing = sum(1 for r in rows if not r.get(field, "").strip())
    return round(missing / total * 100, 2) if total else 0

def check_valid_dates(rows, field):
    invalid = 0
    for r in rows:
        val = r.get(field, "").strip()
        if val:
            try:
                datetime.strptime(val[:10], "%Y-%m-%d")
            except:
                invalid += 1
    return invalid

def validate():
    merged_path = BASE_DIR / "data" / "merged" / "merged_raw_jobs.csv"
    clean_path = BASE_DIR / "data" / "processed" / "clean_ai_ml_data_jobs.csv"
    results = {}

    merged_exists = merged_path.exists()
    results["merged_file_exists"] = merged_exists
    if merged_exists:
        merged = load_csv(merged_path)
        results["merged_total_rows"] = len(merged)
        merged_cols = list(merged[0].keys()) if merged else []
        missing_cols = [c for c in MANDATORY_COLUMNS if c not in merged_cols]
        results["merged_missing_columns"] = missing_cols
        results["merged_schema_ok"] = len(missing_cols) == 0

    clean_exists = clean_path.exists()
    results["clean_file_exists"] = clean_exists
    if clean_exists:
        clean = load_csv(clean_path)
        results["clean_total_rows"] = len(clean)
        clean_cols = list(clean[0].keys()) if clean else []

        missing_checks = {}
        for field in ["title", "company_name", "job_url", "description", "publication_date"]:
            missing_checks[f"missing_{field}_pct"] = check_missing_percent(clean, field)

        results["missing_value_checks"] = missing_checks
        results["remote_status_counts"] = {}
        statuses = set()
        for r in clean:
            s = r.get("remote_status", "").strip()
            statuses.add(s)
            results["remote_status_counts"][s] = results["remote_status_counts"].get(s, 0) + 1
        valid_statuses = {"Remote", "On-site", "Hybrid", "Unknown", ""}
        results["remote_status_valid"] = all(s in valid_statuses for s in statuses if s)

        date_invalid = check_valid_dates(clean, "publication_date")
        results["invalid_dates"] = date_invalid

        salary_zero = sum(1 for r in clean if (r.get("salary_min_raw") and float(r["salary_min_raw"]) == 0) or (r.get("salary_max_raw") and float(r["salary_max_raw"]) == 0))
        results["salary_zeros_converted"] = salary_zero

        brackets = {}
        for r in clean:
            b = r.get("experience_bracket", "Not mentioned").strip()
            brackets[b] = brackets.get(b, 0) + 1
        results["experience_brackets"] = brackets

        sources = {}
        for r in clean:
            s = r.get("source", "")
            sources[s] = sources.get(s, 0) + 1
        results["source_counts"] = sources

    results["output_file_check"] = clean_exists

    out_path = BASE_DIR / "output" / "validation_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[VALIDATE] Results saved to {out_path}")
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    validate()
