# Ticket: ETL Pipeline for Title Transformation

## Ticket Information
- **Ticket ID:** AIRFLOW-001
- **Type:** Feature
- **Priority:** Medium
- **Status:** To Do
- **Created:** 2025-12-13
- **Assignee:** Data Engineering Team

## Business Requirement

### Overview
Implement an ETL (Extract, Transform, Load) pipeline using Apache Airflow and PySpark to automate the transformation of JSON data files. The pipeline should read JSON input, transform specific fields, and store the results.

### Business Value
- **Automation:** Eliminate manual data transformation processes
- **Scalability:** Leverage Spark's distributed computing for large datasets
- **Reliability:** Use Airflow's orchestration for reliable, scheduled execution
- **Auditability:** Track data transformations with Airflow task logs

### User Story
```
As a Data Engineer,
I want an automated ETL pipeline that transforms title fields in JSON files,
So that I can process data consistently without manual intervention.
```

## Functional Requirements

### 1. Extract Phase (Task 1)
**Requirement:** Read JSON data from source file

- **Input Location:** `/opt/airflow/database/input.json`
- **Input Format:** JSON file with structure:
  ```json
  {
    "title": "hello"
  }
  ```
- **Expected Behavior:**
  - Read JSON file using PySpark
  - Parse into Spark DataFrame
  - Validate JSON structure
  - Handle missing files gracefully with appropriate error messages

### 2. Transform Phase (Task 2)
**Requirement:** Transform title field value

- **Input:** DataFrame from Extract phase
- **Transformation Rule:**
  - Find all records where `title = "hello"`
  - Replace with `title = "hello world"`
- **Expected Behavior:**
  - Apply transformation using PySpark DataFrame operations
  - Preserve all other fields unchanged
  - Log transformation statistics (rows processed, rows modified)
  - Handle edge cases (null values, empty strings)

### 3. Load Phase (Task 3)
**Requirement:** Store transformed data to output file

- **Output Location:** `/opt/airflow/database/output.json`
- **Output Format:** JSON file with transformed data
- **Expected Output Structure:**
  ```json
  {
    "title": "hello world"
  }
  ```
- **Expected Behavior:**
  - Write DataFrame to JSON format
  - Overwrite existing output file if present
  - Ensure data integrity (no partial writes)
  - Validate output file creation

## Technical Requirements

### Technology Stack
- **Orchestration:** Apache Airflow 3.1.5
- **Processing Engine:** Apache Spark 4.0.1
- **Operator:** SparkSubmitOperator
- **Language:** Python 3.10 / PySpark

### Pipeline Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Airflow DAG                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐  │
│  │   Extract    │─────▶│  Transform   │─────▶│   Load    │  │
│  │              │      │              │      │           │  │
│  │ Read JSON    │      │ Update Title │      │ Write JSON│  │
│  │ from input   │      │ hello →      │      │ to output │  │
│  │              │      │ hello world  │      │           │  │
│  └──────────────┘      └──────────────┘      └───────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
           │                       │                    │
           ▼                       ▼                    ▼
    ┌──────────────┐      ┌──────────────┐    ┌──────────────┐
    │ Spark Driver │      │ Spark Worker │    │ Spark Worker │
    └──────────────┘      └──────────────┘    └──────────────┘
