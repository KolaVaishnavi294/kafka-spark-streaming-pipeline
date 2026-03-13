from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import os

spark = SparkSession.builder \
    .appName("RealTimePipeline") \
    .config("spark.sql.shuffle.partitions", "2") \
    .getOrCreate()

schema = StructType([
    StructField("event_time", TimestampType()),
    StructField("user_id", StringType()),
    StructField("page_url", StringType()),
    StructField("event_type", StringType())
])

# 1. Read from Kafka
raw_kafka = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:29092") \
    .option("subscribe", "user_activity") \
    .load()

# 2. Parse and Watermark (Crucial for joins and windows)
events = raw_kafka.select(from_json(col("value").cast("string"), schema).alias("data")) \
    .select("data.*") \
    .withWatermark("event_time", "2 minutes")

# 3. Requirement 10: Data Lake
events.withColumn("event_date", to_date(col("event_time"))) \
    .writeStream \
    .partitionBy("event_date") \
    .format("parquet") \
    .option("path", "/app/data/lake") \
    .option("checkpointLocation", "/app/checkpoints/lake") \
    .start()

# 4. Requirement 11: Enriched Kafka Topic
events.withColumn("processing_time", current_timestamp()) \
    .select(to_json(struct("*")).alias("value")) \
    .writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:29092") \
    .option("topic", "enriched_activity") \
    .option("checkpointLocation", "/app/checkpoints/enriched") \
    .start()

# 5. Requirement 5 & 8: Page Views (Added window_end mapping)
page_views = events.filter(col("event_type") == "page_view") \
    .groupBy(window(col("event_time"), "1 minute"), col("page_url")) \
    .count() \
    .select(
        col("window.start").alias("window_start"),
        col("window.end").alias("window_end"), 
        "page_url", 
        col("count").alias("view_count")
    )

# 6. Requirement 6: Active Users
active_users = events.groupBy(window(col("event_time"), "5 minutes", "1 minute")) \
    .agg(approx_count_distinct("user_id").alias("active_user_count")) \
    .select(
        col("window.start").alias("window_start"), 
        col("window.end").alias("window_end"), 
        "active_user_count"
    )

# 7. Requirement 7: Session Duration (Stream-Stream Join)
starts = events.filter(col("event_type") == "session_start") \
    .select(col("user_id").alias("start_user_id"), col("event_time").alias("start_time"))

ends = events.filter(col("event_type") == "session_end") \
    .select(col("user_id").alias("end_user_id"), col("event_time").alias("end_time"))

user_sessions = starts.join(
    ends,
    expr("""
        start_user_id = end_user_id AND
        end_time >= start_time AND
        end_time <= start_time + interval 1 hour
    """)
).select(
    col("start_user_id").alias("user_id"),
    "start_time",
    "end_time",
    (unix_timestamp("end_time") - unix_timestamp("start_time")).alias("duration_seconds")
)

# --- POSTGRES SINK ---
def write_to_postgres(df, epoch_id, table_name):
    db_url = f"jdbc:postgresql://db:5432/{os.getenv('DB_NAME')}"
    df.write.mode("append") \
        .format("jdbc") \
        .option("url", db_url) \
        .option("dbtable", table_name) \
        .option("user", os.getenv("DB_USER")) \
        .option("password", os.getenv("DB_PASSWORD")) \
        .option("driver", "org.postgresql.Driver") \
        .save()

# Start Sinks
page_views.writeStream.foreachBatch(lambda df, id: write_to_postgres(df, id, "page_view_counts")).start()
active_users.writeStream.foreachBatch(lambda df, id: write_to_postgres(df, id, "active_users")).start()
user_sessions.writeStream.foreachBatch(lambda df, id: write_to_postgres(df, id, "user_sessions")).start()

spark.streams.awaitAnyTermination()