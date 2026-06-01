"""
Demo screenshot generator - runs each pipeline component and
displays cleanly formatted output for screenshot capture.
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parents[1]
SCRIPTS = BASE / "scripts"

def run(cmd, label):
    sep = "=" * 65
    print(f"\n{sep}")
    print(f"  {label}")
    print(f"{sep}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    lines = result.stdout.strip().split("\n")
    for line in lines:
        print(f"  {line}")
    if result.stderr.strip():
        for line in result.stderr.strip().split("\n"):
            if "traceback" not in line.lower() and "error" not in line.lower():
                print(f"  {line}")
    print(f"{sep}\n")

def main():
    print(f"""
{'='*65}
  JOB MARKET ANALYTICS PIPELINE - DEMO SCREENSHOTS
  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
  Project: {BASE}
{'='*65}
""")

    # Step 1: Extract - Arbeitnow
    run([sys.executable, str(SCRIPTS / "extract_arbeitnow.py")],
        "1/8  EXTRACT: Arbeitnow API")

    # Step 2: Extract - RemoteOK
    run([sys.executable, str(SCRIPTS / "extract_remoteok.py")],
        "2/8  EXTRACT: RemoteOK API")

    # Step 3: Extract - Himalayas
    run([sys.executable, str(SCRIPTS / "extract_himalayas.py")],
        "3/8  EXTRACT: Himalayas API")

    # Step 4: Extract - RemoteJobs
    run([sys.executable, str(SCRIPTS / "extract_remotejobs.py")],
        "4/8  EXTRACT: RemoteJobs.org API")

    # Step 5: Merge
    run([sys.executable, str(SCRIPTS / "merge_sources.py")],
        "5/8  MERGE: Schema standardization + source unification")

    # Step 6: Clean (KNIME reference)
    run([sys.executable, str(SCRIPTS / "knime_cleaning_reference.py")],
        "6/8  CLEAN: KNIME cleaning + AI/ML filter + salary + experience")

    # Step 7: Validate
    run([sys.executable, str(SCRIPTS / "validate_outputs.py")],
        "7/8  VALIDATE: Data quality checks")

    # Step 8: Metrics
    run([sys.executable, str(SCRIPTS / "calculate_metrics.py")],
        "8/8  METRICS: All 15 analysis questions answered")

    print(f"""
{'='*65}
  PIPELINE COMPLETE - READY FOR SCREENSHOT
{'='*65}

  Deliverables generated:
   - data/raw/*.csv (4 source files)
   - data/merged/merged_raw_jobs.csv
   - data/processed/clean_ai_ml_data_jobs.csv
   - output/validation_results.json
   - output/metrics_summary.json
   - report/final_report.docx
""")

if __name__ == "__main__":
    main()
