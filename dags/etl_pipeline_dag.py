"""
Airflow DAG: ETL Title Transformation Pipeline
==============================================
This DAG orchestrates a three-phase ETL pipeline using PySpark:
1. Extract: Read JSON data from input file
2. Transform: Change title from "hello" to "hello world"
3. Load: Write transformed data to output file

The entire pipeline runs as a single Spark job with all three phases.

Ticket: AIRFLOW-001
Schedule: Manual trigger (can be configured to run on schedule)
"""

from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime, timedelta

# Default arguments for the DAG
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=1),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=10),
}

# Define the DAG
with DAG(
    dag_id='etl_title_transform_pipeline',
    default_args=default_args,
    description='ETL pipeline to transform JSON title field from "hello" to "hello world"',
    schedule=None,  # Manual trigger only (change to cron expression for scheduled runs)
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['etl', 'spark', 'transformation', 'json'],
    max_active_runs=1,  # Prevent concurrent runs
    doc_md="""
    # ETL Title Transformation Pipeline

    ## Overview
    This pipeline processes JSON data through Extract, Transform, Load phases.

    ## Input
    - **File:** `/opt/airflow/database/input.json`
    - **Format:** JSON with title field
    - **Example:**
      ```json
      {
        "title": "hello"
      }
      ```

    ## Processing
    - Reads input JSON using PySpark
    - Transforms title: "hello" → "hello world"
    - Writes output JSON

    ## Output
    - **File:** `/opt/airflow/database/output.json`
    - **Format:** JSON with transformed title
    - **Example:**
      ```json
      {
        "title": "hello world"
      }
      ```

    ## Monitoring
    - **Airflow UI:** Task logs and execution status
    - **Spark UI:** http://localhost:8085 (job execution details)

    ## Troubleshooting
    - Ensure input.json exists in database directory
    - Verify Spark cluster is running
    - Check volume mounts are configured correctly
    """
) as dag:

    # Single Spark job that handles all three ETL phases
    etl_transform_job = SparkSubmitOperator(
        task_id='etl_title_transform',
        application='/opt/spark-jobs/etl_title_transform.py',
        conn_id='spark_standalone_cluster',
        verbose=True,
        conf={
            'spark.driver.memory': '1g',
            'spark.executor.memory': '1g',
            'spark.executor.cores': '1',
        },
        application_args=[],
        name='ETL_Title_Transform_Pipeline',
        execution_timeout=timedelta(minutes=10),
        doc_md="""
        ### ETL Title Transform Task

        Executes the complete ETL pipeline in a single Spark job:

        **Extract Phase:**
        - Reads `/opt/airflow/database/input.json`
        - Parses JSON into Spark DataFrame
        - Validates data structure

        **Transform Phase:**
        - Applies transformation rule: title="hello" → title="hello world"
        - Logs transformation statistics
        - Preserves other fields unchanged

        **Load Phase:**
        - Writes transformed data to `/opt/airflow/database/output.json`
        - Overwrites existing output file
        - Ensures data integrity

        **Expected Duration:** < 5 minutes
        **Retry Policy:** 3 retries with exponential backoff
        """
    )

    # Task dependency (single task in this case)
    etl_transform_job
