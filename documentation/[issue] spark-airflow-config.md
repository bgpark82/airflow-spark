# SparkSubmitOperator Issues and Solutions

## Issue 1: Spark Master Connection Failure and YARN Default

### Problem
Airflow's `SparkSubmitOperator` failed to execute Spark jobs due to environment configuration issues.

**Error Message:** `Could not load connection string spark_default, defaulting to yarn`

### Analysis
* Airflow couldn't find the `spark_default` connection or no explicit `conn_id` was configured
* `SparkSubmitHook` defaulted to using `--master yarn`
* **Root Cause:** Docker Compose environment uses **Spark Standalone Cluster**, not YARN. Airflow container cannot find YARN master, causing job submission to fail.

### Solution

#### Step 1: Configure Airflow Connection
In Airflow Web UI (`Admin > Connections`), add a connection for Spark Standalone cluster:
* **Connection ID:** `spark_standalone_cluster` (or your preferred name)
* **Connection Type:** `Spark`
* **Host:** `spark://spark-master` (Docker Compose service name)
* **Port:** `7077`

#### Step 2: Update DAG Code
Explicitly specify the connection ID in `SparkSubmitOperator`:
```python
run_spark_hello_world = SparkSubmitOperator(
    # ...
    conn_id='spark_standalone_cluster',  # Use the connection ID from Step 1
    # ...
)
```

---

## Issue 2: Missing JAVA Environment Variable

### Problem
**Error Message:** `JAVA_HOME is not set`

### Analysis
* `spark-submit` requires Java Development Kit (JDK) path to be set in `JAVA_HOME` environment variable
* Currently not configured in the Airflow container
* Spark runs on JVM, making this essential

### Solution

#### Step 1: Modify Dockerfile
Install Java and set `JAVA_HOME` environment variable:
```dockerfile
FROM apache/airflow:3.1.5

# Install Spark Provider
RUN pip install apache-airflow-providers-apache-spark

# Install Java and set environment variables
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jdk && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME environment variable
ENV JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"

USER airflow
```

#### Step 2: Rebuild Docker Compose
```bash
docker compose up --build
```

### Summary
1. Configure Airflow Connection to point to Spark Standalone cluster (`spark://spark-master:7077`)
2. Update DAG to explicitly use `conn_id`
3. Modify Dockerfile to install Java and set `JAVA_HOME`
4. Rebuild with `docker compose up --build`

---

## Issue 3: Java Executable Path Mismatch

### Problem
**Error Message:** `/usr/lib/jvm/java-17-openjdk-amd64/bin/java: No such file or directory`

### Analysis
* `JAVA_HOME` variable was set, but the Java executable doesn't exist at the specified path
* `spark-submit` script searches for Java executable by:
  1. Taking `$JAVA_HOME` value (`"/usr/lib/jvm/java-17-openjdk-amd64"`)
  2. Appending `/bin/java` to create full path
  3. Looking for executable at `/usr/lib/jvm/java-17-openjdk-amd64/bin/java`
* The file doesn't exist at this location

### Solution

#### Option 1: Install Both Java and Spark Binaries (Recommended)
In Docker Compose environment, Airflow container needs both Java and Spark binaries (`spark-submit`, `spark-class`, etc.).

**Complete Dockerfile modification:**
```dockerfile
FROM apache/airflow:3.1.5

# 1. Install Spark Provider
RUN pip install apache-airflow-providers-apache-spark

USER root

# 2. Install Java
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jdk && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. Install Spark binaries (example: Spark 3.5.7)
ENV SPARK_VERSION=3.5.7
ENV HADOOP_VERSION=3
ENV SPARK_HOME="/opt/spark"

RUN mkdir -p ${SPARK_HOME} && \
    curl -o /tmp/spark.tgz "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz" && \
    tar -xzf /tmp/spark.tgz --directory ${SPARK_HOME} --strip-components 1 && \
    rm /tmp/spark.tgz

# 4. Set environment variables
ENV JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
ENV PATH="${JAVA_HOME}/bin:${SPARK_HOME}/bin:${SPARK_HOME}/sbin:${PATH}"

# Grant ownership to Airflow user
RUN chown -R airflow:0 ${SPARK_HOME}

USER airflow
```

#### Option 2: Create Symbolic Link (Alternative)
If Java is installed at a different location:
```dockerfile
USER root
# Example: if actual Java path is /usr/lib/jvm/default-java/bin/java
RUN ln -sf /usr/lib/jvm/default-java/bin/java /usr/lib/jvm/java-17-openjdk-amd64/bin/java
USER airflow
```

#### Rebuild
```bash
docker compose up --build
```

---

## Issue 4: Spark Class Script Error (Continued)

### Problem
**Error Messages:**
* `/opt/spark/bin/spark-class: line 71: /usr/lib/jvm/java-17-openjdk-amd64/bin/java: No such file or directory`
* `/opt/spark/bin/spark-class: line 97: CMD: bad array subscript`

