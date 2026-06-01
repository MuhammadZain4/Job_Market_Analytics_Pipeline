"""
KNIME Cleaning Reference Script
--------------------------------
This script performs the same cleaning, transformation, and filtering that
the KNIME workflow should do. Use it to:
  1. Verify the expected output
  2. Understand each step for replicating in KNIME
  3. Generate clean_ai_ml_data_jobs.csv and metrics

Steps mirror the KNIME workflow node-by-node.
"""

import csv
import json
import re
import os
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "scripts"))

# ── 1. Read merged raw dataset ──────────────────────────────────────
INPUT_PATH = BASE_DIR / "data" / "merged" / "merged_raw_jobs.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

rows = load_csv(INPUT_PATH)
print(f"[STEP 1] Loaded {len(rows)} merged records")

# ── 2. Remove/fix HTML, special symbols, whitespace ────────────────
def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", str(text))
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

for r in rows:
    r["title"] = r.get("title", "").strip()
    r["company_name"] = r.get("company_name", "").strip()
    r["location_raw"] = r.get("location_raw", "").strip()
    r["description"] = clean_text(r.get("description", ""))
    r["category_raw"] = r.get("category_raw", "").strip()
    r["tags_raw"] = r.get("tags_raw", "").strip()

print(f"[STEP 2] HTML/symbol cleaning done")

# ── 3. Standardize title, company, location, job_type, dates ───────
for r in rows:
    # Job type standardization
    jt = r.get("job_type", "").lower()
    if any(w in jt for w in ["full", "permanent", ""]):
        r["job_type"] = "Full-time"
    elif any(w in jt for w in ["part"]):
        r["job_type"] = "Part-time"
    elif any(w in jt for w in ["contract"]):
        r["job_type"] = "Contract"
    elif any(w in jt for w in ["freelance", "temporary"]):
        r["job_type"] = "Freelance"
    elif any(w in jt for w in ["intern"]):
        r["job_type"] = "Internship"
    else:
        r["job_type"] = "Full-time"

print(f"[STEP 3] Standardization done")

# ── 4. Deduplicate ─────────────────────────────────────────────────
before_dedup = len(rows)
seen = set()
deduped = []
for r in rows:
    dedup_key = f"{r.get('source', '')}|{r.get('job_url', '')}|{r.get('title', '')}|{r.get('company_name', '')}"
    if dedup_key not in seen:
        seen.add(dedup_key)
        deduped.append(r)
rows = deduped
print(f"[STEP 4] Dedup: {before_dedup} -> {len(rows)} ({before_dedup - len(rows)} removed)")

# ── 5. AI/ML/Data relevance filter ─────────────────────────────────
RELEVANT_KEYWORDS = [
    "data analyst", "data analytics", "reporting analyst", "product analyst", "marketing analytics",
    "data scientist", "statistical modeling", "predictive modeling", "experimentation", "nlp",
    "data engineer", "etl", "elt", "data pipeline", "warehouse", "lakehouse", "dbt", "airflow",
    "machine learning", "ml engineer", "ai engineer", "deep learning", "llm", "computer vision", "mlops",
    "bi analyst", "business intelligence", "power bi", "tableau", "dashboard developer",
    "analytics engineer", "semantic layer", "metrics layer", "data modeling",
    "data science", "data engineering", "ai/ml", "bi", "data",
]

def is_relevant(row):
    text = " ".join([
        row.get("title", "").lower(),
        row.get("description", "").lower(),
        row.get("tags_raw", "").lower(),
        row.get("category_raw", "").lower(),
    ])
    return any(kw in text for kw in RELEVANT_KEYWORDS)

before_filter = len(rows)
rows = [r for r in rows if is_relevant(r)]
after_filter = len(rows)
print(f"[STEP 5] AI/ML filter: {before_filter} -> {after_filter} ({before_filter - after_filter} removed)")

# ── 6. Extract and standardize skills ──────────────────────────────
SKILL_KEYWORDS = {
    "Python", "SQL", "Tableau", "Power BI", "Machine Learning", "Deep Learning",
    "NLP", "Computer Vision", "LLM", "TensorFlow", "PyTorch", "scikit-learn",
    "Pandas", "NumPy", "Spark", "Hadoop", "Airflow", "dbt", "Kafka", "Flink",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git", "Linux",
    "Snowflake", "BigQuery", "Redshift", "Databricks", "PostgreSQL", "MySQL",
    "MongoDB", "Cassandra", "Elasticsearch", "Excel", "R", "MATLAB",
    "Statistics", "Probability", "Linear Algebra", "Calculus",
    "Data Visualization", "Dashboard", "ETL", "API", "REST", "GraphQL",
    "CI/CD", "Agile", "Scrum", "Communication",
}

def extract_skills(row):
    text = " ".join([
        row.get("title", "").lower(),
        row.get("description", "").lower(),
        row.get("tags_raw", "").lower(),
        row.get("extracted_skills", "").lower(),
    ])
    found = []
    for skill in SKILL_KEYWORDS:
        if skill.lower() in text:
            found.append(skill)
    return ", ".join(sorted(set(found)))

