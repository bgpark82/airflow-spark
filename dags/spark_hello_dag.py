
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow import DAG
from datetime import datetime

with DAG(
        dag_id="spark_hello_world_cluster",
        start_date=datetime(2025, 1, 1),
        schedule=None,
        catchup=False,
        tags=['spark'],
) as dag:
    run_spark_job = SparkSubmitOperator(
        task_id="run_spark_hello_world",
        application="/opt/spark-jobs/hello_spark.py",
        conn_id="spark_standalone_cluster",
        verbose=True,
    )