### Analysis
* Spark binaries successfully installed to `/opt/spark`
* `/opt/spark/bin/spark-class` script references `JAVA_HOME` but Java executable still not found
* Actual Java installation path differs from configured `JAVA_HOME` path
* `CMD: bad array subscript` is a secondary shell error caused by the Java path issue

### Solution

#### Fix JAVA_HOME Path
Most Debian/Ubuntu containers install `openjdk-17-jdk` to `/usr/lib/jvm/java-17-openjdk-amd64`, but sometimes the system uses a different default path.

**Dockerfile modification:**
```dockerfile
# After Java installation
USER root

# Create symbolic link from actual Java path to expected path
# Assumes 'default-java' points to actual installation
RUN if [ -d "/usr/lib/jvm/default-java" ]; then \
        ln -sf /usr/lib/jvm/default-java /usr/lib/jvm/java-17-openjdk-amd64; \
    fi

# Set JAVA_HOME
ENV JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
# (followed by SPARK_HOME and PATH settings)

USER airflow
```

#### Rebuild and Verify
```bash
docker compose up --build
```

**Verification:** If still failing after rebuild, connect to container and verify:
```bash
docker compose exec airflow-worker bash
ls -l /usr/lib/jvm/java-17-openjdk-amd64/bin/java
```

---

## Issue 5: Missing Spark Job File

### Problem
**Error Message:** `python3: can't open file '/opt/spark-jobs/hello_spark.py': [Errno 2] No such file or directory`

**Error Code:** 2 (indicates "No such file or directory")

### Analysis
* Java and Spark binary path issues are now resolved
* `spark-submit` command executes successfully
* `SparkSubmitOperator` tells Spark to execute `/opt/spark-jobs/hello_spark.py`
* File doesn't exist in Airflow worker container's filesystem at this path
* In client deploy mode (`--deploy-mode client`), Spark driver starts in Airflow worker container and expects job file to exist locally

### Root Cause
* DAG's `SparkSubmitOperator` has `application` parameter set to `/opt/spark-jobs/hello_spark.py`
* This file is not volume-mounted or copied to Airflow worker container's `/opt/spark-jobs/` directory

### Solution

#### Step 1: Create Local Job Directory
Create directory for Spark job files in local Airflow project folder:
```bash
mkdir spark-jobs
# Place hello_spark.py file here
```

#### Step 2: Modify docker-compose.yaml
Add volume mount to sync local `spark-jobs` directory with container's `/opt/spark-jobs`:

```yaml
x-airflow-common:
  &airflow-common
  # ... (other settings)
  volumes:
    - ${AIRFLOW_PROJ_DIR:-.}/dags:/opt/airflow/dags
    - ${AIRFLOW_PROJ_DIR:-.}/logs:/opt/airflow/logs
    - ${AIRFLOW_PROJ_DIR:-.}/config:/opt/airflow/config
    - ${AIRFLOW_PROJ_DIR:-.}/plugins:/opt/airflow/plugins
    # Add this line:
    - ${AIRFLOW_PROJ_DIR:-.}/spark-jobs:/opt/spark-jobs
```

#### Step 3: Restart Docker Compose
```bash
docker compose up -d
```

---

## Issue 6: Spark Version Compatibility (Serialization Error)

### Problem
**Error Message:** `java.io.InvalidClassException: org.apache.spark.rpc.netty.RpcEndpointVerifier$CheckExistence; local class incompatible: stream classdesc serialVersionUID = 7789290765573734431, local class serialVersionUID = 5378738997755484868`

### Analysis
* Error occurs in Java serialization mechanism
* Spark RPC (Remote Procedure Call) serializes objects when transmitting over network
* `InvalidClassException` means sender (Airflow driver) and receiver (Spark Master) use the same class but with different versions (SerialVersionUID mismatch)
* Class `org.apache.spark.rpc.netty.RpcEndpointVerifier$CheckExistence` is Spark's internal RPC endpoint verification class
* **Conclusion:** Spark binary version in Airflow container differs from Spark Master container version

### Root Cause
Spark can have RPC class and protocol changes even between minor versions (e.g., 3.4.x vs 3.5.x). All cluster components must use **exactly the same Spark version**.

Current setup has version mismatch:
1. **Airflow container (Spark Driver):** Downloads Spark binary in `Dockerfile` to `/opt/spark`
2. **Spark Master/Worker containers:** Uses `image: apache/spark:X.X.X` in `docker-compose.yaml`

### Solution

#### Match Spark Versions Across All Components
Ensure `SPARK_VERSION` in Dockerfile matches image tags in docker-compose.yaml:

