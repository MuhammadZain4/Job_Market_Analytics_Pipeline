import json
import requests
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
METRICS_PATH = BASE_DIR / "output" / "metrics_summary.json"

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook-test/job-market-alert")

def main():
    if not METRICS_PATH.exists():
        print(f"[N8N] Metrics file not found at {METRICS_PATH}")
        return

    with open(METRICS_PATH, "r") as f:
        metrics = json.load(f)

    payload = {
        "pipeline_status": "Success",
        "pipeline_name": "Job Market Analytics Pipeline",
        "total_cleaned_jobs": metrics.get("total_clean", 0),
        "jobs_by_source": metrics.get("clean_by_source", {}),
        "remote_status_ratio": metrics.get("remote_status_ratios", {}),
        "zero_one_year_jobs": metrics.get("zero_one_year_jobs", 0),
        "average_salary_usd": metrics.get("avg_salary_usd_overall", "N/A"),
        "top_skills": metrics.get("top_skills", [])[:5],
        "experience_brackets": metrics.get("experience_brackets", {}),
        "top_source": metrics.get("top_source", ""),
        "analysis_date": metrics.get("analysis_date", ""),
    }

    try:
        resp = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=15)
        print(f"[N8N] Webhook sent. Status: {resp.status_code}")
        print(f"[N8N] Response: {resp.text[:200]}")
    except requests.RequestException as e:
        print(f"[N8N] Webhook error: {e}")
        print("[N8N] Metrics payload saved locally for manual n8n trigger.")
        fallback = BASE_DIR / "output" / "n8n_payload.json"
        with open(fallback, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"[N8N] Payload saved to {fallback}")

if __name__ == "__main__":
    main()
