from airflow import DAG
from airflow.providers.ssh.operators.ssh import SSHOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 5, 9),
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

with DAG(
    dag_id='update_user_locations_dag',
    default_args=default_args,
    description='Update MongoDB using SSHOperator',
    schedule_interval='* * * * *',  # runs every minute
    catchup=False
) as dag:

    update_task = SSHOperator(
        task_id='update_user_locations',
        ssh_conn_id='dev_env_ssh',
        command='python3 /home/developer/AlertCircle/update_user_locations.py',
        do_xcom_push=True  # captures stdout into logs
    )