| File | Variable/Tag | Required Value |
| :--- | :--- | :--- |
| **Airflow `Dockerfile`** | `ENV SPARK_VERSION=` | `3.5.7` (or your chosen version) |
| **`docker-compose.yaml` (spark-master)** | `image: apache/spark:` | `apache/spark:3.5.7` (match Dockerfile) |
| **`docker-compose.yaml` (spark-worker)** | `image: apache/spark:` | `apache/spark:3.5.7` (match Dockerfile) |

#### Note on Python Version Mismatch
If you previously encountered `[PYTHON_VERSION_MISMATCH]` error (3.12 vs 3.8):
* Upgrading to Spark 4.0.x naturally resolves Python 3.12 compatibility
* If staying with Spark 3.5.x, you must install Python 3.12 in Spark Worker containers

#### Rebuild
```bash
docker compose up --build
```

---

## Issue 7: Python Version Mismatch Between Driver and Worker

### Problem
Python version mismatch between Airflow container (driver) and Spark Worker containers causing PySpark execution failures.

### Analysis: Airflow Image and Python Version

**Airflow Image Structure:**
* Official Airflow Docker images are built on specific Python versions
* `apache/airflow:3.1.5` is built on **Python 3.12** by default
* Once built, the core Python environment cannot be simply replaced with another version (e.g., 3.10)

**`PYSPARK_DRIVER_PYTHON` Limitation:**
* This environment variable tells Spark which Python executable to use
* Setting it to `python3.10` won't work if Python 3.10 executable isn't installed in the container
* The executable must actually exist in the filesystem

### Solution

#### Option 1: Use Python 3.10-based Airflow Image (Recommended)
Most stable and recommended approach. Use an Airflow version that provides Python 3.10:

```dockerfile
# Dockerfile
FROM apache/airflow:2.8.3-python3.10

# ... rest of configuration remains the same
```

**Advantages:**
* Clean, stable environment
* No dependency conflicts
* Matches Spark Worker Python version

#### Option 2: Install Python 3.10 in Current Image (Alternative)
Keep `apache/airflow:3.1.5` but add Python 3.10:

```dockerfile
FROM apache/airflow:3.1.5

USER root

# Install Python 3.10 and dev packages
RUN apt-get update && \
    apt-get install -y python3.10 python3.10-dev && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Configure PySpark to use Python 3.10
ENV PYSPARK_DRIVER_PYTHON=/usr/bin/python3.10

USER airflow
```

**Considerations:**
* Larger image size
* Potential dependency conflicts
* Maintains Airflow 3.1.5 version

### Recommendation
Use **Option 1** (Python 3.10-based image) to match Spark Worker Python version and resolve PySpark version mismatch issues definitively.

---

## Summary of All Issues

### Issue Resolution Order
1. **Issue 1:** Configure Spark connection - Point to `spark://spark-master:7077`
2. **Issue 2:** Install Java and set `JAVA_HOME` in Dockerfile
3. **Issue 3 & 4:** Fix Java executable path mismatch with symbolic links
4. **Issue 5:** Volume mount `spark-jobs` directory for job files
5. **Issue 6:** Match Spark versions across Airflow and Spark containers
6. **Issue 7:** Match Python versions between driver (Airflow) and workers

### Complete Working Configuration

**Dockerfile:**
```dockerfile
FROM apache/airflow:2.8.3-python3.10

# Install Spark Provider
RUN pip install apache-airflow-providers-apache-spark

USER root

# Install Java
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jdk && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Spark binaries
ENV SPARK_VERSION=3.5.7
ENV HADOOP_VERSION=3
ENV SPARK_HOME="/opt/spark"

RUN mkdir -p ${SPARK_HOME} && \
    curl -o /tmp/spark.tgz "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz" && \
    tar -xzf /tmp/spark.tgz --directory ${SPARK_HOME} --strip-components 1 && \
    rm /tmp/spark.tgz

# Set environment variables
ENV JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
ENV PATH="${JAVA_HOME}/bin:${SPARK_HOME}/bin:${SPARK_HOME}/sbin:${PATH}"

RUN chown -R airflow:0 ${SPARK_HOME}

USER airflow
```

**docker-compose.yaml volumes:**
```yaml
volumes:
  - ${AIRFLOW_PROJ_DIR:-.}/dags:/opt/airflow/dags
  - ${AIRFLOW_PROJ_DIR:-.}/logs:/opt/airflow/logs
  - ${AIRFLOW_PROJ_DIR:-.}/config:/opt/airflow/config
  - ${AIRFLOW_PROJ_DIR:-.}/plugins:/opt/airflow/plugins
  - ${AIRFLOW_PROJ_DIR:-.}/spark-jobs:/opt/spark-jobs
```

**Spark images in docker-compose.yaml:**
```yaml
spark-master:
  image: apache/spark:3.5.7

spark-worker:
  image: apache/spark:3.5.7
```

**DAG Configuration:**
```python
run_spark_hello_world = SparkSubmitOperator(
    conn_id='spark_standalone_cluster',
    application='/opt/spark-jobs/hello_spark.py',
    # ... other parameters
)
```