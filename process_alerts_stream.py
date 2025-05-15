from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StringType, DoubleType, TimestampType
from pyspark.sql.functions import col, expr, to_json, struct, broadcast, from_json
from sedona.register import SedonaRegistrator

# Initialize Spark
spark = SparkSession.builder \
    .appName("ProcessAlertsStream") \
    .master("local[*]") \
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2,"
            "org.apache.sedona:sedona-sql-3.4_2.12:1.4.1,"
            "org.apache.sedona:sedona-viz-3.4_2.12:1.4.1,"
            "org.datasyslab:geotools-wrapper:geotools-24.0,"
            "org.mongodb.spark:mongo-spark-connector_2.12:10.1.1") \
    .config("spark.sql.extensions", "org.apache.sedona.sql.SedonaSqlExtensions") \
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
    .config("spark.kryo.registrator", "org.apache.sedona.core.serde.SedonaKryoRegistrator") \
    .config("spark.mongodb.read.connection.uri", "mongodb://mongo:27017") \
    .config("spark.mongodb.read.database", "AlertCircleProject") \
    .config("spark.mongodb.read.collection", "latest_user_location") \
    .getOrCreate()

SedonaRegistrator.registerAll(spark)

# Kafka configs
kafka_bootstrap_servers = "course-kafka:9092"
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

# Read alerts from Kafka and parse JSON
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

# Batch processing function
def process_batch(batch_df, batch_id):
    print(f"\n🚀 Processing batch {batch_id}")

    try:
        users_df = spark.read.format("mongodb").load() \
            .withColumnRenamed("user_id", "nearby_user_id") \
            .withColumn("user_point", expr("ST_Point(location.coordinates[0], location.coordinates[1])"))
    except Exception as e:
        print("❌ MongoDB read failed:", e)
        return

    if users_df.rdd.isEmpty():
        print("⚠️ No active users.")
        return

    enriched_df = batch_df.crossJoin(broadcast(users_df)) \
        .withColumn("distance_meters", expr("ST_DistanceSphere(alert_point, user_point)")) \
        .filter("distance_meters <= 500")

    output_df = enriched_df.select(to_json(struct("*")).alias("value"))

    output_df.write \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("topic", enriched_topic) \
        .save()

# Start the stream
query = alerts_df.writeStream \
    .foreachBatch(process_batch) \
    .outputMode("append") \
    .option("checkpointLocation", "/tmp/spark_checkpoint/enriched_alerts") \
    .start()

query.awaitTermination()
