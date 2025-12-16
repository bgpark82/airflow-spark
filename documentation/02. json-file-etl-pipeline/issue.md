# 실제 문제: Docker Volume 마운트 누락 (해결됨)

## 핵심 원인

Spark 컨테이너에 필요한 디렉토리가 마운트되지 않아서 발생한 문제였다.

### 문제 상황

**DAG 설정 (`dags/etl_pipeline_dag.py:86`):**
```python
application='/opt/spark-jobs/etl_title_transform.py'
```

**Spark Job 파일 경로 (`spark-jobs/etl_title_transform.py:177`):**
```python
INPUT_PATH = "/opt/airflow/database/input.json"
OUTPUT_PATH = "/opt/airflow/database/output.json"
```

**기존 docker-compose.yaml 볼륨 설정:**

✅ Airflow 컨테이너:
```yaml
volumes:
  - ./spark-jobs:/opt/spark-jobs
  - ./database:/opt/airflow/database
```

❌ Spark 컨테이너 (master & worker):
```yaml
volumes:
  - ./database:/opt/airflow/database  # spark-jobs 마운트 없음!
```

### 왜 에러가 발생했나?

1. Airflow가 Spark 클러스터에 job을 submit
2. Spark master/worker가 `/opt/spark-jobs/etl_title_transform.py` 접근 시도
3. **해당 경로가 컨테이너 내부에 마운트되지 않음** → 파일을 찾을 수 없음
4. `FileNotFoundError` 발생

## 해결 방법

**docker-compose.yaml 수정:**

```yaml
# spark-master
volumes:
  # ✅ 추가: Spark가 PySpark 스크립트에 접근할 수 있도록 마운트
  - ${AIRFLOW_PROJ_DIR:-.}/spark-jobs:/opt/spark-jobs
  # ✅ 유지: 입출력 데이터 파일용 디렉토리
  - ${AIRFLOW_PROJ_DIR:-.}/database:/opt/airflow/database

# spark-worker
volumes:
  # ✅ 추가: Spark가 PySpark 스크립트에 접근할 수 있도록 마운트
  - ${AIRFLOW_PROJ_DIR:-.}/spark-jobs:/opt/spark-jobs
  # ✅ 유지: 입출력 데이터 파일용 디렉토리
  - ${AIRFLOW_PROJ_DIR:-.}/database:/opt/airflow/database
```

### 적용 방법

```bash
docker-compose down
docker-compose up -d
```

### 핵심 교훈

Airflow-Spark 통합 환경에서는:
- **Airflow 컨테이너**: DAG 실행, Spark job submit
- **Spark 컨테이너**: 실제 PySpark 코드 실행

→ **Spark 컨테이너에도 PySpark 스크립트와 데이터 파일 모두 마운트되어야 함**

⸻

# 추가 참고: Spark 캐시 불일치 문제

핵심부터 말하면 Spark가 "이미 존재한다고 믿고 있는 파일/테이블이 실제 스토리지에는 없어서" 발생한 에러다.
로그에 나온 두 문장이 정확히 그 상황을 설명하고 있다.

⸻

에러의 본질

QueryExecutionErrors$.fileNotExistError
You can explicitly invalidate the cache in Spark by running 'REFRESH TABLE tableName'

이 조합이 나오면 99% 확률로 캐시 불일치(cache inconsistency) 문제다.

Spark는 성능 때문에 다음 정보를 캐시에 저장한다.
•	테이블 메타데이터 (파일 경로, 파티션 정보)
•	DataFrame / Dataset lineage
•	파일 리스트 (특히 Parquet, ORC)

그런데 외부에서 실제 파일이 바뀌거나 삭제됨 → Spark는 그걸 모른 채 옛날 파일을 읽으려고 시도 → fileNotExistError

⸻

가장 흔한 원인들 (우선순위 순)

1️⃣ Airflow / 다른 Spark Job이 데이터를 덮어씀 (overwrite)

예시:
•	이전 Spark job:

