네, 제공해주신 `docker-compose.yaml` 파일에 `RUN pip install apache-airflow-providers-apache-spark` 명령어를 **직접 추가할 수는 없습니다.**

### 🚫 직접 추가할 수 없는 이유

`docker-compose.yaml` 파일은 Docker 컨테이너를 실행하기 위한 설정 파일이지, **Docker 이미지를 빌드하는 명령어(`RUN`)를 정의하는 파일**이 아닙니다. `RUN` 명령어는 이미지를 만드는 데 사용되는 \*\*`Dockerfile`\*\*에 포함되어야 합니다.

현재 `docker-compose.yaml` 파일은 Airflow 컨테이너의 이미지로 `$AIRFLOW_IMAGE_NAME` 환경 변수를 사용하도록 설정되어 있으며, 이는 기본적으로 이미 빌드된 공식 이미지 `apache/airflow:3.1.5`를 사용합니다.

```yaml
# docker-compose.yaml 파일의 관련 부분
x-airflow-common:
  &airflow-common
  image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:3.1.5}
  # build: .  <-- 이 부분이 현재 주석 처리되어 있습니다.
```

### ✅ 해결 방법: 커스텀 Dockerfile을 통한 확장

Spark 프로바이더를 설치하려면, 공식 Airflow 이미지를 기반으로 **새로운 커스텀 이미지**를 빌드하도록 설정을 변경해야 합니다.

다음 단계를 따라야 합니다.

#### 1단계: `Dockerfile` 작성

`docker-compose.yaml` 파일이 있는 동일한 디렉토리에 `Dockerfile`이라는 이름의 파일을 생성하고 다음 내용을 추가합니다.

```dockerfile
# Dockerfile
# 공식 Airflow 이미지를 기본 이미지로 사용
FROM apache/airflow:3.1.5 

# 필요한 Spark Provider 패키지를 설치합니다.
# Airflow 이미지에는 이미 pip가 설치되어 있습니다.
RUN pip install apache-airflow-providers-apache-spark
```

#### 2단계: `docker-compose.yaml` 수정

`x-airflow-common` 섹션에서 **이미지(image) 사용을 주석 처리**하고 **빌드(build) 기능을 활성화**하여, 방금 만든 `Dockerfile`을 사용하도록 변경합니다.

```yaml
x-airflow-common:
  &airflow-common
  # image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:3.1.5}  <- 이 줄을 주석 처리하거나 제거
  build: .                                             # <- 이 줄의 주석을 해제
  env_file:
# ... (나머지 설정은 그대로 둡니다.)
```

#### 3단계: Docker Compose 재실행

수정된 `docker-compose.yaml` 파일과 `Dockerfile`을 사용하여 서비스를 빌드하고 시작합니다.

```bash
# Dockerfile을 사용하여 새 이미지를 빌드합니다.
docker compose build

# 서비스를 시작합니다.
docker compose up
```

이렇게 하면 `airflow-worker`, `airflow-scheduler` 등 모든 Airflow 관련 서비스 컨테이너가 Spark 프로바이더가 설치된 새로운 커스텀 이미지를 사용하게 되어 `ModuleNotFoundError` 문제를 해결할 수 있습니다.