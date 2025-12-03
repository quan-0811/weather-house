FROM apache/airflow:2.7.1

USER root

RUN apt-get update && \
    apt-get install -y docker.io && \
    apt-get clean

USER airflow