```

### File Paths
- **Input File:** `/opt/airflow/database/input.json`
- **Output File:** `/opt/airflow/database/output.json`
- **Spark Job:** `/opt/spark-jobs/etl_title_transform.py`
- **DAG File:** `/opt/airflow/dags/etl_pipeline_dag.py`

### Configuration
- **DAG Configuration:**
  - DAG ID: `etl_title_transform_pipeline`
  - Schedule: Manual trigger (None) or configurable cron
  - Catchup: False
  - Tags: ['etl', 'spark', 'transformation']

- **Spark Configuration:**
  - Connection ID: `spark_standalone_cluster`
  - Deploy Mode: Client mode
  - Executor Memory: 1g (configurable)
  - Driver Memory: 1g (configurable)

## Non-Functional Requirements

### Performance
- Pipeline should complete within 5 minutes for input files < 100MB
- Should handle files up to 1GB without memory issues
- Spark job should utilize available worker resources efficiently

### Reliability
- Pipeline should retry failed tasks (max 3 retries with exponential backoff)
- Should handle partial failures gracefully
- Should not corrupt existing output files on failure

### Observability
- All tasks must log execution start and end times
- Transformation statistics should be logged (rows read, transformed, written)
- Airflow UI should display task status and logs
- Spark UI should be accessible for job monitoring

### Error Handling
- Invalid JSON should raise clear error messages
- Missing input file should fail gracefully with descriptive error
- Disk full or permission issues should be caught and reported
- All errors should be logged to Airflow task logs

## Acceptance Criteria

### Success Criteria
- [ ] Input JSON file is successfully read by PySpark
- [ ] Title field "hello" is transformed to "hello world"
- [ ] Transformed data is written to output.json
- [ ] All three tasks complete successfully in Airflow UI
- [ ] Output file contains correct transformed data
- [ ] Pipeline can be triggered manually from Airflow UI
- [ ] Logs show clear execution flow for each task
- [ ] Pipeline completes within expected time (< 5 minutes)

### Test Cases

#### Test Case 1: Happy Path
**Given:** input.json exists with `{"title": "hello"}`
**When:** Pipeline is triggered
**Then:**
- Extract task completes successfully
- Transform task changes title to "hello world"
- Load task creates output.json with `{"title": "hello world"}`
- All tasks show success status

#### Test Case 2: Missing Input File
**Given:** input.json does not exist
**When:** Pipeline is triggered
**Then:**
- Extract task fails with clear error message
- Subsequent tasks are skipped
- Error is logged in Airflow

#### Test Case 3: Invalid JSON
**Given:** input.json contains invalid JSON syntax
**When:** Pipeline is triggered
**Then:**
- Extract task fails during JSON parsing
- Error message indicates JSON parsing failure
- No partial output file is created

#### Test Case 4: Re-run Pipeline
**Given:** Pipeline has run successfully once
**When:** Pipeline is triggered again
**Then:**
- Output.json is overwritten with new results
- No duplicate data is created
- Pipeline completes successfully

## Implementation Plan

### Phase 1: PySpark Job Development
1. Create `etl_title_transform.py` with three main functions:
   - `extract_data()`: Read JSON from input path
   - `transform_data()`: Apply title transformation
   - `load_data()`: Write to output path
2. Add logging and error handling
3. Test locally with sample data

### Phase 2: Airflow DAG Development
1. Create `etl_pipeline_dag.py` with three tasks
2. Configure SparkSubmitOperator for each task
3. Define task dependencies (extract >> transform >> load)
4. Add task documentation and descriptions

### Phase 3: Integration Testing
1. Deploy PySpark job to `/opt/spark-jobs/`
2. Deploy DAG to `/opt/airflow/dags/`
3. Verify Spark connection configuration
4. Trigger pipeline and verify execution

### Phase 4: Validation
1. Verify output.json contains correct data
2. Check Airflow task logs for each phase
3. Monitor Spark UI during execution
4. Validate error handling scenarios

## Dependencies

### Prerequisites
- Apache Airflow 3.1.5 running with CeleryExecutor
- Apache Spark 4.0.1 standalone cluster operational
- Spark connection `spark_standalone_cluster` configured in Airflow
- Java 17 installed in Airflow worker container
- Volume mount for `/opt/airflow/database/` directory

### External Dependencies
- None (self-contained pipeline)

## Risks and Mitigation

### Risk 1: Volume Mount Issues
**Risk:** Database directory not properly mounted in containers
**Mitigation:**
- Add volume mount in docker-compose.yaml
- Verify mount before running pipeline
- Add health check for directory existence

### Risk 2: Spark Memory Issues
**Risk:** Large files may cause out-of-memory errors
**Mitigation:**
- Configure appropriate Spark executor memory
- Implement data partitioning for large files
- Monitor memory usage during execution

### Risk 3: File Locking
**Risk:** Concurrent pipeline runs may conflict
**Mitigation:**
- Set DAG max_active_runs = 1
- Implement file locking mechanism if needed
- Use unique output file names with timestamps

## Rollback Plan

If pipeline fails in production:
1. Pause DAG in Airflow UI
2. Verify input data integrity
3. Check Spark cluster health
4. Review error logs
5. Fix issues and re-deploy
6. Test with sample data before resuming

## Documentation

### Required Documentation
- [ ] README update with ETL pipeline usage
- [ ] Code comments in PySpark job
- [ ] DAG documentation string
- [ ] Operational runbook for troubleshooting

## Success Metrics

### Key Performance Indicators (KPIs)
- **Pipeline Success Rate:** > 95% successful runs
- **Average Execution Time:** < 5 minutes
- **Data Accuracy:** 100% correct transformations
- **Error Recovery:** < 15 minutes to identify and resolve issues

## Sign-off

- **Business Owner:** _________________ Date: _______
- **Technical Lead:** _________________ Date: _______
- **QA Lead:** _________________ Date: _______

## Notes

- This is a basic ETL pipeline that can be extended for more complex transformations
- Future enhancements may include data validation, schema evolution, and incremental processing
- Consider adding data quality checks in future iterations
