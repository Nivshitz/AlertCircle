from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StringType, DoubleType, TimestampType
from pyspark.sql.functions import col, expr, to_json, struct, broadcast, from_json, collect_list, lit
from sedona.register import SedonaRegistrator
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

# === Load environment variables from .env ===
load_dotenv()
EC2_EXTERNAL_IP = os.getenv("EC2_EXTERNAL_IP")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# === Initialize SparkSession ===
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

# === Kafka topics and checkpoint ===
kafka_bootstrap_servers = f"{EC2_EXTERNAL_IP}:9092"
raw_topic = "raw_alerts"
enriched_topic = "enriched_alerts"
checkpoint_dir = "./checkpoints/alerts_stream_v3"

# === Schema for incoming alerts ===
alert_schema = StructType() \
    .add("event_id", StringType()) \
    .add("event_time", TimestampType()) \
    .add("event_type", StringType()) \
    .add("user_id", StringType()) \
    .add("description", StringType()) \
    .add("latitude", DoubleType()) \
    .add("longitude", DoubleType())

# === Read alerts from Kafka ===
alerts_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
    .option("subscribe", raw_topic) \
    .option("startingOffsets", "latest") \
    .load() \
    .selectExpr("CAST(value AS STRING) as json_value") \
    .withColumn("data", from_json(col("json_value"), alert_schema)) \
    .select("data.*") \
    .withColumn("alert_point", expr("ST_Point(longitude, latitude)"))

# === Batch processing function ===
def process_batch(batch_df, batch_id):
    print(f"\n🚀 Processing batch {batch_id}")
    batch_df.show(truncate=False)

    try:
        users_df = spark.read \
            .format("mongo") \
            .option("uri", f"mongodb://{EC2_EXTERNAL_IP}:27017") \
            .option("database", "AlertCircleProject") \
            .option("collection", "latest_user_location") \
            .load() \
            .withColumnRenamed("user_id", "nearby_user_id") \
            .withColumn("user_point", expr("ST_Point(location.coordinates[1], location.coordinates[0])"))
        users_df.show(truncate=False)
    except Exception as e:
        print("❌ MongoDB read failed:", e)
        return

    if users_df.count() == 0:
        print("⚠️ No active users.")
        return

    # === Spatial join and proximity filter ===
    joined_df = batch_df.crossJoin(broadcast(users_df)) \
        .withColumn("distance_meters", expr("ST_DistanceSphere(alert_point, user_point)")) \
        .filter(col("distance_meters") <= 500) \
        .filter(col("user_id") != col("nearby_user_id"))

    # === Group enriched alerts ===
    grouped_df = joined_df.groupBy("event_id", "event_time", "event_type", "user_id",
                                   "description", "latitude", "longitude") \
        .agg(collect_list("nearby_user_id").alias("nearby_users"))

    # === Archive to S3 ===
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    grouped_df = grouped_df.withColumn("date", lit(today))

    s3_path = "s3a://alert-circle/enriched-alerts/"
    grouped_df.write \
        .mode("append") \
        .partitionBy("date") \
        .parquet(s3_path)

    print(f"✅ Batch {batch_id} archived to {s3_path}")

    # === Send to Kafka ===
    output_df = grouped_df.select(to_json(struct("*")).alias("value"))
    output_df.write \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("topic", enriched_topic) \
        .save()
    
    print(f"✅ Batch {batch_id} sent to Kafka topic '{enriched_topic}'")

# === Start the stream ===
query = alerts_df.writeStream \
    .foreachBatch(process_batch) \
    .outputMode("append") \
    .option("checkpointLocation", checkpoint_dir) \
    .start()

query.awaitTermination()