df.write.mode("overwrite").parquet("/data/events")

	•	현재 Spark job:

SELECT * FROM events

Spark는 기존 파일 경로를 캐시하고 있는데
overwrite로 인해 파일 이름 자체가 바뀜 → 캐시된 파일이 사라짐

✔ 가장 흔한 케이스

⸻

2️⃣ Hive / External Table + 파일 직접 삭제
•	Hive external table
•	S3 / HDFS 경로에 대해
•	수동 삭제
•	lifecycle policy
•	다른 배치가 cleanup 수행

Spark SQL은:

table -> path -> file list (cached)

실제 파일은:

❌ 없음


⸻

3️⃣ Spark Session 재사용 (Airflow에서 특히 흔함)

Airflow SparkSubmitHook 사용 시:
•	같은 application name
•	YARN cluster 모드
•	long-lived Spark session

👉 이전 태스크의 캐시가 살아 있음

⸻

4️⃣ 파티션 추가/삭제 후 MSCK REPAIR / REFRESH 안 함
•	날짜 파티션 구조
•	새로운 파티션 생성 or 삭제
•	Spark는 여전히 옛 파티션 기준으로 읽음

⸻

왜 에러 메시지에 “REFRESH TABLE”이 나오나?

Spark가 친절하게 힌트를 준다:

“내가 캐시를 들고 있는데, 현실이랑 안 맞아. 직접 무효화해라.”

즉:
•	Spark 잘못 ❌
•	메타데이터 싱크 문제 ⭕️

⸻

즉각적인 해결 방법 (응급처치)

✅ SQL 기준

REFRESH TABLE tableName;

또는

UNCACHE TABLE tableName;
REFRESH TABLE tableName;


⸻

✅ DataFrame 기준

spark.catalog.clearCache()

또는

df.unpersist()


⸻

✅ Airflow에서 가장 확실한 방법
•	Spark job 새 application name
•	Spark session 재사용 금지
•	필요 시 job 시작 시 강제 refresh

spark.sql("REFRESH TABLE tableName")


⸻

구조적인 해결 (재발 방지)

✔ overwrite 패턴 개선

// ❌ 위험
mode("overwrite")

// ⭕️ 권장
mode("overwrite")
.option("overwriteSchema", "true")

또는
•	날짜별 path 분리
•	atomic write 패턴 사용

⸻

✔ Airflow DAG 설계
•	upstream job → downstream job 사이에 파일 변경 있음
•	downstream 시작 시 항상:

REFRESH TABLE


⸻

✔ S3 / HDFS cleanup job 확인
•	lifecycle policy
•	vacuum / cleanup job
•	retention 설정

⸻

5살에게 설명하면

스파크는 “이 상자에 장난감이 있어”라고 기억하고 있었어.
그런데 누군가 몰래 장난감을 치워버렸어.
그래서 스파크가 상자를 열었는데 “어? 없어!” 하고 놀란 거야.
그래서 “내 기억을 다시 정리할게”라고 말하는 게 REFRESH TABLE이야.

⸻

질문을 조금 더 정확히 고치면

❌ 원래 질문

a. 원인이 뭐야

⭕️ 더 좋은 질문

Airflow에서 Spark job 실행 중 fileNotExistError가 발생했는데, 외부 overwrite나 캐시 불일치로 발생했을 가능성이 있나?

---

“상태없음” 에러라는 표현은 Airflow UI에서 Task Instance의 상태가 None으로 표시되는 상황을 말하는 것 같아.
즉, 태스크가 아직 실행되지 않았거나, Airflow가 상태를 제대로 읽지 못할 때 나타나는 상태야.

⸻

원인 분석

Airflow에서 Task Instance 상태가 None으로 나오는 대표적인 이유는 다음과 같아:

⸻

1️⃣ DAG가 아직 스케줄되지 않음
•	DAG가 Airflow scheduler에 의해 감지되지 않은 상태
•	scheduler가 새 DAG 파일을 읽기 전까지는 상태가 없음

