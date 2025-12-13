# 공식 Spark 이미지를 기본 이미지로 사용
FROM apache/spark:3.5.7

# Python 3.12를 설치합니다. (Debian/Ubuntu 기반 이미지라고 가정)
USER root
RUN apt-get update && \
    # 'python3.12' 대신 'python3' 관련 일반 패키지 및 build-essential 설치 시도
    apt-get install -y --no-install-recommends \
        python3 \
        python3-dev \
        python3-pip \
        build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 파이썬 실행 경로를 PYSPARK_PYTHON에 명시합니다.
# 이렇게 하면 Spark가 PySpark 작업을 실행할 때 3.12 버전을 사용하도록 강제됩니다.
ENV PYSPARK_PYTHON=/usr/bin/python3.12

# 사용자 권한을 기본 Spark 사용자(일반적으로 spark)로 복원 (선택 사항)
# USER spark