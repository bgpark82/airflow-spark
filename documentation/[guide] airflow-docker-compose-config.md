제공해주신 Apache Airflow 공식 문서를 참고하여, 초보자도 쉽게 따라 할 수 있는 Airflow 실행 환경 설정 및 실행 방법을 안내해 드립니다.

Airflow 공식 문서에서는 가장 간단하게 Airflow를 실행하기 위해 이미 잘 정의된 `docker-compose.yaml` 파일을 다운로드하여 사용하는 방법을 권장합니다.

직접 `docker-compose.yaml` 파일을 작성하는 대신, 다음 단계를 따라 공식 파일을 다운로드하고 환경을 설정하는 것이 가장 쉽고 빠릅니다.

-----

## 🚀 Airflow Docker Compose로 실행하기 (간단 버전)

### 1단계: 파일 및 환경 설정

먼저 Airflow 프로젝트를 위한 디렉토리를 만들고, 해당 디렉토리로 이동하세요.

```bash
mkdir airflow_home
cd airflow_home
```

#### 1\. `docker-compose.yaml` 파일 다운로드

최신 안정 버전의 `docker-compose.yaml` 파일을 다운로드합니다. 이 파일은 Airflow 실행에 필요한 모든 서비스(스케줄러, 웹서버, Postgres DB, Redis 등)를 포함하고 있습니다.

```bash
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/stable/docker-compose.yaml'
```

#### 2\. 필수 디렉토리 및 사용자 ID(`.env` 파일) 설정

Airflow가 DAG 파일, 로그 등을 저장할 로컬 디렉토리를 생성하고, 권한 문제를 피하기 위해 사용자 ID를 환경 변수로 설정합니다.

* **Linux/macOS 사용자:**
  ```bash
  mkdir -p ./dags ./logs ./plugins ./config
  echo -e "AIRFLOW_UID=$(id -u)" > .env
  ```
  *(이 명령은 현재 사용자의 UID를 `.env` 파일에 기록하여 컨테이너 내 Airflow 프로세스의 사용자 권한을 호스트와 일치시킵니다.)*
* **Windows 사용자 (WSL/Git Bash가 아닌 경우):**
  수동으로 `.env` 파일을 생성하고 다음 내용을 입력하세요.
  ```
  AIRFLOW_UID=50000
  ```

### 2단계: 데이터베이스 초기화 (첫 실행 시 필수)

Airflow를 처음 실행하기 전에 데이터베이스 마이그레이션을 실행하고 기본 관리자 계정을 생성해야 합니다.

```bash
docker compose up airflow-init
```

이 작업이 완료되면, 로그 마지막에 `exited with code 0`과 같은 성공 메시지가 나타납니다.

### 3단계: Airflow 실행

이제 모든 Airflow 서비스를 시작할 수 있습니다.

```bash
docker compose up
```

서비스를 백그라운드에서 실행하려면 `-d` 옵션을 추가합니다.

```bash
docker compose up -d
```

### 4단계: 웹 UI 접속

모든 컨테이너가 정상적으로 실행된 후 (약 1\~2분 소요), 웹 브라우저를 열고 다음 주소로 접속하세요.

* **주소:** `http://localhost:8080`

#### 기본 로그인 정보:

| 항목 | 값 |
| :--- | :--- |
| **사용자 이름 (Username)** | `airflow` |
| **비밀번호 (Password)** | `airflow` |

-----

## 📋 참고: 다운로드된 `docker-compose.yaml`의 주요 구성 요소 (초보자 설명)

다운로드한 `docker-compose.yaml` 파일에는 Airflow를 실행하기 위한 최소한의 구성 요소들이 포함되어 있습니다.

| 서비스 이름 | 역할 (무엇을 하는가?) |
| :--- | :--- |
| **`postgres`** | Airflow의 메타데이터(DAG 상태, 태스크 실행 기록, 연결 정보 등)를 저장하는 데이터베이스 |
| **`redis`** | Celery Executor를 사용할 때 스케줄러와 워커 간의 메시지를 전달하는 브로커 |
| **`airflow-scheduler`** | DAG 파일을 모니터링하고, 정의된 스케줄에 따라 태스크를 실행하도록 예약하는 핵심 서비스 |
| **`airflow-webserver`** | DAG 관리, 태스크 상태 확인, 연결/변수 설정 등을 위한 웹 사용자 인터페이스 (Web UI) |
| **`airflow-worker`** | 스케줄러가 지시한 실제 태스크를 실행하는 작업자 서비스 |
| **`airflow-init`** | Airflow를 처음 시작할 때 데이터베이스를 초기화하는 일회성 서비스 |

이 구성을 통해 Airflow의 모든 핵심 기능을 하나의 `docker compose up` 명령으로 쉽게 실행할 수 있습니다.