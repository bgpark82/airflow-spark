# ETL Pipeline Guide: Title Transformation

## Overview

This guide provides instructions for running the ETL (Extract, Transform, Load) pipeline that transforms JSON data using Apache Airflow and PySpark.

**Business Requirement:** [AIRFLOW-001] - ETL Pipeline for Title Transformation

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ETL Pipeline Flow                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Input File              Transform              Output File  │
│  ┌──────────┐           ┌──────────┐           ┌──────────┐ │
│  │input.json│──Extract─▶│  PySpark │──Load────▶│output.json│
│  │          │           │          │           │          │ │
│  │ title:   │           │  title   │           │ title:   │ │
│  │ "hello"  │           │  hello → │           │ "hello   │ │
│  │          │           │  hello   │           │  world"  │ │
│  │          │           │  world   │           │          │ │
│  └──────────┘           └──────────┘           └──────────┘ │
│       │                       │                      │       │
│       └───────────────────────┴──────────────────────┘       │
│                     Spark Cluster                            │
└─────────────────────────────────────────────────────────────┘
```

## Files and Locations

### Pipeline Files
- **DAG Definition:** `dags/etl_pipeline_dag.py`
- **PySpark Job:** `spark-jobs/etl_title_transform.py`
- **Business Ticket:** `documentation/ticket-etl-pipeline.md`

### Data Files
- **Input:** `database/input.json`
- **Output:** `database/output.json` (created after pipeline runs)

### Container Paths
- **Input:** `/opt/airflow/database/input.json`
- **Output:** `/opt/airflow/database/output.json`

## Quick Start

### 1. Verify Prerequisites

Ensure all services are running:
```bash
docker compose ps
```

All Airflow and Spark containers should show "healthy" or "running" status.

### 2. Verify Input File

Check that input.json exists:
```bash
cat database/input.json
```

Expected content:
```json
{
  "title": "hello"
}
```

### 3. Access Airflow Web UI

1. Open browser: http://localhost:8080
2. Login with credentials:
   - Username: `airflow`
   - Password: `airflow`

### 4. Locate the DAG

1. Find DAG: `etl_title_transform_pipeline`
2. You should see it in the DAG list with tags: `etl`, `spark`, `transformation`, `json`

### 5. Trigger the Pipeline

**Option A: Manual Trigger via UI**
1. Click on the DAG name
2. Click the "Play" button (▶) in the top right
3. Select "Trigger DAG"
4. Click "Trigger" to confirm

**Option B: Trigger via CLI**
```bash
docker compose exec airflow-worker airflow dags trigger etl_title_transform_pipeline
```

### 6. Monitor Execution

**In Airflow UI:**
1. Click on the running DAG instance (colored circle)
2. View the Grid view showing task status
3. Click on the task `etl_title_transform` to see details
4. Click "Log" to view execution logs

**Task Status Indicators:**
- 🟢 Green: Success
- 🔴 Red: Failed
- 🟡 Yellow: Running
- ⚪ White: Queued

### 7. Verify Results

After successful execution, check the output file:

**Option A: From host machine**
```bash
cat database/output.json/part-00000-*.json
```

**Option B: From container**
```bash
docker compose exec airflow-worker cat /opt/airflow/database/output.json/part-00000-*.json
```

Expected output:
```json
{"title":"hello world"}
```

## Detailed Pipeline Steps

### Extract Phase
**What it does:**
- Reads `/opt/airflow/database/input.json`
- Parses JSON into Spark DataFrame
- Validates data structure
- Logs record count and schema

**Expected log output:**
```
EXTRACT PHASE: Reading JSON data
Input path: /opt/airflow/database/input.json
Successfully read 1 records
Input schema:
root
 |-- title: string (nullable = true)
```

### Transform Phase
**What it does:**
- Applies transformation rule: `title = "hello"` → `title = "hello world"`
- Counts modified records
- Preserves other fields (if any)
- Logs transformation statistics

**Expected log output:**
```
TRANSFORM PHASE: Updating title field
Records to process: 1
Transformation complete:
  - Total records processed: 1
  - Records modified: 1
