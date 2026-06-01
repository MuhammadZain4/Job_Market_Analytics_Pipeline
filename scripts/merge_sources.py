import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
MERGE_DIR = BASE_DIR / "data" / "merged"

def clean_html(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def parse_date(date_val, source):
    if not date_val:
        return None
    try:
        if source == "RemoteOK" and isinstance(date_val, (int, float)):
            return datetime.fromtimestamp(date_val, tz=timezone.utc).strftime("%Y-%m-%d")
    except: pass
    for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%B %d, %Y"]:
        try:
            return datetime.strptime(str(date_val)[:10], fmt).strftime("%Y-%m-%d")
        except: pass
    try:
        return str(date_val)[:10]
    except:
        return None

def extract_salary_from_raw(job, source):
    min_s, max_s, curr = None, None, None
    text = job.get("salary_text_raw") or job.get("description") or ""
    text = str(text)
    if source == "RemoteOK":
        s_min = job.get("salary_min")
        s_max = job.get("salary_max")
        if s_min and s_min != "0" and s_min != 0:
            try:
                min_s = float(s_min)
                max_s = float(s_max) if s_max else None
                curr = "USD"
                return min_s, max_s, curr
            except: pass
    if source == "RemoteJobs.org":
        s_min = job.get("salary_min")
        s_max = job.get("salary_max")
        if s_min:
            try: min_s = float(s_min); max_s = float(s_max) if s_max else None; curr = "USD"; return min_s, max_s, curr
            except: pass
    patterns = [
        (r'(?:USD|\$)\s*([\d,]+)\s*[-–to]+\s*([\d,]+)\s*(?:k|K)?\s*a\s*year', "USD"),
        (r'(?:EUR|€)\s*([\d,]+)\s*[-–to]+\s*([\d,]+)\s*(?:k|K)?\s*a\s*year', "EUR"),
        (r'(?:GBP|£)\s*([\d,]+)\s*[-–to]+\s*([\d,]+)\s*(?:k|K)?\s*a\s*year', "GBP"),
        (r'\$([\d,]+)\s*[-–]+\s*\$([\d,]+)', "USD"),
    ]
    for pat, c in patterns:
        m = re.search(pat, text)
        if m:
            try:
                min_s = float(m.group(1).replace(",", ""))
                max_s = float(m.group(2).replace(",", "")) if m.lastindex >= 2 else None
                curr = c
                return min_s, max_s, curr
            except: pass
    return None, None, None

def map_arbeitnow(job):
    return {
        "source": "Arbeitnow",
        "job_id": str(job.get("id", "")),
        "title": job.get("title", ""),
        "company_name": job.get("company_name", ""),
        "location_raw": job.get("location", ""),
        "remote_status": "Remote" if job.get("remote") else "On-site",
        "job_type": job.get("job_types", [None])[0] if isinstance(job.get("job_types"), list) else "",
        "category_raw": ", ".join(job.get("tags", [])) if isinstance(job.get("tags"), list) else str(job.get("tags", "")),
        "tags_raw": ", ".join(job.get("tags", [])) if isinstance(job.get("tags"), list) else "",
        "description": clean_html(job.get("description", "")),
        "publication_date": parse_date(job.get("created_at"), "Arbeitnow"),
        "job_url": job.get("url", ""),
        "salary_text_raw": "",
        "salary_min_raw": None,
        "salary_max_raw": None,
        "currency_raw": None,
        "salary_min_usd": None,
        "salary_max_usd": None,
        "salary_mid_usd": None,
        "experience_years_min": None,
        "experience_years_max": None,
        "experience_bracket": "Not mentioned",
        "extracted_skills": "",
        "job_category_clean": "",
        "scrape_date": job.get("_scrape_date", ""),
    }

def map_remoteok(job):
    desc = clean_html(job.get("description", ""))
    return {
        "source": "RemoteOK",
        "job_id": str(job.get("id", "")),
        "title": job.get("position", ""),
        "company_name": job.get("company", ""),
        "location_raw": job.get("location", ""),
        "remote_status": "Remote",
        "job_type": "Full-time",
        "category_raw": ", ".join(job.get("tags", [])) if isinstance(job.get("tags"), list) else str(job.get("tags", "")),
        "tags_raw": ", ".join(job.get("tags", [])) if isinstance(job.get("tags"), list) else "",
        "description": desc,
        "publication_date": parse_date(job.get("date"), "RemoteOK"),
        "job_url": job.get("url", ""),
        "salary_text_raw": f"{job.get('salary_min', '')} - {job.get('salary_max', '')} USD" if job.get("salary_min") else "",
        "salary_min_raw": job.get("salary_min"),
        "salary_max_raw": job.get("salary_max"),
        "currency_raw": "USD" if job.get("salary_min") else None,
        "salary_min_usd": float(job["salary_min"]) if job.get("salary_min") else None,
        "salary_max_usd": float(job["salary_max"]) if job.get("salary_max") else None,
        "salary_mid_usd": ((float(job["salary_min"]) + float(job["salary_max"])) / 2) if job.get("salary_min") and job.get("salary_max") else None,
        "experience_years_min": None,
        "experience_years_max": None,
        "experience_bracket": "Not mentioned",
        "extracted_skills": "",
        "job_category_clean": "",
        "scrape_date": job.get("_scrape_date", ""),
    }

def map_himalayas(job):
    desc = clean_html(job.get("description", ""))
    sal_min, sal_max, curr = extract_salary_from_raw(job, "Himalayas")
    return {
        "source": "Himalayas",
        "job_id": str(job.get("id", "") or job.get("applicationLink", "")),
        "title": job.get("title", ""),
        "company_name": job.get("companyName", ""),
        "location_raw": job.get("location", "") or job.get("locationRestrictions", ""),
        "remote_status": "Remote",
        "job_type": job.get("employmentType", ""),
        "category_raw": ", ".join(job.get("categories", [])) if isinstance(job.get("categories"), list) else "",
        "tags_raw": ", ".join(job.get("skills", [])) if isinstance(job.get("skills"), list) else "",
        "description": desc,
        "publication_date": parse_date(job.get("postedAt", job.get("date", "")), "Himalayas"),
        "job_url": job.get("applicationLink", job.get("url", "")),
        "salary_text_raw": job.get("salary", "") or "",
        "salary_min_raw": sal_min,
        "salary_max_raw": sal_max,
        "currency_raw": curr,
        "salary_min_usd": None,
        "salary_max_usd": None,
        "salary_mid_usd": None,
        "experience_years_min": None,
        "experience_years_max": None,
        "experience_bracket": "Not mentioned",
        "extracted_skills": "",
        "job_category_clean": "",
        "scrape_date": job.get("_scrape_date", ""),
    }

def map_remotejobs(job):
    desc = clean_html(job.get("description", "") or job.get("content", ""))
    sal_min, sal_max, curr = extract_salary_from_raw(job, "RemoteJobs.org")
    company = job.get("company", {})
    if isinstance(company, dict):
        company_name = company.get("name", "")
    else:
        company_name = str(company) if company else ""
    location = job.get("location", "") or job.get("locations", "")
    return {
        "source": "RemoteJobs.org",
        "job_id": str(job.get("id", "")),
        "title": job.get("title", ""),
        "company_name": company_name,
        "location_raw": location,
        "remote_status": "Remote",
        "job_type": job.get("type", job.get("employmentType", "")),
        "category_raw": job.get("category", "") or job.get("_query_category", ""),
        "tags_raw": ", ".join(job.get("skills", [])) if isinstance(job.get("skills"), list) else job.get("skills", ""),
        "description": desc,
        "publication_date": parse_date(job.get("publication_date", job.get("date", job.get("createdAt", ""))), "RemoteJobs.org"),
        "job_url": job.get("url", job.get("apply_url", "")),
        "salary_text_raw": job.get("salary", "") or job.get("salary_text", "") or "",
        "salary_min_raw": job.get("salary_min") or sal_min,
        "salary_max_raw": job.get("salary_max") or sal_max,
        "currency_raw": job.get("salary_currency") or curr or "USD",
        "salary_min_usd": None,
        "salary_max_usd": None,
        "salary_mid_usd": None,
        "experience_years_min": None,
        "experience_years_max": None,
        "experience_bracket": "Not mentioned",
        "extracted_skills": "",
        "job_category_clean": "",
        "scrape_date": job.get("_scrape_date", ""),
    }

STANDARD_FIELDS = [
    "source", "job_id", "title", "company_name", "location_raw", "remote_status",
    "job_type", "category_raw", "tags_raw", "description", "publication_date",
    "job_url", "salary_text_raw", "salary_min_raw", "salary_max_raw", "currency_raw",
    "salary_min_usd", "salary_max_usd", "salary_mid_usd",
    "experience_years_min", "experience_years_max", "experience_bracket",
    "extracted_skills", "job_category_clean", "scrape_date",
]

MAPPERS = {
    "Arbeitnow": map_arbeitnow,
    "RemoteOK": map_remoteok,
    "Himalayas": map_himalayas,
    "RemoteJobs.org": map_remotejobs,
}

def main():
    MERGE_DIR.mkdir(parents=True, exist_ok=True)
    all_standardized = []
    source_counts = {}

    for source_name, mapper in MAPPERS.items():
        raw_file = RAW_DIR / f"raw_{source_name.lower().replace('.', '').replace('-', '_')}_jobs.csv"
        raw_file_alt = RAW_DIR / f"raw_{source_name.lower().replace('.org', '').replace('-', '_')}_jobs.csv"
        actual_file = raw_file if raw_file.exists() else raw_file_alt
        if not actual_file.exists():
            print(f"[WARN] Raw file not found for {source_name} at {actual_file}")
            continue
        count = 0
        with open(actual_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                std = mapper(row)
                all_standardized.append(std)
                count += 1
        source_counts[source_name] = count
        print(f"[MERGE] {source_name}: {count} records")

    out_path = MERGE_DIR / "merged_raw_jobs.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=STANDARD_FIELDS)
        writer.writeheader()
        writer.writerows(all_standardized)

    print(f"[MERGE] Total merged: {len(all_standardized)} -> {out_path}")
    print(f"[MERGE] Source counts: {source_counts}")

if __name__ == "__main__":
    main()
