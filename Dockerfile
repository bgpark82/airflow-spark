# Dockerfile
# 공식 Airflow 이미지를 기본 이미지로 사용
# Python 3.12 기반
FROM apache/airflow:3.1.5-python3.10

# 필요한 Spark Provider 패키지를 설치합니다.
# Airflow 이미지에는 이미 pip가 설치되어 있습니다.
RUN pip install apache-airflow-providers-apache-spark

# 2. Java 설치 및 환경 변수 설정
# apt-get을 사용하기 위해 임시로 root 권한으로 전환
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jdk && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. Spark 바이너리 설치 (예시: Spark 3.5.7)
ENV SPARK_VERSION=4.0.1
ENV HADOOP_VERSION=3
ENV SPARK_HOME="/opt/spark"

RUN mkdir -p ${SPARK_HOME} && \
    curl -o /tmp/spark.tgz "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz" && \
    tar -xzf /tmp/spark.tgz --directory ${SPARK_HOME} --strip-components 1 && \
    rm /tmp/spark.tgz

# 4. 환경 변수 설정
# Java 설치 후 실제 Java 홈 경로를 찾아서 사용합니다.
# /usr/lib/jvm/java-17-openjdk-amd64 이 경로가 정확하다면 그대로 사용합니다.
# 그렇지 않다면 아래처럼 update-alternatives로 찾거나 심볼릭 링크를 사용합니다.
ENV JAVA_HOME="/usr/lib/jvm/java-17-openjdk-arm64"
ENV PATH="${JAVA_HOME}/bin:${SPARK_HOME}/bin:${SPARK_HOME}/sbin:${PATH}"

# Airflow 사용자에게 소유권 부여
RUN chown -R airflow:0 ${SPARK_HOME}

# 다시 비-root 사용자로 전환
USER airflow