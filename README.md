# Airflow + PySpark Integration Project

A Docker Compose-based project demonstrating how to integrate Apache Airflow with Apache Spark for distributed data processing workflows.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation Guide](#installation-guide)
- [Quick Start](#quick-start)
- [Project Architecture](#project-architecture)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)
- [Additional Resources](#additional-resources)

## Overview

This project sets up a complete development environment featuring:
- **Apache Airflow 3.1.5** with CeleryExecutor for workflow orchestration
- **Apache Spark 4.0.1** Standalone cluster for distributed computing
- **PostgreSQL** for Airflow metadata storage
- **Redis** for Celery task queue
- Full integration between Airflow and Spark using `SparkSubmitOperator`

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 2.0 or higher)
- **Git** (for cloning the repository)
- **Minimum System Requirements:**
  - 4GB RAM available for Docker
  - 2 CPU cores
  - 10GB free disk space

## Installation Guide

### Step 1: Clone or Set Up Project Directory

```bash
# Create project directory
mkdir hello-airflow-pyspark
cd hello-airflow-pyspark
```

### Step 2: Create Project Structure

Create the following directory structure:

```
hello-airflow-pyspark/
├── dags/                  # Airflow DAG definitions
├── logs/                  # Airflow logs
├── plugins/               # Airflow plugins
├── config/                # Airflow configuration
├── spark-jobs/            # PySpark job scripts
├── Dockerfile             # Custom Airflow image
├── docker-compose.yaml    # Docker services configuration
└── .env                   # Environment variables
```

### Step 3: Create the Dockerfile

Create a `Dockerfile` to build a custom Airflow image with Spark integration:

```dockerfile
FROM apache/airflow:3.1.5-python3.10

# Install Spark Provider for Airflow
RUN pip install apache-airflow-providers-apache-spark

USER root

# Install Java (required for Spark)
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jdk && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Spark binaries
ENV SPARK_VERSION=4.0.1
ENV HADOOP_VERSION=3
ENV SPARK_HOME="/opt/spark"

RUN mkdir -p ${SPARK_HOME} && \
    curl -o /tmp/spark.tgz "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz" && \
    tar -xzf /tmp/spark.tgz --directory ${SPARK_HOME} --strip-components 1 && \
    rm /tmp/spark.tgz

# Set environment variables
# Note: Adjust JAVA_HOME path based on your architecture (arm64 or amd64)
ENV JAVA_HOME="/usr/lib/jvm/java-17-openjdk-arm64"
ENV PATH="${JAVA_HOME}/bin:${SPARK_HOME}/bin:${SPARK_HOME}/sbin:${PATH}"

# Grant ownership to Airflow user
RUN chown -R airflow:0 ${SPARK_HOME}

USER airflow
```

**Important:** If you're on an amd64 architecture (Intel/AMD processors), change:
```dockerfile
ENV JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
```

### Step 4: Create docker-compose.yaml

Create a `docker-compose.yaml` file with the following services:

```yaml
---
x-airflow-common:
  &airflow-common
  build: .
  env_file:
    - ${ENV_FILE_PATH:-.env}
  environment:
    &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: CeleryExecutor
    AIRFLOW__CORE__AUTH_MANAGER: airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0
    AIRFLOW__CORE__FERNET_KEY: ''
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
    AIRFLOW__CORE__LOAD_EXAMPLES: 'true'
    AIRFLOW__CORE__EXECUTION_API_SERVER_URL: 'http://airflow-apiserver:8080/execution/'
    AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK: 'true'
    AIRFLOW_CONFIG: '/opt/airflow/config/airflow.cfg'
  volumes:
    - ${AIRFLOW_PROJ_DIR:-.}/dags:/opt/airflow/dags
    - ${AIRFLOW_PROJ_DIR:-.}/logs:/opt/airflow/logs
    - ${AIRFLOW_PROJ_DIR:-.}/config:/opt/airflow/config
    - ${AIRFLOW_PROJ_DIR:-.}/plugins:/opt/airflow/plugins
    - ${AIRFLOW_PROJ_DIR:-.}/spark-jobs:/opt/spark-jobs # spark job이 정의될 공간. airflow가 읽어서 실행한다
  user: "${AIRFLOW_UID:-50000}:0"
  depends_on:
    &airflow-common-depends-on
    redis:
      condition: service_healthy
    postgres:
      condition: service_healthy

services:
  # Spark Master
  spark-master:
    image: apache/spark:4.0.1 # bitami/spark는 더이상 서비스 하지 않는다
    container_name: spark-master
    hostname: spark-master
    command: /opt/spark/bin/spark-class org.apache.spark.deploy.master.Master
    environment:
      - SPARK_MODE=master
      - SPARK_MASTER_HOST=spark-master
      - SPARK_MASTER_PORT=7077
      - SPARK_MASTER_WEBUI_PORT=8080
    ports:
      - '8085:8080'  # Spark Master Web UI
      - '7077:7077'  # Spark Master communication

  # Spark Worker
  spark-worker:
    image: apache/spark:4.0.1
    container_name: spark-worker-1
    hostname: spark-worker-1
    command: /opt/spark/bin/spark-class org.apache.spark.deploy.worker.Worker spark://spark-master:7077
    depends_on:
      - spark-master
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
      - SPARK_WORKER_CORES=2
      - SPARK_WORKER_MEMORY=2g
    ports:
      - '8084:8081'  # Spark Worker Web UI

  # PostgreSQL (Airflow metadata database)
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 10s
      retries: 5
      start_period: 5s
    restart: always

  # Redis (Celery message broker)
  redis:
    image: redis:7.2-bookworm
    expose:
      - 6379
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 30s
      retries: 50
      start_period: 30s
    restart: always

  # Airflow API Server
  airflow-apiserver:
    <<: *airflow-common
    command: api-server
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/api/v2/version"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  # Airflow Scheduler
  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8974/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  # Airflow DAG Processor
  airflow-dag-processor:
    <<: *airflow-common
    command: dag-processor
    healthcheck:
      test: ["CMD-SHELL", 'airflow jobs check --job-type DagProcessorJob --hostname "$${HOSTNAME}"']
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  # Airflow Celery Worker
  airflow-worker:
    <<: *airflow-common
    command: celery worker
    healthcheck:
      test:
        - "CMD-SHELL"
        - 'celery --app airflow.providers.celery.executors.celery_executor.app inspect ping -d "celery@$${HOSTNAME}" || celery --app airflow.executors.celery_executor.app inspect ping -d "celery@$${HOSTNAME}"'
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    environment:
      <<: *airflow-common-env
      DUMB_INIT_SETSID: "0"
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-apiserver:
        condition: service_healthy
      airflow-init:
        condition: service_completed_successfully

  # Airflow Triggerer
  airflow-triggerer:
    <<: *airflow-common
    command: triggerer
    healthcheck:
      test: ["CMD-SHELL", 'airflow jobs check --job-type TriggererJob --hostname "$${HOSTNAME}"']
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  # Airflow Initialization
  airflow-init:
    <<: *airflow-common
    entrypoint: /bin/bash
    command:
      - -c
      - |
        mkdir -v -p /opt/airflow/{logs,dags,plugins,config}
        /entrypoint airflow version
        /entrypoint airflow config list >/dev/null
        chown -R "${AIRFLOW_UID}:0" /opt/airflow/
    environment:
      <<: *airflow-common-env
      _AIRFLOW_DB_MIGRATE: 'true'
      _AIRFLOW_WWW_USER_CREATE: 'true'
      _AIRFLOW_WWW_USER_USERNAME: ${_AIRFLOW_WWW_USER_USERNAME:-airflow}
      _AIRFLOW_WWW_USER_PASSWORD: ${_AIRFLOW_WWW_USER_PASSWORD:-airflow}
    user: "0:0"

volumes:
  postgres-db-volume:
```

### Step 5: Create Environment File

Create a `.env` file in the project root:

```bash
# Airflow UID (for file permissions)
AIRFLOW_UID=50000

# Airflow Web UI credentials
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow
```

### Step 6: Initialize Directory Structure

```bash
# Create required directories
mkdir -p dags logs plugins config spark-jobs

# Set proper permissions (Linux/Mac only)
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

## Quick Start

### 1. Start All Services

Build and start all containers:

```bash
docker compose up --build
```

This will:
- Build the custom Airflow image with Spark integration
- Start PostgreSQL, Redis, Spark Master, Spark Worker
- Initialize Airflow database
- Start all Airflow services (scheduler, worker, API server, etc.)

**Note:** Initial startup may take 5-10 minutes.

### 2. Configure Spark Connection in Airflow

Once all services are running:

1. Open Airflow Web UI: http://localhost:8080
2. Login with credentials (default: `airflow` / `airflow`)
3. Navigate to **Admin > Connections**
4. Click the **+** button to add a new connection
5. Configure the Spark connection:
    - **Connection ID:** `spark_standalone_cluster`
    - **Connection Type:** `Spark`
   - **Host:** `spark://spark-master`
   - **Port:** `7077`
6. Click **Save**

### 3. Create a Sample PySpark Job

Create `spark-jobs/hello_spark.py`:

```python
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
```

### 4. Create an Airflow DAG

Create `dags/spark_hello_dag.py`:

```python
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
```

### 5. Run the DAG

1. Go to Airflow Web UI: http://localhost:8080
2. Find the DAG `spark_hello_world_cluster`
3. Toggle it to **ON** (unpause)
4. Click the **Play** button and select **Trigger DAG**
5. Click on the running DAG instance to view logs
6. Click on the task `run_spark_hello_world` to see execution details

### 6. Monitor Spark Jobs

- **Spark Master UI:** http://localhost:8085
  - View cluster status, resources, and running applications
- **Spark Worker UI:** http://localhost:8084
  - Monitor individual worker status and resources

## Project Architecture

### Container Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Network                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────┐    ┌──────────────────┐                 │
│  │ Spark Master   │◄───┤  Spark Worker    │                 │
│  │ (port 7077)    │    │  (2 cores, 2GB)  │                 │
│  │ Web UI: 8085   │    │  Web UI: 8084    │                 │
│  └────────▲───────┘    └──────────────────┘                 │
│           │                                                 │
│           │ spark-submit                                    │
│           │                                                 │
│  ┌────────┴───────────────────────────────────┐             │
│  │      Airflow Worker (Celery)               │             │
│  │  - Runs SparkSubmitOperator                │             │
│  │  - Contains Spark Client (/opt/spark)      │             │
│  │  - Java 17 + Python 3.10                   │             │
│  └────────────────────────────────────────────┘             │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Scheduler   │  │  API Server  │  │ DAG Processor│       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │  PostgreSQL  │  │    Redis     │                         │
│  │  (metadata)  │  │  (broker)    │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **DAG Definition:** User defines DAG with `SparkSubmitOperator` in `dags/` directory
2. **Scheduler:** Airflow scheduler reads DAG and schedules tasks
3. **Worker:** Celery worker picks up the task
4. **Spark Submit:** Worker executes `spark-submit` command with job file from `/opt/spark-jobs`
5. **Spark Master:** Receives job submission and allocates resources
6. **Spark Worker:** Executes PySpark application
7. **Results:** Task logs and results are stored in Airflow metadata database

## How It Works

### Component Integration

#### 1. Airflow Container with Spark Client

The custom Dockerfile installs:
- **Spark Provider:** `apache-airflow-providers-apache-spark` for `SparkSubmitOperator`
- **Java 17:** Required dependency for Spark
- **Spark Binaries:** Complete Spark distribution in `/opt/spark` for client operations

#### 2. Version Compatibility

All components use compatible versions:
- **Airflow:** 3.1.5 with Python 3.10
- **Spark:** 4.0.1 (same version in Airflow container and Spark cluster)
- **Java:** OpenJDK 17

#### 3. Volume Mounts

Key directories are mounted:
- `./dags:/opt/airflow/dags` - DAG definitions
- `./spark-jobs:/opt/spark-jobs` - PySpark job files
- `./logs:/opt/airflow/logs` - Execution logs

#### 4. SparkSubmitOperator

The operator:
1. Reads the PySpark script from `/opt/spark-jobs`
2. Connects to Spark Master using `conn_id="spark_standalone_cluster"`
3. Submits job via `spark-submit` command
4. Monitors job execution
5. Returns success/failure to Airflow

### Example Execution Flow

```
1. User triggers DAG "spark_hello_world_cluster"
   ↓
2. Scheduler queues task "run_spark_hello_world"
   ↓
3. Celery worker picks up task
   ↓
4. SparkSubmitOperator constructs command:
   spark-submit \
     --master spark://spark-master:7077 \
     /opt/spark-jobs/hello_spark.py
   ↓
5. Spark Master receives application
   ↓
6. Spark Worker executes PySpark code:
   - Creates SparkSession
   - Creates DataFrame
   - Shows results
   - Stops session
   ↓
7. Results logged in Airflow task instance
```

## Troubleshooting

### Common Issues

#### 1. Connection Refused Error

**Error:** `Connection refused to spark-master:7077`

**Solution:** Ensure Spark Master is running:
```bash
docker compose ps spark-master
```

Check Spark Master logs:
```bash
docker compose logs spark-master
```

#### 2. Java Not Found

**Error:** `JAVA_HOME is not set` or `java: command not found`

**Solution:** Verify Java installation in Airflow container:
```bash
docker compose exec airflow-worker bash
echo $JAVA_HOME
java -version
```

#### 3. Python Version Mismatch

**Error:** `[PYTHON_VERSION_MISMATCH] Python versions mismatch`

**Solution:** Ensure all containers use the same Python version (3.10 in this setup)

#### 4. Spark Job File Not Found

**Error:** `can't open file '/opt/spark-jobs/hello_spark.py'`

**Solution:** Check volume mount:
```bash
docker compose exec airflow-worker ls -la /opt/spark-jobs/
```

Ensure file exists in local `./spark-jobs/` directory

### Viewing Logs

**Airflow task logs:**
```bash
docker compose logs airflow-worker
```

**Spark Master logs:**
```bash
docker compose logs spark-master
```

**Spark Worker logs:**
```bash
docker compose logs spark-worker
```

### Restarting Services

```bash
# Stop all services
docker compose down

# Remove volumes (fresh start)
docker compose down -v

# Rebuild and restart
docker compose up --build
```

## Additional Resources

### Documentation
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [Spark Provider for Airflow](https://airflow.apache.org/docs/apache-airflow-providers-apache-spark/)

### Web UIs
- **Airflow:** http://localhost:8080 (username: `airflow`, password: `airflow`)
- **Spark Master:** http://localhost:8085
- **Spark Worker:** http://localhost:8084

### Project Files
- Detailed troubleshooting guide: `documentation/sparkSubmitOperator-issue.md`
- Configuration guides available in `documentation/` directory

## License

This project is for educational purposes.