```

### Load Phase
**What it does:**
- Writes transformed DataFrame to JSON
- Overwrites existing output directory
- Uses single partition (coalesce(1)) for single output file
- Validates write success

**Expected log output:**
```
LOAD PHASE: Writing transformed data
Output path: /opt/airflow/database/output.json
Writing 1 records to output
Successfully wrote data to /opt/airflow/database/output.json
```

## Monitoring and Troubleshooting

### Viewing Logs

**Airflow Task Logs:**
1. In Airflow UI, click on task
2. Click "Log" button
3. View real-time streaming logs

**Spark Application Logs:**
1. Open Spark Master UI: http://localhost:8085
2. Click on "Running Applications" or "Completed Applications"
3. Click on the application to see details
4. View stdout/stderr logs

### Common Issues

#### Issue 1: DAG Not Appearing

**Symptom:** DAG doesn't show in Airflow UI

**Solution:**
1. Check DAG file syntax:
   ```bash
   docker compose exec airflow-worker python /opt/airflow/dags/etl_pipeline_dag.py
   ```
2. Check DAG processor logs:
   ```bash
   docker compose logs airflow-dag-processor | grep etl_pipeline
   ```
3. Verify file is in correct location:
   ```bash
   docker compose exec airflow-worker ls -la /opt/airflow/dags/
   ```

#### Issue 2: Input File Not Found

**Symptom:** Error: "Path does not exist: /opt/airflow/database/input.json"

**Solution:**
1. Verify file exists on host:
   ```bash
   ls -la database/
   ```
2. Check volume mount in container:
   ```bash
   docker compose exec airflow-worker ls -la /opt/airflow/database/
   ```
3. Verify docker-compose.yaml has volume mount:
   ```yaml
   volumes:
     - ${AIRFLOW_PROJ_DIR:-.}/database:/opt/airflow/database
   ```
4. Restart containers if mount was just added:
   ```bash
   docker compose restart
   ```

#### Issue 3: Spark Connection Failed

**Symptom:** "Connection refused to spark-master:7077"

**Solution:**
1. Verify Spark Master is running:
   ```bash
   docker compose ps spark-master
   ```
2. Check Spark Master UI: http://localhost:8085
3. Verify connection in Airflow:
   - Go to Admin > Connections
   - Find `spark_standalone_cluster`
   - Ensure Host: `spark://spark-master` and Port: `7077`

#### Issue 4: Permission Denied

**Symptom:** "Permission denied" errors when writing output

**Solution:**
1. Check file permissions:
   ```bash
   ls -la database/
   ```
2. Fix permissions if needed:
   ```bash
   chmod 777 database/
   ```
3. Verify AIRFLOW_UID in .env file matches your user ID

#### Issue 5: Task Stuck in Queued

**Symptom:** Task shows yellow (queued) but never runs

**Solution:**
1. Check Celery worker status:
   ```bash
   docker compose logs airflow-worker | tail -50
   ```
2. Verify worker is registered:
   ```bash
   docker compose exec airflow-worker airflow celery inspect active
   ```
3. Restart worker if needed:
   ```bash
   docker compose restart airflow-worker
   ```

### Viewing Detailed Logs

**Complete pipeline logs:**
```bash
docker compose exec airflow-worker \
  cat /opt/airflow/logs/dag_id=etl_title_transform_pipeline/run_id=*/task_id=etl_title_transform/attempt=*.log
```

**Spark Master logs:**
```bash
docker compose logs spark-master | tail -100
```

**Spark Worker logs:**
```bash
docker compose logs spark-worker | tail -100
```

## Advanced Usage

### Customizing Input Data

Edit `database/input.json` with different content:

```json
{
  "title": "hello",
  "author": "John Doe",
  "created_at": "2025-12-13"
}
```