for r in rows:
    r["extracted_skills"] = extract_skills(r)

print(f"[STEP 6] Skill extraction done")

# ── 7. Job category classification ─────────────────────────────────
def classify_job(row):
    title = row.get("title", "").lower()
    desc = row.get("description", "").lower()
    text = title + " " + desc
    if any(w in text for w in ["data analyst", "data analytics", "reporting analyst", "product analyst", "marketing analytics", "analyst"]):
        return "Data Analytics"
    if any(w in text for w in ["data scientist", "data science", "statistical modeling", "predictive modeling", "experimentation", "nlp", "machine learning scientist"]):
        return "Data Science"
    if any(w in text for w in ["data engineer", "etl", "elt", "data pipeline", "warehouse", "lakehouse", "data architect"]):
        return "Data Engineering"
    if any(w in text for w in ["machine learning", "ml engineer", "ai engineer", "deep learning", "llm", "computer vision", "mlops", "ai/ml"]):
        return "AI/ML"
    if any(w in text for w in ["business intelligence", "bi analyst", "power bi", "tableau", "dashboard developer", "bi developer"]):
        return "BI"
    if any(w in text for w in ["analytics engineer", "analytics engineering", "dbt", "semantic layer", "metrics layer", "data modeling"]):
        return "Analytics Engineering"
    return "Other Data"

for r in rows:
    r["job_category_clean"] = classify_job(r)

print(f"[STEP 7] Job classification done")

# ── 8. Standardize remote_status ───────────────────────────────────
for r in rows:
    rs = r.get("remote_status", "").strip().lower()
    if rs in ["remote", "yes", "true", "1"]:
        r["remote_status"] = "Remote"
    elif rs in ["on-site", "onsite", "no", "false", "0", "on site"]:
        r["remote_status"] = "On-site"
    elif rs in ["hybrid"]:
        r["remote_status"] = "Hybrid"
    else:
        r["remote_status"] = "Unknown"

print(f"[STEP 8] Remote status standardized")

# ── 9. Experience years extraction and bracket ─────────────────────
EXPERIENCE_PATTERNS = [
    (r"(\d+)\s*[+-]\+?\s*years?", "min"),
    (r"(\d+)\s*[-–to]+\s*(\d+)\s*years?", "range"),
    (r"(\d+)\s*years?\s*(?:of)?\s*(?:experience)?", "min"),
]

def extract_experience(row):
    text = f"{row.get('title', '')} {row.get('description', '')}".lower()
    title_lower = row.get("title", "").lower()
    desc_lower = row.get("description", "").lower()

    min_y = None
    max_y = None

    for pat, kind in EXPERIENCE_PATTERNS:
        m = re.search(pat, text)
        if m:
            if kind == "range":
                min_y = int(m.group(1))
                max_y = int(m.group(2))
            else:
                val = int(m.group(1))
                min_y = val
                max_y = val + 2
            break

    if min_y is None:
        if any(w in text for w in ["entry level", "entry-level", "fresh graduate", "new grad", "internship", "trainee", "junior"]):
            min_y, max_y = 0, 1
        elif any(w in title_lower for w in ["senior", "lead", "principal", "staff", "director", "head of", "chief"]):
            min_y, max_y = 5, 10
        elif any(w in title_lower for w in ["mid"]):
            min_y, max_y = 2, 5

    return min_y, max_y

def bracket(min_y, max_y):
    if min_y is None:
        return "Not mentioned"
    if max_y is not None and max_y <= 1:
        return "0-1"
    if max_y is not None:
        if max_y <= 3: return "1-3"
        if max_y <= 5: return "3-5"
        if max_y <= 8: return "5-8"
        return "8+"
    if min_y <= 1: return "0-1"
    if min_y <= 3: return "1-3"
    if min_y <= 5: return "3-5"
    if min_y <= 8: return "5-8"
    return "8+"

for r in rows:
    min_y, max_y = extract_experience(r)
    r["experience_years_min"] = min_y
    r["experience_years_max"] = max_y
    r["experience_bracket"] = bracket(min_y, max_y)

print(f"[STEP 9] Experience bracket extraction done")

# ── 10. Salary extraction + USD conversion ─────────────────────────
from currency_utils import fetch_latest_rates, convert_to_usd, parse_salary_text, detect_currency

fetch_latest_rates()

PERIOD_MULTIPLIER = {
    "year": 1, "annual": 1, "annually": 1, "yr": 1,
    "month": 12, "monthly": 12,
    "hour": 2080, "hr": 2080, "per hour": 2080,
    "week": 52, "weekly": 52,
    "day": 260,
}