⸻

2️⃣ 태스크가 아직 예약되지 않음
•	DAG 파일은 존재하지만, scheduler가 태스크를 queue에 넣지 않은 상태
•	Triggered 하지 않았거나, start_date가 현재보다 미래

⸻

3️⃣ DAG 또는 Task가 database와 sync되지 않음
•	Airflow metadata DB에서 TaskInstance row가 생성되지 않음
•	흔히 다음 경우 발생
•	airflow db upgrade/migrate 미실행
•	scheduler가 충분히 오래 실행되지 않음

⸻

4️⃣ Airflow worker가 정상적으로 실행되지 않음
•	CeleryExecutor, LocalExecutor, KubernetesExecutor 등
•	Worker가 down이거나 queue 연결 문제
•	DAG가 scheduler에 의해 queue에 넣어졌지만 worker가 가져가지 못함

⸻

5️⃣ DAG 파일이 변경되었거나, import 에러 존재
•	DAG가 로드되지 않으면 Airflow는 해당 DAG에 대해 아무 상태도 기록하지 않음
•	DAG 파싱 에러가 있는 경우도 포함

⸻

확인 방법
1.	Scheduler 로그 확인

docker logs airflow-scheduler

	•	DAG가 감지되고 있는지 확인
	•	태스크가 queue에 들어가는 로그 확인

	2.	Worker 로그 확인

docker logs airflow-worker

	•	CeleryExecutor 환경이면 worker가 태스크 가져가는지 확인

	3.	DAG 상태 확인

airflow dags list
airflow tasks list <dag_id>

	•	태스크가 정상적으로 등록되어 있는지

	4.	Start date 확인

	•	태스크가 실행되려면 start_date <= execution_date 여야 함
	•	흔히 start_date를 미래로 잡아서 실행 안 되는 경우 있음

⸻

5살에게 설명하면

에어플로우는 “이 일을 언제 시작할까?”를 기록하는 노트가 있어.
근데 아직 노트에 “시작” 표시가 안 되어 있으면, 상태가 “없음”으로 나오는 거야.
즉, Airflow가 아직 “이 일을 시작할 준비가 됐다”라고 기록하지 않은 상태야.

⸻

질문을 더 정확하게 고치면

❌ 원래 질문

airflow에서 상태없음 에러는 왜 나오는거야

⭕️ 더 정확한 질문

Airflow UI에서 Task Instance가 None 상태로 나올 때, scheduler/worker/metadata DB 관점에서 어떤 원인들이 있을까?

---

# Spark 3.4+ JSON 읽기 에러 (해결됨)

## 에러 메시지

```
[UNSUPPORTED_FEATURE.QUERY_ONLY_CORRUPT_RECORD_COLUMN] The feature is not supported:
Queries from raw JSON/CSV/XML files are disallowed when the referenced columns only
include the internal corrupt record column (named `_corrupt_record` by default).
```

## 핵심 원인

Spark 3.4 이상 버전에서는 raw JSON/CSV/XML 파일에 대해 직접 쿼리(count, show 등)를 실행할 수 없다.
파일을 읽은 후 반드시 `.cache()` 또는 `.persist()`를 호출하여 DataFrame을 메모리에 저장해야 한다.

### 문제 코드 (`spark-jobs/etl_title_transform.py:65`)

```python
# ❌ Spark 3.4+에서 에러 발생
df = spark.read.json(input_path)
row_count = df.count()  # 여기서 에러 발생
```

### 왜 에러가 발생했나?

1. `spark.read.json()`은 lazy evaluation으로 실제 파일을 읽지 않고 plan만 생성
2. `df.count()`를 호출할 때 실제로 파일을 읽으려고 시도
3. Spark 3.4+의 보안/성능 정책으로 raw 파일에 대한 직접 쿼리 차단
4. `UNSUPPORTED_FEATURE.QUERY_ONLY_CORRUPT_RECORD_COLUMN` 에러 발생

## 해결 방법

