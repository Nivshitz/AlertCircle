from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StringType, DoubleType, TimestampType
from pyspark.sql.functions import col, expr, to_json, struct, broadcast, from_json, collect_list, lit
from sedona.register import SedonaRegistrator
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
EC2_EXTERNAL_IP = os.getenv("EC2_EXTERNAL_IP")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Config
KAFKA_BOOTSTRAP_SERVERS = f"{EC2_EXTERNAL_IP}:9092"
RAW_TOPIC = "raw_alerts"
ENRICHED_TOPIC = "enriched_alerts"
CHECKPOINT_DIR = "./checkpoints/alerts_stream_v4"

# Initialize SparkSession
spark = SparkSession.builder \
    .appName("ProcessAlertsStream") \
    .master("local[*]") \
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2,"
            "org.apache.sedona:sedona-sql-3.4_2.12:1.4.1,"
            "org.apache.sedona:sedona-viz-3.4_2.12:1.4.1,"
            "org.datasyslab:geotools-wrapper:geotools-24.0,"
            "org.mongodb.spark:mongo-spark-connector_2.12:3.0.1,"
            "org.apache.hadoop:hadoop-aws:3.3.1,"
            "com.amazonaws:aws-java-sdk-bundle:1.11.1026") \
    .config("spark.sql.extensions", "org.apache.sedona.sql.SedonaSqlExtensions") \
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
    .config("spark.kryo.registrator", "org.apache.sedona.core.serde.SedonaKryoRegistrator") \
    .config("spark.hadoop.fs.s3a.access.key", AWS_ACCESS_KEY) \
    .config("spark.hadoop.fs.s3a.secret.key", AWS_SECRET_KEY) \
    .config("spark.hadoop.fs.s3a.endpoint", "s3.amazonaws.com") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.fast.upload", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.aws.credentials.provider",
            "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
    .getOrCreate()

SedonaRegistrator.registerAll(spark)

# Schema for incoming alerts
alert_schema = StructType() \
    .add("event_id", StringType()) \
    .add("event_time", TimestampType()) \
    .add("event_type", StringType()) \
    .add("user_id", StringType()) \
    .add("description", StringType()) \
    .add("latitude", DoubleType()) \
    .add("longitude", DoubleType())

# Consume alerts from raw_alerts Kafka topic
alerts_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("subscribe", RAW_TOPIC) \
    .option("startingOffsets", "latest") \
    .load() \
    .selectExpr("CAST(value AS STRING) as json_value") \
    .withColumn("data", from_json(col("json_value"), alert_schema)) \
    .select("data.*") \
    .withColumn("alert_point", expr("ST_Point(longitude, latitude)"))

# MicroBatch processing
def process_batch(batch_df, batch_id):
    print(f"\n=== Processing batch {batch_id} ===")
    print("\n=== Alerts in this batch: ===")
    batch_df.show(truncate=False)

    if batch_df.count() == 0:
        print(f"=== Batch {batch_id} is empty — skipping write. ===")
        return
    
    try:
        users_df = spark.read \
            .format("mongo") \
            .option("uri", f"mongodb://{EC2_EXTERNAL_IP}:27017") \
            .option("database", "AlertCircleProject") \
            .option("collection", "latest_user_location") \
            .load() \
            .withColumnRenamed("user_id", "nearby_user_id") \
            .withColumn("user_point", expr("ST_Point(location.coordinates[0], location.coordinates[1])"))
        
        print("=== Active users: ===")
        users_df.show(truncate=False)
    except Exception as e:
        print("MongoDB read failed:", e)
        return

    if users_df.count() == 0:
        print("=== No active users. ===")
        return

    # Calculate distance between alert points and user locations
    joined_df = batch_df.crossJoin(broadcast(users_df)) \
        .withColumn("distance_meters", expr("ST_DistanceSphere(alert_point, user_point)"))
    
    # Filter for users within 500 meters from the alert point and exclude self-matches
    joined_df = joined_df.filter(col("distance_meters") <= 500) \
        .filter(col("user_id") != col("nearby_user_id"))

    # Group enriched alerts: enrich each alert with nearby users
    grouped_df = joined_df.groupBy("event_id", "event_time", "event_type", "user_id",
                                   "description", "latitude", "longitude") \
        .agg(collect_list("nearby_user_id").alias("nearby_users"))

    # Check if there are any enriched alerts to write
    if grouped_df.count() == 0:
        print(f"=== Batch {batch_id} produced no enriched alerts — skipping write. ===")
        return

    # Archive to S3 with a partition by date
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    grouped_df = grouped_df.withColumn("date", lit(today))

    s3_path = "s3a://alert-circle/enriched-alerts/"
    grouped_df.write \
        .mode("append") \
        .partitionBy("date") \
        .parquet(s3_path)

    print(f"=== Batch {batch_id} archived to {s3_path} ===")

    # Send to Kafka enriched_alerts topic
    output_df = grouped_df.select(to_json(struct("*")).alias("value"))
    output_df.write \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("topic", ENRICHED_TOPIC) \
        .save()
    
    print(f"=== Batch {batch_id} sent to Kafka topic '{ENRICHED_TOPIC}' ===")

# Start the streaming query with foreachBatch
query = alerts_df.writeStream \
    .foreachBatch(process_batch) \
    .outputMode("append") \
    .option("checkpointLocation", CHECKPOINT_DIR) \
    .start()

query.awaitTermination()
