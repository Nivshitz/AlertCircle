from airflow import DAG
from airflow.providers.ssh.operators.ssh import SSHOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'nivshitz',
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

with DAG(
    dag_id='update_user_locations_ssh_dag',
    default_args=default_args,
    description='Update MongoDB using SSHOperator',
    schedule_interval='*/1 * * * *',
    start_date=datetime(2025, 5, 9),
    catchup=False,
    max_active_runs=1
) as dag:
    update_task = SSHOperator(
        task_id='update_user_locations',
        ssh_conn_id='dev_env_ssh',
        command='python3 /home/developer/airflow/update_user_locations.py',
    )
