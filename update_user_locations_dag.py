from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'nivshitz',
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

with DAG(
    dag_id='update_user_locations_dag',
    default_args=default_args,
    description='Update MongoDB using BashOperator',
    schedule_interval='*/1 * * * *',
    start_date=datetime(2025, 5, 9),
    catchup=False
) as dag:
    update_task = BashOperator(
        task_id='update_user_locations',
        bash_command='docker exec dev_env python3 /home/developer/AlertCircle/update_user_locations.py',
    )
