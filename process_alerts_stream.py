from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StringType, DoubleType, TimestampType
from pyspark.sql.functions import col, expr, to_json, struct, broadcast
from sedona.register import SedonaRegistrator
from sedona.sql.functions import ST_Point, ST_DistanceSphere

# Initialize Spark
spark = SparkSession.builder \
    .appName("ProcessAlertsStream") \
    .master("local[*]") \
    .config("spark.jars.packages", 
    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2,"
    "org.apache.sedona:sedona-python-adapter-3.0_2.12:1.2.0,"
    "org.datasyslab:geotools-wrapper:geotools-24.0,"
    "org.mongodb.spark:mongo-spark-connector_2.12:10.1.1") \
    .getOrCreate()

SedonaRegistrator.registerAll(spark)

# Kafka configs
kafka_bootstrap_servers = "localhost:9092"
raw_topic = "raw_alerts"
enriched_topic = "enriched_alerts"

# Alert schema
alert_schema = StructType() \
    .add("event_id", StringType()) \
    .add("event_time", TimestampType()) \
    .add("event_type", StringType()) \
    .add("user_id", StringType()) \
    .add("description", StringType()) \
    .add("latitude", DoubleType()) \
    .add("longitude", DoubleType())

# Read Kafka's raw_alerts topic
alerts_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
    .option("subscribe", raw_topic) \
    .option("startingOffsets", "latest") \
    .load() \
    .selectExpr("CAST(value AS STRING)") \
    .selectExpr(f"from_json(value, '{alert_schema.json()}') as data") \
    .select("data.*")

 # Prepare alerts with geometry point: user_point(longitude, latitude)
alerts_df = alerts_df \
    .withColumn("alert_point", expr("ST_Point(longitude, latitude)"))

# Batch processing function: join alerts with user locations with Sedona spatial join
def process_batch(batch_df, batch_id):
    # Load latest user location from MongoDB
    users_df = spark.read.format("mongo") \
        .option("uri", "mongodb://mongo:27017/AlertCircleProject.latest_user_location") \
        .load() \
        .withColumnRenamed("user_id", "nearby_user_id") \
        .withColumn("user_point", ST_Point(col("location.coordinates")[0], col("location.coordinates")[1]))

    if users_df.rdd.isEmpty():
        print("No active users.")
        return

    # Distance filter: only users within 500 meters are considered. Using broadcast join for performance
    enriched_df = batch_df.crossJoin(broadcast(users_df)) \
        .withColumn("distance_meters", ST_DistanceSphere(batch_df.alert_point, users_df.user_point)) \
        .filter("distance_meters <= 500")

    # Prepare output for Kafka
    output_df = enriched_df.select(to_json(struct("*")).alias("value"))

    # Write to enriched_alerts topic
    output_df.write \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("topic", enriched_topic) \
        .save()

# Launch streaming with foreachBatch: process each micro-batch of alerts and write to enriched_alerts topic
query = alerts_df.writeStream \
    .foreachBatch(process_batch) \
    .outputMode("append") \
    .option("checkpointLocation", "/tmp/spark_checkpoint/enriched_alerts") \
    .start()

query.awaitTermination()
