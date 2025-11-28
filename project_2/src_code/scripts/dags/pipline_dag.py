from datetime import datetime
from pathlib import Path
import sys
import subprocess

from airflow import DAG
from airflow.operators.python import PythonOperator


project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

DEFAULT_SCRIPTS_DIR ="/opt/airflow/dags/"


def run_script(script_name: str):
    script_path = DEFAULT_SCRIPTS_DIR + script_name

    #if not script_path.exists():
    #    raise FileNotFoundError(f"Script introuvable: {script_path}")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Erreur dans {script_name}:\n{result.stderr}")

    return result.stdout


with DAG(
    dag_id="amazon_review_data_pipeline",
    description="ETL Amazon review orchestré par Airflow",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["etl", "amazon"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract_postgres_to_s3",
        python_callable=lambda: run_script("extract_postgres_to_s3.py"),
        #python_callable=lambda: run_script("/opt/airflow/dags/extract_postgres_to_s3.py"),

    )

    setup_mongo_task = PythonOperator(
        task_id="setup_mongodb",
        python_callable=lambda: run_script("setup_mongodb.py"),
    )

    setup_snowflake_task = PythonOperator(
        task_id="setup_snowflake",
        python_callable=lambda: run_script("setup_snowflake.py"),
    )

    process_task = PythonOperator(
        task_id="process_and_store",
        python_callable=lambda: run_script("process_and_store.py"),
    )

    extract_task >> setup_mongo_task >> setup_snowflake_task >> process_task
