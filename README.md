# Real-Time Streaming Data Pipeline with Kafka and Spark

## 1. Project Overview

This project implements a **real-time data engineering pipeline** that captures user activity events using **Apache Kafka**, processes them with **Apache Spark Structured Streaming**, and writes results to multiple storage layers.

The pipeline demonstrates key streaming concepts such as:

- Kafka event ingestion
- Spark Structured Streaming processing
- Windowed aggregations
- Stateful session tracking
- Watermark handling for late data
- Multi-sink architecture

### Data Flow
```bash
User Activity Events → Kafka → Spark Streaming → Multiple Outputs
```
Outputs:

- **PostgreSQL** → Real-time analytics layer  
- **Parquet Data Lake** → Historical storage  
- **Kafka Enriched Topic** → Downstream messaging layer  

---

# 2. Technologies Used

- Apache Kafka
- Apache Spark Structured Streaming
- PostgreSQL
- Docker & Docker Compose
- Python
- Parquet

---

# 3. Prerequisites

Before running the project ensure the following are installed:

- Docker
- Docker Compose

---

# 4. Project Structure
```bash
kafka-spark-pipeline
│
├── docker-compose.yml
├── .env.example
├── Dockerfile
├── requirements.txt
├── spark_app.py
├── init-db.sql
├── scripts
│     └── producer.py
│
├── checkpoints/
├── data
│     └── lake
└── README.md
```

---

# 5. Execution Steps
## Step 1: Project Folder Cleanup

Ensure the project directory contains only source files and remove any leftover streaming state.

```bash
rm -Recurse -Force ./checkpoints/*
rm -Recurse -Force ./data/lake/*
```
This prevents Spark checkpoint conflicts from previous runs.

## Step 2: Start the Infrastructure

Start all services using Docker Compose.
```bash
docker-compose up -d --build
```
This command builds and launches the following containers:

- Zookeeper

- Kafka

- PostgreSQL

- Spark container

### Verify containers are running:
After 60 seconds for all services to pass their health checks. You can verify the status using
```bash
docker ps
```
Expected containers:

- kafka-spark-pipeline-zookeeper-1
- kafka-spark-pipeline-kafka-1
- kafka-spark-pipeline-db-1
- kafka-spark-pipeline-spark-app-1

## step 3: Create the Ingestion Topic
Manually create the user_activity topic in Kafka.
```bash
docker exec -it kafka-spark-pipeline-kafka-1 kafka-topics --create --topic user_activity --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

## Step 4: Run the Spark Application
Run the Spark application. This command includes the necessary Kafka and PostgreSQL drivers.
```bash
docker exec -it kafka-spark-pipeline-spark-app-1 spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.5.0 /app/spark_app.py
```
- This starts the Spark streaming pipeline.

- Keep this terminal open to monitor logs.

Note: Keep this terminal open. Wait until you see Streaming query has been idle and waiting for new data before proceeding.

## Step 5: Generate Live Events
Open a new terminal window and start the Kafka producer:
```bash
docker exec -it kafka-spark-pipeline-kafka-1 kafka-console-producer --bootstrap-server localhost:9092 --topic user_activity
```
Paste the following events one at a time:
```bash
{"event_time": "2026-03-13T20:35:00Z", "user_id": "user_video_01", "page_url": "/home", "event_type": "page_view"}
{"event_time": "2026-03-13T20:41:00Z", "user_id": "user_video_01", "page_url": "/login", "event_type": "session_start"}
{"event_time": "2026-03-13T20:43:00Z", "user_id": "user_video_01", "page_url": "/logout", "event_type": "session_end"}
{"event_time": "2026-03-13T20:55:00Z", "user_id": "trigger_msg", "page_url": "/home", "event_type": "page_view"}
```
- Wait 15 seconds for the watermark to process, then press Ctrl+C to exit the producer.

## 6. Verification Steps

These steps confirm that the pipeline is working correctly.

### 6.1 Verify PostgreSQL Output

#### Check whether the session duration was calculated(Stream-Stream Join)
```bash
docker exec -it kafka-spark-pipeline-db-1 psql -U postgres -d streaming_db -c "SELECT * FROM user_sessions;"
```
Example output:
```bash
 user_id    |     start_time      |      end_time       | duration_seconds 
---------------+---------------------+---------------------+------------------
 user_video_01 | ---------------- | ------------------- |          120
(1 row)
```

#### Check Windowed page view counts:
```bash
docker exec -it kafka-spark-pipeline-db-1 psql -U postgres -d streaming_db -c "SELECT * FROM page_view_counts;"
```

### Check Active Users Counts:
```bash
docker exec -it kafka-spark-pipeline-db-1 psql -U postgres -d streaming_db -c "SELECT * FROM active_users;"
```

### 6.2 Verify Data Lake (Parquet Files)

Spark continuously writes raw events to the data lake.

#### Check the generated partitioned files:
```bash
docker exec -it kafka-spark-pipeline-spark-app-1 ls -R /app/data/lake
```
Expected files:

- part-00000.parquet
- part-00001.parquet
- 6.3 Verify Enriched Kafka Topic

#### Downstream Enrichment (Kafka)
Verify that the enriched events (with processing_time) are being published:
```bash
docker exec -it kafka-spark-pipeline-kafka-1 kafka-console-consumer --bootstrap-server localhost:9092 --topic enriched_activity --from-beginning --max-messages 1
```
Example output:
```bash
{"event_time":"2026-03-13T20:35:00.000Z","user_id":"user_video_01","page_url":"/home","event_type":"page_view","processing_time":"2026-03-13T15:08:27.598Z"}
Processed a total of 1 messages
```

---

## 7. Architecture Highlights
### Watermarking

- Spark uses a 2-minute watermark to handle late arriving events.

- withWatermark("event_time", "2 minutes")

- Events arriving later than 2 minutes are dropped.

### Stream-Stream Join

Session duration is computed by joining:

- session_start

- session_end

A 1-hour join boundary prevents unbounded state growth in Spark.

### Multi-Sink Architecture

Spark writes processed data to three destinations simultaneously:

| Destination | Purpose                    |
| ----------- | -------------------------- |
| PostgreSQL  | Real-time analytics        |
| Parquet     | Historical data lake       |
| Kafka       | Downstream event messaging |

---

## 8. Stopping the Pipeline

Stop all containers with:
```bash
docker-compose down
```

---

## 9. Summary

This project demonstrates a complete end-to-end real-time data pipeline:

- Kafka ingestion

- Spark streaming processing

- Windowed aggregations

- Stateful session tracking

- Watermarking for late data

- PostgreSQL analytics layer

- Parquet data lake storage

- Kafka enriched event publishing