The pipeline will transform only the title field, preserving other fields.

### Multiple Records

The pipeline supports multiple records:

```json
{"title": "hello", "id": 1}
{"title": "world", "id": 2}
{"title": "hello", "id": 3}
```

After transformation:
```json
{"title": "hello world", "id": 1}
{"title": "world", "id": 2}
{"title": "hello world", "id": 3}
```

### Scheduling the Pipeline

To run on a schedule, edit `dags/etl_pipeline_dag.py`:

```python
# Change schedule from None to cron expression
schedule='0 2 * * *',  # Runs daily at 2 AM
```

Common schedules:
- `'@daily'` - Once per day at midnight
- `'@hourly'` - Once per hour
- `'0 */4 * * *'` - Every 4 hours
- `'0 9 * * 1-5'` - Weekdays at 9 AM

### Configuring Spark Resources

Adjust Spark resources in DAG:

```python
conf={
    'spark.driver.memory': '2g',      # Increase driver memory
    'spark.executor.memory': '2g',    # Increase executor memory
    'spark.executor.cores': '2',      # Use 2 cores per executor
},
```

## Performance Tips

### For Large Files

1. **Increase partition count:**
   ```python
   # In etl_title_transform.py, replace coalesce(1) with:
   df.repartition(10).write.json(output_path)
   ```

2. **Increase Spark memory:**
   ```python
   # In etl_pipeline_dag.py:
   'spark.driver.memory': '4g',
   'spark.executor.memory': '4g',
   ```

3. **Use more workers:**
   ```bash
   # Add more workers in docker-compose.yaml
   docker compose scale spark-worker=3
   ```

### For Better Performance

1. **Enable broadcast joins** (for small lookup tables)
2. **Cache frequently accessed DataFrames**
3. **Partition data** by key columns
4. **Use parquet format** instead of JSON for intermediate data

## Cleanup

### Remove Output Files
```bash
rm -rf database/output.json/
```

### Stop Pipeline
In Airflow UI, toggle DAG to "OFF"

### Reset Pipeline State
```bash
docker compose exec airflow-worker \
  airflow dags delete etl_title_transform_pipeline
```

## Testing

### Test Input File Creation
```bash
echo '{"title": "hello", "test": true}' > database/test_input.json
```

### Dry Run (Validate DAG)
```bash
docker compose exec airflow-worker \
  airflow dags test etl_title_transform_pipeline 2025-01-01
```

### Manual Spark Job Execution
```bash
docker compose exec airflow-worker \
  spark-submit \
    --master spark://spark-master:7077 \
    /opt/spark-jobs/etl_title_transform.py
```

## Success Criteria Checklist

- [ ] All Docker containers running
- [ ] Airflow UI accessible at http://localhost:8080
- [ ] Spark Master UI accessible at http://localhost:8085
- [ ] DAG visible in Airflow UI
- [ ] Spark connection configured (`spark_standalone_cluster`)
- [ ] Input file exists at `database/input.json`
- [ ] Database volume mounted in containers
- [ ] Pipeline can be triggered manually
- [ ] Pipeline completes successfully (green status)
- [ ] Output file created at `database/output.json/`
- [ ] Output contains transformed data: `"title": "hello world"`
- [ ] Logs show all three phases (Extract, Transform, Load)

## Related Documentation

- **Business Requirement:** `documentation/ticket-etl-pipeline.md`
- **Troubleshooting:** `documentation/sparkSubmitOperator-issue.md`
- **Installation Guide:** `README.md`
- **Git Workflow:** `documentation/git-workflow-guide.md`

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review Airflow task logs
3. Check Spark UI for job details
4. Review business requirement ticket
5. Check documentation files

## Next Steps

After successful pipeline execution:
1. Extend transformation logic for more complex rules
2. Add data validation tasks
3. Implement error handling and alerts
4. Schedule pipeline for automated runs
5. Add monitoring and metrics
6. Implement incremental processing
7. Add data quality checks
