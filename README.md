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

```powershell
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
```bash
docker ps
```
Expected containers:

- kafka-spark-pipeline-zookeeper-1
- kafka-spark-pipeline-kafka-1
- kafka-spark-pipeline-db-1
- kafka-spark-pipeline-spark-app-1

## Step 3: Run the Spark Application

Submit the Spark Structured Streaming job.
```bash
docker exec -it kafka-spark-pipeline-spark-app-1 spark-submit \
--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0,org.postgresql:postgresql:42.5.0 \
/app/spark_app.py
```
- This starts the Spark streaming pipeline.

- Keep this terminal open to monitor logs.

## Step 4: Produce Test Data

Open a new terminal and run a Kafka producer.
```bash
docker exec -it kafka-spark-pipeline-kafka-1 kafka-console-producer \
--bootstrap-server localhost:9092 \
--topic user_activity
```
Paste the following events one at a time:
```bash
{"event_time": "2026-03-13T14:00:00Z", "user_id": "fresh_user", "page_url": "/home", "event_type": "session_start"}

{"event_time": "2026-03-13T14:05:00Z", "user_id": "fresh_user", "page_url": "/checkout", "event_type": "session_end"}

{"event_time": "2026-03-13T14:15:00Z", "user_id": "pusher", "page_url": "/home", "event_type": "page_view"}
```
- Wait 10 seconds, then press Ctrl + C.

The pusher event forces Spark to advance event time, which allows the session window to close and results to be written to the database.

## 6. Verification Steps

These steps confirm that the pipeline is working correctly.

### 6.1 Verify PostgreSQL Output

#### Check whether the session duration was calculated.
```bash
docker exec -it kafka-spark-pipeline-db-1 psql -U postgres -d streaming_db -c "SELECT * FROM user_sessions;"
```
Example output:
```bash
user_id | start_time | end_time | duration_seconds
fresh_user | ... | ... | 300
```

#### Check page view counts:
```bash
docker exec -it kafka-spark-pipeline-db-1 psql -U postgres -d streaming_db -c "SELECT * FROM page_view_counts;"
```

### 6.2 Verify Data Lake (Parquet Files)

Spark continuously writes raw events to the data lake.

#### Check the generated partitioned files:
```bash
ls ./data/lake/event_date=2026-03-13/
```
Expected files:

- part-00000.parquet
- part-00001.parquet
- 6.3 Verify Enriched Kafka Topic

#### Spark publishes enriched events with an additional processing_time field.
```bash
docker exec -it kafka-spark-pipeline-kafka-1 kafka-console-consumer \
--bootstrap-server localhost:9092 \
--topic enriched_activity \
--from-beginning \
--max-messages 1
```
Example output:
```bash
{
"event_time": "2026-03-13T14:15:00Z",
"user_id": "pusher",
"page_url": "/home",
"event_type": "page_view",
"processing_time": "2026-03-13T14:15:03Z"
}
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