from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import subprocess
import sys
import os
import requests
import json
import shutil

PROJECT_DIR  = "/opt/airflow/job_market_project"
SCRIPTS_DIR  = "/opt/airflow/job_market_project/scripts"
DATA_RAW     = "/opt/airflow/job_market_project/data/raw"
DATA_MERGED  = "/opt/airflow/job_market_project/data/merged"
DATA_PROC    = "/opt/airflow/job_market_project/data/processed"
DATA_ARCHIVE = "/opt/airflow/job_market_project/data/archive"

N8N_WEBHOOK = "http://host.docker.internal:5678/webhook/job-market-alert"

default_args = {
    "owner": "Muhammad Zain",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

dag = DAG(
    "job_market_analytics_pipeline",
    default_args=default_args,
    description="Job Market Analytics Pipeline - Assignment 3",
    schedule="@daily",
    start_date=datetime(2026, 5, 16),
    catchup=False,
    tags=["assignment3", "job_market"],
)

def run_extract_arbeitnow():
    os.makedirs(DATA_RAW, exist_ok=True)
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, "extract_arbeitnow.py")],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        raise Exception(f"Arbeitnow extraction failed: {result.stderr}")

def run_extract_remoteok():
    os.makedirs(DATA_RAW, exist_ok=True)
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, "extract_remoteok.py")],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        raise Exception(f"RemoteOK extraction failed: {result.stderr}")

def run_extract_himalayas():
    os.makedirs(DATA_RAW, exist_ok=True)
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, "extract_himalayas.py")],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        raise Exception(f"Himalayas extraction failed: {result.stderr}")

def run_extract_remotejobs():
    os.makedirs(DATA_RAW, exist_ok=True)
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, "extract_remotejobs.py")],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        raise Exception(f"RemoteJobs extraction failed: {result.stderr}")

def run_merge_sources():
    os.makedirs(DATA_MERGED, exist_ok=True)
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, "merge_sources.py")],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        raise Exception(f"Merge failed: {result.stderr}")
    merged_file = os.path.join(DATA_MERGED, "merged_raw_jobs.csv")
    if not os.path.exists(merged_file):
        raise Exception("merged_raw_jobs.csv not found after merge!")

def run_knime_workflow():
    print("KNIME workflow already executed manually - skipping")

def validate_clean_output():
    import pandas as pd
    clean_file   = os.path.join(DATA_PROC, "clean_ai_ml_data_jobs.csv")
    metrics_file = os.path.join(DATA_PROC, "metrics_summary.csv")
    if not os.path.exists(clean_file):
        raise Exception(f"clean_ai_ml_data_jobs.csv not found!")
    metrics_file = os.path.join(DATA_PROC, "metrics_summary.csv")

def calculate_metrics():
    import pandas as pd
    clean_file = os.path.join(DATA_PROC, "clean_ai_ml_data_jobs.csv")
    df = pd.read_csv(clean_file)
    metrics = {
        "total_jobs": len(df),
        "pipeline_status": "Success",
        "run_date": str(datetime.now()),
    }
    if "source" in df.columns:
        metrics["jobs_by_source"] = df["source"].value_counts().to_dict()
    if "remote_status" in df.columns:
        metrics["remote_ratio"] = df["remote_status"].value_counts().to_dict()
    if "experience_bracket" in df.columns:
        metrics["experience_distribution"] = df["experience_bracket"].value_counts().to_dict()
        metrics["zero_to_one_year_jobs"] = int(df[df["experience_bracket"] == "0-1"].shape[0])
    if "salary_mid_usd" in df.columns:
        salary_df = df[df["salary_mid_usd"].notna() & (df["salary_mid_usd"] > 0)]
        if len(salary_df) > 0:
            metrics["average_salary_usd"] = round(float(salary_df["salary_mid_usd"].mean()), 2)
    metrics_path = os.path.join(DATA_PROC, "pipeline_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics saved! Total jobs: {metrics['total_jobs']}")

def trigger_n8n_workflow():
    import pandas as pd
    clean_file   = os.path.join(DATA_PROC, "clean_ai_ml_data_jobs.csv")
    metrics_path = os.path.join(DATA_PROC, "pipeline_metrics.json")
    df = pd.read_csv(clean_file)
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            metrics = json.load(f)
    else:
        metrics = {"total_jobs": len(df), "pipeline_status": "Success"}
    payload = {
        "total_jobs": metrics.get("total_jobs", len(df)),
        "jobs_by_source": metrics.get("jobs_by_source", {}),
        "remote_ratio": metrics.get("remote_ratio", {}),
        "zero_to_one_year_jobs": metrics.get("zero_to_one_year_jobs", 0),
        "average_salary_usd": metrics.get("average_salary_usd", "N/A"),
        "pipeline_status": "Success",
        "run_date": str(datetime.now()),
    }
    try:
        response = requests.post(N8N_WEBHOOK, json=payload, timeout=30)
        print(f"n8n response: {response.status_code}")
    except Exception as e:
        print(f"WARNING: n8n trigger failed: {e}")

def archive_outputs():
    os.makedirs(DATA_ARCHIVE, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    files_to_archive = [
        os.path.join(DATA_PROC, "clean_ai_ml_data_jobs.csv"),
        os.path.join(DATA_PROC, "metrics_summary.csv"),
        os.path.join(DATA_MERGED, "merged_raw_jobs.csv"),
    ]
    for f in files_to_archive:
        if os.path.exists(f):
            fname = os.path.basename(f)
            dest  = os.path.join(DATA_ARCHIVE, f"{timestamp}_{fname}")
            shutil.copy2(f, dest)
            print(f"Archived: {fname}")

# Tasks
t_extract_arbeitnow = PythonOperator(task_id="extract_arbeitnow", python_callable=run_extract_arbeitnow, dag=dag)
t_extract_remoteok  = PythonOperator(task_id="extract_remoteok",  python_callable=run_extract_remoteok,  dag=dag)
t_extract_himalayas = PythonOperator(task_id="extract_himalayas", python_callable=run_extract_himalayas, dag=dag)
t_extract_remotejobs= PythonOperator(task_id="extract_remotejobs",python_callable=run_extract_remotejobs,dag=dag)
t_merge             = PythonOperator(task_id="merge_sources",     python_callable=run_merge_sources,     dag=dag)
t_knime             = PythonOperator(task_id="run_knime_workflow", python_callable=run_knime_workflow,    dag=dag)
t_validate          = PythonOperator(task_id="validate_clean_output", python_callable=validate_clean_output, dag=dag)
t_metrics           = PythonOperator(task_id="calculate_metrics", python_callable=calculate_metrics,     dag=dag)
t_n8n               = PythonOperator(task_id="trigger_n8n_workflow", python_callable=trigger_n8n_workflow, dag=dag)
t_archive           = PythonOperator(task_id="archive_outputs",   python_callable=archive_outputs,       dag=dag)

# Dependencies
[t_extract_arbeitnow, t_extract_remoteok, t_extract_himalayas, t_extract_remotejobs] >> t_merge
t_merge >> t_knime >> t_validate >> t_metrics >> t_n8n >> t_archive