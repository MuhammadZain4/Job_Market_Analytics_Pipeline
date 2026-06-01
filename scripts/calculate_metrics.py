import csv
import json
import os
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parents[1]
CLEAN_PATH = BASE_DIR / "data" / "processed" / "clean_ai_ml_data_jobs.csv"
MERGED_PATH = BASE_DIR / "data" / "merged" / "merged_raw_jobs.csv"

def load_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def safe_float(val):
    if val is None:
        return None
    try:
        v = float(str(val).replace(",", "").strip())
        return v if v > 0 else None
    except:
        return None

def calculate():
    metrics = {}

    merged = load_csv(MERGED_PATH) if MERGED_PATH.exists() else []
    clean = load_csv(CLEAN_PATH) if CLEAN_PATH.exists() else []

    # Q1: Total jobs by source before filtering
    raw_counts = Counter(r.get("source", "") for r in merged)
    metrics["total_raw_by_source"] = dict(raw_counts)
    metrics["total_raw"] = len(merged)

    # Q2: Jobs after AI/ML/Data filtering
    metrics["total_clean"] = len(clean)

    # Q3: Highest contributing source
    if clean:
        clean_source_counts = Counter(r.get("source", "") for r in clean)
        metrics["clean_by_source"] = dict(clean_source_counts)
        metrics["top_source"] = clean_source_counts.most_common(1)[0] if clean_source_counts else None

    # Q4: Remote/on-site/hybrid/unknown ratio
    if clean:
        remote_counts = Counter(r.get("remote_status", "Unknown") for r in clean)
        metrics["remote_status_counts"] = dict(remote_counts)
        metrics["remote_status_ratios"] = {k: round(v / len(clean) * 100, 1) for k, v in remote_counts.items()}

    # Q5: Remote/on-site by source
    if clean:
        remote_by_source = {}
        for r in clean:
            src = r.get("source", "")
            status = r.get("remote_status", "Unknown")
            if src not in remote_by_source:
                remote_by_source[src] = {}
            remote_by_source[src][status] = remote_by_source[src].get(status, 0) + 1
        metrics["remote_by_source"] = remote_by_source

    # Q6: 0-1 year jobs
    if clean:
        zero_one = [r for r in clean if r.get("experience_bracket", "").strip() == "0-1"]
        metrics["zero_one_year_jobs"] = len(zero_one)

    # Q7: Experience bracket distribution
    if clean:
        bracket_counts = Counter(r.get("experience_bracket", "Not mentioned") for r in clean)
        metrics["experience_brackets"] = dict(bracket_counts)
        metrics["experience_bracket_pcts"] = {k: round(v / len(clean) * 100, 1) for k, v in bracket_counts.items()}

    # Q8: Average salary overall
    if clean:
        salaries = [safe_float(r.get("salary_mid_usd")) for r in clean]
        salaries = [s for s in salaries if s is not None]
        metrics["avg_salary_usd_overall"] = round(sum(salaries) / len(salaries), 2) if salaries else None
        metrics["salary_count"] = len(salaries)
        metrics["salary_coverage_pct"] = round(len(salaries) / len(clean) * 100, 1) if clean else 0

    # Q9: Average salary by job category
    if clean:
        cat_salaries = {}
        for r in clean:
            cat = r.get("job_category_clean", "Unknown").strip() or "Unknown"
            sal = safe_float(r.get("salary_mid_usd"))
            if sal is not None:
                if cat not in cat_salaries:
                    cat_salaries[cat] = []
                cat_salaries[cat].append(sal)
        metrics["avg_salary_by_category"] = {k: round(sum(v) / len(v), 2) for k, v in cat_salaries.items()}

    # Q10: Average salary by experience bracket
    if clean:
        bracket_salaries = {}
        for r in clean:
            br = r.get("experience_bracket", "Not mentioned").strip()
            sal = safe_float(r.get("salary_mid_usd"))
            if sal is not None:
                if br not in bracket_salaries:
                    bracket_salaries[br] = []
                bracket_salaries[br].append(sal)
        metrics["avg_salary_by_bracket"] = {k: round(sum(v) / len(v), 2) for k, v in bracket_salaries.items()}

    # Q11: Most frequent skills
    if clean:
        all_skills = []
        for r in clean:
            skills = r.get("extracted_skills", "")
            for s in skills.split(","):
                s = s.strip()
                if s and len(s) > 1:
                    all_skills.append(s)
        metrics["top_skills"] = Counter(all_skills).most_common(20)

    # Q12: Top companies
    if clean:
        companies = Counter(r.get("company_name", "").strip() for r in clean if r.get("company_name", "").strip())
        metrics["top_companies"] = companies.most_common(20)

    # Q13: Job category distribution
    if clean:
        cat_counts = Counter(r.get("job_category_clean", "Unknown").strip() or "Unknown" for r in clean)
        metrics["job_category_counts"] = dict(cat_counts)

    # Q14: Salary coverage by source
    if clean:
        source_salaries = {}
        for r in clean:
            src = r.get("source", "")
            sal = safe_float(r.get("salary_mid_usd"))
            if src not in source_salaries:
                source_salaries[src] = {"total": 0, "with_salary": 0}
            source_salaries[src]["total"] += 1
            if sal is not None:
                source_salaries[src]["with_salary"] += 1
        metrics["salary_coverage_by_source"] = {
            k: round(v["with_salary"] / v["total"] * 100, 1) if v["total"] else 0
            for k, v in source_salaries.items()
        }

    # Q15: Data quality issues summary
    quality_issues = []
    if merged:
        missing_titles = sum(1 for r in merged if not r.get("title", "").strip())
        quality_issues.append(f"{missing_titles} records missing title in merged data")
    if clean:
        null_salaries = sum(1 for r in clean if not r.get("salary_mid_usd", "").strip())
        quality_issues.append(f"{null_salaries} records without salary data")
        null_bracket = sum(1 for r in clean if r.get("experience_bracket", "").strip() == "Not mentioned")
        quality_issues.append(f"{null_bracket} records without experience bracket")
    metrics["data_quality_issues"] = quality_issues

    # Additional: scraping timestamp
    metrics["analysis_date"] = "2026-05-17"

    out_path = BASE_DIR / "output" / "metrics_summary.json"
    with open(out_path, "w") as f:
        json.dump(metrics, f, indent=2)

    metrics_csv = BASE_DIR / "output" / "metrics_summary.csv"
    with open(metrics_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Metric", "Value"])
        for k, v in metrics.items():
            w.writerow([k, json.dumps(v) if isinstance(v, (dict, list)) else str(v)])

    print(f"[METRICS] Saved to {out_path}")
    print(json.dumps(metrics, indent=2, default=str))
    return metrics

if __name__ == "__main__":
    calculate()
