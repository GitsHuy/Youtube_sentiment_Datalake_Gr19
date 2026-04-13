FROM apache/spark:v3.3.0

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip curl \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && pip3 install --no-cache-dir pyspark==3.3.0 transformers==4.41.2 sentencepiece==0.2.0 "numpy<2" \
    && pip3 install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.2.2 \
    && curl -fsSL -o /opt/spark/jars/spark-sql-kafka-0-10_2.12-3.3.0.jar https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.3.0/spark-sql-kafka-0-10_2.12-3.3.0.jar \
    && curl -fsSL -o /opt/spark/jars/spark-token-provider-kafka-0-10_2.12-3.3.0.jar https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.3.0/spark-token-provider-kafka-0-10_2.12-3.3.0.jar \
    && curl -fsSL -o /opt/spark/jars/kafka-clients-2.8.1.jar https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/2.8.1/kafka-clients-2.8.1.jar \
    && curl -fsSL -o /opt/spark/jars/commons-pool2-2.11.1.jar https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar \
    && curl -fsSL -o /opt/spark/jars/jsr305-3.0.0.jar https://repo1.maven.org/maven2/com/google/code/findbugs/jsr305/3.0.0/jsr305-3.0.0.jar \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PYSPARK_PYTHON=/usr/bin/python3
