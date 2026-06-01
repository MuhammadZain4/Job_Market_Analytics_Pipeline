import requests
import csv
import os
import json
from datetime import datetime, timezone
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
SOURCE_NAME = "RemoteOK"
API_URL = "https://remoteok.com/api"

def extract():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    scrape_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    try:
        resp = requests.get(API_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        resp.raise_for_status()
        jobs = resp.json()
    except requests.RequestException as e:
        print(f"[{SOURCE_NAME}] Error: {e}")
        return

    # First item is usually metadata — skip if it's not a job dict
    all_jobs = []
    for j in jobs:
        if isinstance(j, dict) and j.get("id") and j.get("position"):
            row = dict(j)
            row["_source"] = SOURCE_NAME
            row["_scrape_date"] = scrape_ts
            all_jobs.append(row)

    if not all_jobs:
        print(f"[{SOURCE_NAME}] No jobs extracted.")
        return

    fieldnames = list(all_jobs[0].keys())
    out_path = RAW_DIR / "raw_remoteok_jobs.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_jobs)

    print(f"[{SOURCE_NAME}] Extracted {len(all_jobs)} jobs -> {out_path}")

if __name__ == "__main__":
    extract()
