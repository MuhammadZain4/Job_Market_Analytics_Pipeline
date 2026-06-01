from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id='job_market_master_pipeline',
    start_date=datetime(2026, 5, 17),
    schedule_interval=None,
    catchup=False
) as dag:

    # 1. Pehla node: trigger_n8n_automation
    first_task = BashOperator(
        task_id='trigger_n8n_automation',
        bash_command='echo "Starting n8n automation"',
    )

    previous_task = first_task

    # 2. Loop chalega baqi 9 execute_node_part nodes banane ke liye (Total = 10 nodes)
    for i in range(1, 10):
        current_task = BashOperator(
            task_id=f'execute_node_part_{i}',
            bash_command=f'echo "Running node part {i}"',
        )
        
        # Straight line chain connection
        previous_task >> current_task
        previous_task = current_task