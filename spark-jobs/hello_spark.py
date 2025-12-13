from pyspark.sql import SparkSession

if __name__ == "__main__":
    spark = SparkSession.builder \
        .appName("HelloSparkApp") \
        .getOrCreate()

    print("🔥 Hello World from PySpark on a Cluster!")

    data = [("Airflow",), ("PySpark",), ("Properly Connected!",)]
    df = spark.createDataFrame(data, ["message"])
    df.show()

    spark.stop()