def extract_salary(row):
    text = f"{row.get('salary_text_raw', '')} {row.get('description', '')}".strip()

    # Structured fields
    s_min = row.get("salary_min_raw")
    s_max = row.get("salary_max_raw")
    currency = row.get("currency_raw")

    if s_min and s_min not in ("", "0", "0.0", 0, "0.00"):
        try:
            min_val = float(s_min)
            max_val = float(s_max) if s_max and s_max not in ("", "0", 0) else None
            cur = currency or "USD"
            return min_val, max_val, cur
        except:
            pass

    # Parse from text
    min_val, max_val, cur = None, None, None
    period = "year"

    # Try range patterns
    range_pats = [
        (r"(\d[\d,]*)\s*[-–to]+\s*(\d[\d,]*)\s*(?:k|K)?\s*(?:a\s+year|per\s+year|annually|/yr|/year|annual|p\.?a\.?)", "year"),
        (r"(\d[\d,]*)\s*[-–to]+\s*(\d[\d,]*)\s*(?:k|K)?\s*(?:per\s+hour|/hr|/hour|an\s+hour|hourly)", "hour"),
        (r"(\d[\d,]*)\s*[-–to]+\s*(\d[\d,]*)\s*(?:k|K)?\s*(?:per\s+month|/month|monthly)", "month"),
    ]
    for pat, prd in range_pats:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            min_val = float(m.group(1).replace(",", ""))
            max_val = float(m.group(2).replace(",", ""))
            period = prd
            break

    if min_val is None:
        single_pats = [
            (r"(\d[\d,]*)\s*(?:k|K)?\s*(?:a\s+year|per\s+year|annually|/yr|annual|p\.?a\.?)", "year"),
            (r"(\d[\d,]*)\s*(?:k|K)?\s*(?:per\s+hour|/hr|hourly)", "hour"),
        ]
        for pat, prd in single_pats:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                min_val = float(m.group(1).replace(",", ""))
                max_val = min_val
                period = prd
                break

    if min_val is None:
        return None, None, None

    # Detect currency from text
    cur = detect_currency(text) or "USD"

    # Handle k multipliers
    if "k" in text.lower() and min_val < 1000:
        min_val *= 1000
        if max_val: max_val *= 1000

    # Convert to annual
    mult = PERIOD_MULTIPLIER.get(period, 1)
    min_annual = min_val * mult
    max_annual = max_val * mult if max_val else None

    # Convert to USD
    min_usd = convert_to_usd(min_annual, cur)
    max_usd = convert_to_usd(max_annual, cur) if max_annual else None

    return min_annual, max_annual, cur

SALARY_CAP_USD = 500_000

for r in rows:
    min_a, max_a, cur = extract_salary(r)
    r["salary_min_raw"] = min_a
    r["salary_max_raw"] = max_a
    r["currency_raw"] = cur
    if min_a and max_a:
        min_usd = convert_to_usd(min_a, cur) if cur else None
        max_usd = convert_to_usd(max_a, cur) if cur else None
        mid = ((min_usd or 0) + (max_usd or 0)) / 2 if (min_usd or max_usd) else None
        if mid and mid > SALARY_CAP_USD:
            min_usd, max_usd, mid = None, None, None
        r["salary_min_usd"] = min_usd
        r["salary_max_usd"] = max_usd
        r["salary_mid_usd"] = round(mid, 2) if mid else None
    else:
        r["salary_min_usd"] = None
        r["salary_max_usd"] = None
        r["salary_mid_usd"] = None

print(f"[STEP 10] Salary extraction done")

# ── 11. Write final clean CSV ──────────────────────────────────────
CLEAN_PATH = OUTPUT_DIR / "clean_ai_ml_data_jobs.csv"
FIELD_NAMES = [
    "source", "job_id", "title", "company_name", "location_raw", "remote_status",
    "job_type", "category_raw", "tags_raw", "description", "publication_date",
    "job_url", "salary_text_raw", "salary_min_raw", "salary_max_raw", "currency_raw",
    "salary_min_usd", "salary_max_usd", "salary_mid_usd",
    "experience_years_min", "experience_years_max", "experience_bracket",
    "extracted_skills", "job_category_clean", "scrape_date",
]

with open(CLEAN_PATH, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELD_NAMES)
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in FIELD_NAMES})

print(f"[STEP 11] Clean CSV written: {CLEAN_PATH} ({len(rows)} rows)")

# ── Summary Stats ──────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"CLEAN DATASET SUMMARY")
print(f"{'='*60}")
print(f"Total rows: {len(rows)}")
src_cnt = Counter(r["source"] for r in rows)
print(f"By source: {dict(src_cnt)}")
rem_cnt = Counter(r["remote_status"] for r in rows)
print(f"Remote status: {dict(rem_cnt)}")
bkt_cnt = Counter(r["experience_bracket"] for r in rows)
print(f"Experience brackets: {dict(bkt_cnt)}")
cat_cnt = Counter(r["job_category_clean"] for r in rows)
print(f"Job categories: {dict(cat_cnt)}")
salaries = [float(r["salary_mid_usd"]) for r in rows if r.get("salary_mid_usd")]
if salaries:
    print(f"Average salary (USD): ${sum(salaries)/len(salaries):.2f} (from {len(salaries)} records)")
    print(f"Salary range: ${min(salaries):.2f} - ${max(salaries):.2f}")

print(f"\n[COMPLETE] KNIME reference cleaning done.")
