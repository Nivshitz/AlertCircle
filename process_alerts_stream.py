from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T

spark = SparkSession.builder \
    .master("local[*]") \
    .appName('ProcessAlertsStream') \
    .config('spark.jars.packages', 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2') \
    .getOrCreate()

alert_schema = T.StructType([
    T.StructField('event_id', T.StringType()),
    T.StructField('event_time', T.DoubleType()),
    T.StructField('user_id', T.StringType()),
    T.StructField('event_type', T.StringType()),
    T.StructField('description', T.StringType()),
    T.StructField('location', T.StructType([
        T.StructField('latitude', T.DoubleType()),
        T.StructField('longitude', T.DoubleType())
    ])),
    T.StructField('device_id', T.DoubleType())
])

raw_alerts_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "course-kafka:9092") \
    .option("subscribe", "raw_alerts") \
    .option("startingOffsets", "earliest") \
    .load() \
    .select(F.col('value').cast(T.StringType()))

parsed_alerts_df = raw_alerts_df \
    .withColumn('parsed_alerts_df', F.from_json(F.col('value'), alert_schema)) \
    .select(F.col('parsed_alerts_df.*'))

final_alerts_df = parsed_alerts_df.select(
    F.col("event_id"),
    F.col("event_time"),
    F.col("user_id"),
    F.col("event_type"),
    F.col("description"),
    F.col("location.latitude").alias("latitude"),
    F.col("location.longitude").alias("longitude"),
    F.col("device_id")
)

query = final_alerts_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

query.awaitTermination()


# # Output to console
# query = final_alerts_df.writeStream \
#     .outputMode("append") \
#     .format("console") \
#     .start()

# query.awaitTermination()

