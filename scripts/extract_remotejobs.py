import requests
import csv
import os
from datetime import datetime, timezone
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
SOURCE_NAME = "RemoteJobs.org"
API_URL = "https://remotejobs.org/api/v1/jobs"

def extract():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    all_jobs = []
    page = 1
    max_pages = 5
    scrape_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    categories = ["data-science", "data-analytics", "data-engineering", "machine-learning", "business-intelligence"]

    for cat in categories:
        page = 1
        while page <= max_pages:
            try:
                params = {"category": cat, "limit": 50, "page": page}
                resp = requests.get(API_URL, params=params, timeout=30)
                resp.raise_for_status()
                raw = resp.json()
                jobs = raw.get("data", []) if isinstance(raw, dict) else raw
                if not jobs or not isinstance(jobs, list):
                    break
                for j in jobs:
                    if isinstance(j, dict):
                        j["_source"] = SOURCE_NAME
                        j["_scrape_date"] = scrape_ts
                        j["_query_category"] = cat
                        all_jobs.append(j)
                page += 1
            except requests.RequestException as e:
                print(f"[{SOURCE_NAME}] Error category={cat} page={page}: {e}")
                break

    if not all_jobs:
        print(f"[{SOURCE_NAME}] No jobs extracted.")
        return

    out_path = RAW_DIR / "raw_remotejobs_jobs.csv"
    fieldnames = list(all_jobs[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_jobs)

    print(f"[{SOURCE_NAME}] Extracted {len(all_jobs)} jobs -> {out_path}")

if __name__ == "__main__":
    extract()
