# 🚀 Job Market Analytics Pipeline

An end-to-end automated data engineering pipeline that scrapes job market data, processes metrics, orchestrates tasks, and triggers automated alerts.

## 🛠️ Tech Stack & Tools
- **Data Scraping & Cleaning:** KNIME Analytics Platform
- **Orchestration:** Apache Airflow (CeleryExecutor Cluster)
- **Containerization:** Docker & Docker Compose
- **Automation & Alerts:** n8n Workflow Automation

---

## 📋 Prerequisites (New Computer Setup)

Kisi bhi naye computer par is pipeline ko chalane se pehle yeh software install hone chahiye:
1. **Python 3.10+**
2. **Docker Desktop** (Make sure WSL2 backend is enabled on Windows)
3. **KNIME Analytics Platform** (Latest Version)

---

## ⚡ Step-by-Step Setup & Execution Commands

### 1️⃣ Clone the Repository & Virtual Environment
Sab se pehle project folder me terminal kholin aur virtual environment bana kar required libraries install karein:

```bash
# Clone the repository
git clone <https://github.com/MuhammadZain4/Job_Market_Analytics_Pipeline>
cd job_market_project

# Create and activate virtual environment
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\activate
# On Linux/Ubuntu:
source venv/bin/activate

# Install required Python libraries
pip install packages/libraries (requests, missingno, etc. if using scripts)

2️⃣ Data Scraping (KNIME)
1 KNIME Analytics Platform ko open karein.
2 Project directory me majood KNIME workflow file ko import karein.
3 Node Repository se agar prompt aaye to Expression Node extension ko update/install karein.
4 Execute All (Green Double Play Button) par click karein taakay data scrap ho kar clean ho jaye aur target directory me save ho jaye.
3️⃣ Start n8n Automation Service
Naye computer par n8n ka fresh container up karne ke liye Docker terminal par yeh command chalayein:

# Pull and run n8n in detached mode
docker run -d --name n8n_local -p 5678:5678 n8nio/n8n

Open browser: ⁠http://localhost:5678⁠
 Ek blank workflow banayein, Webhook Node add karein (Method: ⁠POST⁠, Path: ⁠job-market-alert⁠).
 Webhook node me "Listen for test event" par click kar dein.
4️⃣ Launch Apache Airflow Production Cluster (6 Containers)
Airflow ke heavy production setup (CeleryExecutor) ko up karne ke liye project root directory me jahan ⁠docker-compose-airflow.yml⁠ majood hai, wahan yeh commands run karein:

# Step A: Initialize Airflow Database and Create Admin User
docker compose -f docker-compose-airflow.yml up airflow-init

# Step B: Start all 6 Airflow Services (Webserver, Scheduler, Worker, Redis, Triggerer, Postgres)
docker compose -f docker-compose-airflow.yml up -d

5️⃣ Trigger Pipeline & Alerts
1 Browser me Airflow Dashboard open karein: ⁠http://localhost:8080⁠
2 Credentials: Username: ⁠admin⁠ | Password: ⁠admin⁠
3 Apne DAG ko select karke Trigger DAG (Play button) dabayein.
Agar aap ko terminal se manual alert test karna hai, to local virtual environment active kar ke yeh script chalayein:

python scripts/trigger_n8n.py


📊 Pipeline Flow Summary
1 KNIME extracts raw job postings and calculates salaries in USD using the ⁠Expression⁠ node.
2 Airflow orchestrates and tracks the complete ingestion schedule.
3 n8n Webhook catches the final analytical payload.
4 Gmail Node (SMTP) dispatches a structured plain text summary report directly to the inbox.
Developed by: Muhammad Zain (Data Science Pipeline Automation)
