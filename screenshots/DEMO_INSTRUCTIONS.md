# Demo Instructions - Screenshots & Video

## What We've Already Done
The pipeline runs successfully via Python scripts. Screenshots taken so far:
- `screenshots/pipeline_dashboard.png` - HTML dashboard with all metrics

## What You Need to Do in KNIME (Desktop App)

Build the KNIME workflow on your machine following `knime_workflow/KNIME_WORKFLOW_GUIDE.md`, then take these screenshots:

1. **Full workflow** - Capture the entire KNIME canvas
2. **Row counts** - CSV Reader (~2351) vs CSV Writer (~1242)
3. **Rule Engine config** - AI/ML filter expression window
4. **Statistics output** - Salary min/max/mean

Save all to `screenshots/knime/` folder.

## Airflow Demo (If Docker Works)

If Docker is working on your machine (not the `input/output error` issue):

### 1. Start Airflow
```powershell
cd job_market_project
docker compose -f docker-compose-airflow.yml up -d
```

### 2. Open Airflow Web UI
- Go to http://localhost:8080
- Login: `admin` / `admin`
- You'll see the DAG `job_market_analytics_pipeline`

### 3. Trigger the DAG
- Click the play button > "Trigger DAG"
- Watch tasks run: extract_* (parallel) -> merge -> knime_clean -> validate -> calculate_metrics -> trigger_n8n -> archive

### 4. Screenshots to take
- Airflow DAG grid view showing all tasks
- DAG graph view showing task dependencies (parallel arrows)
- A task log (e.g., extract_arbeitnow or calculate_metrics)
- Save to `screenshots/airflow/`

### 5. Stop Airflow
```powershell
docker compose -f docker-compose-airflow.yml down
```

## n8n Demo (If Docker Works)

### 1. Start n8n
```powershell
docker compose -f docker-compose-n8n.yml up -d
```

### 2. Open n8n
- Go to http://localhost:5678
- Create account on first visit

### 3. Import the workflow
- Click "Workflows" > "Import from File"
- Select `n8n/job_market_alert_workflow.json`

### 4. Activate & test
- Click "Save" then toggle "Active" on
- Open a new terminal and run:
  ```powershell
  cd job_market_project
  python scripts/trigger_n8n.py
  ```

### 5. Screenshots to take
- n8n workflow editor showing the full workflow
- n8n execution result (showing the output message)
- Save to `screenshots/n8n/`

### 6. Stop n8n
```powershell
docker compose -f docker-compose-n8n.yml down
```

## Video Recording (Optional)

If your instructor wants a demo video:
1. Open the project in VS Code
2. Start recording (Windows + G to open Game Bar, click Record)
3. Run: `python scripts/demo_screenshots.py`
4. Show the output files in Explorer
5. Stop recording
6. Save as `demo_video.mp4` or similar

## Deliverables Checklist
- [ ] `screenshots/pipeline_dashboard.png` (DONE - Playwright screenshot)
- [ ] `screenshots/knime/knime_full_workflow.png` (you take in KNIME)
- [ ] `screenshots/knime/knime_row_counts.png` (you take in KNIME)
- [ ] `screenshots/knime/knime_rule_engine_filter.png` (you take in KNIME)
- [ ] `screenshots/knime/knime_statistics.png` (you take in KNIME)
- [ ] `data/processed/clean_ai_ml_data_jobs.csv` (DONE - 1242 rows)
- [ ] `output/metrics_summary.json` (DONE - all 15 metrics)
- [ ] `report/final_report.docx` (DONE)

## Quick Verification Command
```powershell
cd job_market_project
python -c "
import csv, json
clean = list(csv.DictReader(open('data/processed/clean_ai_ml_data_jobs.csv', encoding='utf-8')))
m = json.load(open('output/metrics_summary.json'))
print(f'Rows: {len(clean)}, Avg Salary: \${m[\"avg_salary_usd_overall\"]}, Entry-level: {m[\"zero_one_year_jobs\"]}')
"
```
