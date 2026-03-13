FROM apache/spark:3.5.0

USER root
# Install Python dependencies
RUN pip install pyspark==3.5.0 kafka-python

# Define versions for consistency
ARG KAFKA_VERSION=3.5.0
ARG SPARK_VERSION=3.5.0

# Download the exact compatible JARs for Spark 3.5.0
ADD https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/${SPARK_VERSION}/spark-sql-kafka-0-10_2.12-${SPARK_VERSION}.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/${KAFKA_VERSION}/kafka-clients-${KAFKA_VERSION}.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/${SPARK_VERSION}/spark-token-provider-kafka-0-10_2.12-${SPARK_VERSION}.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/org/postgresql/postgresql/42.6.0/postgresql-42.6.0.jar /opt/spark/jars/

WORKDIR /app
COPY . /app

# Ensure checkpoints directory exists and has permissions
RUN mkdir -p /app/checkpoints && chmod -R 777 /app/checkpoints

# Explicitly include all downloaded jars in the spark-submit command
CMD ["spark-submit", \
     "--master", "local[*]", \
     "--jars", "/opt/spark/jars/spark-sql-kafka-0-10_2.12-3.5.0.jar,/opt/spark/jars/kafka-clients-3.5.0.jar,/opt/spark/jars/spark-token-provider-kafka-0-10_2.12-3.5.0.jar,/opt/spark/jars/postgresql-42.6.0.jar,/opt/spark/jars/commons-pool2-2.11.1.jar", \
     "spark_app.py"]