**spark-jobs/etl_title_transform.py 수정:**

```python
# ✅ .cache()를 추가하여 DataFrame을 메모리에 저장
df = spark.read.json(input_path).cache()

# 이제 count, show 등의 operation 실행 가능
row_count = df.count()
```

### 핵심 교훈

Spark 3.4 이상에서 JSON/CSV/XML 파일을 다룰 때:
- **즉시 `.cache()` 호출**: 파일을 읽은 후 바로 DataFrame을 메모리에 저장
- **에러 메시지 주의**: Spark가 제안하는 해결책(`cache()` 사용)을 따를 것
- **버전 업그레이드 시**: Spark 버전별 breaking changes 확인 필요

### 참고

에러 메시지에서 제안한 해결책:
```
Instead, you can cache or save the parsed results and then send the same query.
For example, `val df = spark.read.schema(schema).json(file).cache()` and then
`df.filter($"_corrupt_record".isNotNull).count()`.
```

---
원인을 찾았습니다\! 보여주신 JSON 형식과 Spark의 기본 동작 방식 사이의 불일치 때문입니다.

### 1\. 문제의 핵심: JSON 포맷 불일치

Spark는 기본적으로 **`Line-delimited JSON` (한 줄에 하나의 JSON 객체)** 형식을 기대합니다. 하지만 보여주신 파일은 여러 줄로 이루어진 **`Multi-line JSON`** 형식입니다.

* **Spark가 보는 방식:** 각 줄을 하나의 데이터로 인식하려고 합니다.
    * 1행: `{` -\> **에러\!** (`_corrupt_record`에 저장)
    * 2행: `"title": "hello"` -\> **에러\!** (독립적인 JSON이 아님)
    * 3행: `}` -\> **에러\!**
* **결과:** 모든 줄이 파싱에 실패하여 정상적인 `title` 컬럼은 안 만들어지고, 오직 에러 기록(`_corrupt_record`)만 남게 됩니다. 이 상태에서 `count()`를 하니 아까 보신 에러가 발생하는 것입니다.

-----

### 2\. 해결 방법: `multiLine` 옵션 추가

코드를 아래와 같이 수정하면 해결됩니다. `option("multiLine", "true")`를 추가하는 것이 핵심입니다.

```python
def extract_data(spark, input_path):
    # ... (생략)
    try:
        # .option("multiLine", "true")를 추가하여 
        # 한 줄이 아닌 여러 줄로 구성된 하나의 JSON 파일을 읽을 수 있게 합니다.
        df = spark.read.option("multiLine", "true").json(input_path).cache()

        # 이제 정상적으로 title 컬럼이 인식되므로 count()가 에러 없이 작동합니다.
        row_count = df.count()
        logger.info(f"Successfully read {row_count} records")

        # ... (이하 동일)
```

-----

### 3\. 왜 전에는 안 됐고, 왜 지금 에러가 날까?

1.  **데이터 부족:** 파일에 정상적으로 파싱된 컬럼이 **단 하나도 없기 때문**입니다.
2.  **Spark 4.0/3.x의 규칙:** "정상 데이터가 아예 없는(Empty or All Corrupt) 상태에서 분석을 진행하는 것은 무의미한 연산"이라고 판단하여 차단하는 보안 장치입니다.

### 4\. (참고) 파일 형식을 바꿀 수 있다면?

만약 파일을 아래와 같이 **한 줄**로 고칠 수 있다면 `multiLine` 옵션 없이도 현재 코드 그대로 잘 작동합니다.

```json
{"title": "hello"}
```

-----

**결론:**
가장 쉬운 해결책은 `extract_data` 함수 내 `spark.read.json(input_path)` 부분을 \*\*`spark.read.option("multiLine", "true").json(input_path)`\*\*로 수정하는 것입니다.

수정 후 다시 Airflow에서 실행해 보시겠어요? 이제 `df.show()`에서 예쁘게 출력되는 데이터를 확인하실 수 있을 겁니다\!