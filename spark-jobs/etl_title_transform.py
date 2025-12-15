"""
ETL Pipeline: Title Transformation
===================================
This PySpark job implements a three-phase ETL pipeline:
1. Extract: Read JSON data from input file
2. Transform: Change title from "hello" to "hello world"
3. Load: Write transformed data to output file

Ticket: AIRFLOW-001
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, lit
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_spark_session(app_name="ETL_Title_Transform"):
    """
    Create and configure Spark session.

    Args:
        app_name (str): Name of the Spark application

    Returns:
        SparkSession: Configured Spark session
    """
    logger.info(f"Creating Spark session: {app_name}")
    spark = SparkSession.builder \
        .appName(app_name) \
        .getOrCreate()

    logger.info(f"Spark version: {spark.version}")
    return spark


def extract_data(spark, input_path):
    """
    Extract phase: Read JSON data from input file.

    Args:
        spark (SparkSession): Active Spark session
        input_path (str): Path to input JSON file

    Returns:
        DataFrame: Spark DataFrame containing input data

    Raises:
        Exception: If file doesn't exist or JSON is invalid
    """
    logger.info("=" * 60)
    logger.info("EXTRACT PHASE: Reading JSON data")
    logger.info(f"Input path: {input_path}")
    logger.info("=" * 60)

    try:
        # Read JSON file into DataFrame
        df = spark.read.json(input_path)

        # Validate data
        row_count = df.count()
        logger.info(f"Successfully read {row_count} records")

        # Show schema
        logger.info("Input schema:")
        df.printSchema()

        # Show sample data
        logger.info("Sample input data:")
        df.show(truncate=False)

        return df

    except Exception as e:
        logger.error(f"Extract phase failed: {str(e)}")
        raise


def transform_data(spark, df):
    """
    Transform phase: Change title from "hello" to "hello world".

    Args:
        spark (SparkSession): Active Spark session
        df (DataFrame): Input DataFrame

    Returns:
        DataFrame: Transformed DataFrame
    """
    logger.info("=" * 60)
    logger.info("TRANSFORM PHASE: Updating title field")
    logger.info("=" * 60)

    try:
        # Count records before transformation
        initial_count = df.count()
        logger.info(f"Records to process: {initial_count}")

        # Show data before transformation
        logger.info("Data before transformation:")
        df.show(truncate=False)

        # Apply transformation: replace "hello" with "hello world"
        transformed_df = df.withColumn(
            "title",
            when(col("title") == "hello", lit("hello world"))
            .otherwise(col("title"))
        )

        # Count records after transformation
        final_count = transformed_df.count()

        # Count how many records were actually modified
        modified_count = transformed_df.filter(col("title") == "hello world").count()

        logger.info(f"Transformation complete:")
        logger.info(f"  - Total records processed: {final_count}")
        logger.info(f"  - Records modified: {modified_count}")

        # Show data after transformation
        logger.info("Data after transformation:")
        transformed_df.show(truncate=False)

        return transformed_df

    except Exception as e:
        logger.error(f"Transform phase failed: {str(e)}")
        raise


def load_data(spark, df, output_path):
    """
    Load phase: Write transformed data to output JSON file.

    Args:
        spark (SparkSession): Active Spark session
        df (DataFrame): Transformed DataFrame
        output_path (str): Path to output JSON file
    """
    logger.info("=" * 60)
    logger.info("LOAD PHASE: Writing transformed data")
    logger.info(f"Output path: {output_path}")
    logger.info("=" * 60)

    try:
        # Count records to write
        record_count = df.count()
        logger.info(f"Writing {record_count} records to output")

        # Write DataFrame to JSON
        # mode="overwrite" ensures we replace existing file
        # coalesce(1) writes to a single file instead of partitions
        df.coalesce(1).write \
            .mode("overwrite") \
            .json(output_path)

        logger.info(f"Successfully wrote data to {output_path}")
        logger.info("Load phase complete")

    except Exception as e:
        logger.error(f"Load phase failed: {str(e)}")
        raise


def main():
    """
    Main ETL pipeline execution.
    """
    # Define file paths
    INPUT_PATH = "/opt/airflow/database/input.json"
    OUTPUT_PATH = "/opt/airflow/database/output.json"

    logger.info("*" * 60)
    logger.info("ETL PIPELINE: Title Transformation")
    logger.info("*" * 60)
    logger.info(f"Input file: {INPUT_PATH}")
    logger.info(f"Output file: {OUTPUT_PATH}")
    logger.info("*" * 60)

    spark = None

    try:
        # Initialize Spark session
        spark = create_spark_session("ETL_Title_Transform")

        # Phase 1: Extract
        input_df = extract_data(spark, INPUT_PATH)

        # Phase 2: Transform
        transformed_df = transform_data(spark, input_df)

        # Phase 3: Load
        load_data(spark, transformed_df, OUTPUT_PATH)

        # Pipeline complete
        logger.info("*" * 60)
        logger.info("ETL PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("*" * 60)

        sys.exit(0)

    except Exception as e:
        logger.error("*" * 60)
        logger.error("ETL PIPELINE FAILED")
        logger.error(f"Error: {str(e)}")
        logger.error("*" * 60)

        sys.exit(1)

    finally:
        # Clean up Spark session
        if spark:
            logger.info("Stopping Spark session")
            spark.stop()


if __name__ == "__main__":
    main()
