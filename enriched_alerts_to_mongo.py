from kafka import KafkaConsumer
from pymongo import MongoClient
import json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
EC2_EXTERNAL_IP = os.getenv("EC2_EXTERNAL_IP")

# Config
KAFKA_TOPIC = "enriched_alerts"
KAFKA_BOOTSTRAP_SERVERS = f"{EC2_EXTERNAL_IP}:9092"
MONGO_URI = f"mongodb://{EC2_EXTERNAL_IP}:27017"
DB_NAME = "AlertCircleProject"
COLLECTION_NAME = "alerts_live"

# Parameters for deduplication: unnotifying users within a radius and time window
RADIUS_METERS = 25
TIME_WINDOW_MINUTES = 10

# Kafka consumer setup
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset="latest",
    enable_auto_commit=True
)

# MongoDB setup
mongo_client = MongoClient(MONGO_URI)
alertsLive_collection = mongo_client[DB_NAME][COLLECTION_NAME]

print(f"=== Listening to topic `{KAFKA_TOPIC}` and writing to MongoDB... ===")

# Consume enriched alerts and write to Mongo
for msg in consumer:
    enriched_alert = msg.value

    try:
        event_id = enriched_alert["event_id"]
        alert_lat = enriched_alert["latitude"]
        alert_lon = enriched_alert["longitude"]
        alert_time = datetime.fromisoformat(enriched_alert["event_time"])

        filtered_users = []
        for user in enriched_alert.get("nearby_users", []):
            existing = alertsLive_collection.find_one({
                "notified_users": user,
                "event_time": {"$gte": alert_time - timedelta(minutes=TIME_WINDOW_MINUTES)},
                "alert_point": {
                    "$nearSphere": {
                        "$geometry": {
                            "type": "Point",
                            "coordinates": [alert_lon, alert_lat]
                        },
                        "$maxDistance": RADIUS_METERS
                    }
                }
            })
            if existing:
                print(f"=== User {user} already notified nearby. Skipping. ===")
            else:
                filtered_users.append(user)

        if not filtered_users:
            print(f"=== Alert {event_id} skipped — all users already notified. ===")
            continue

        # Transform structure for MongoDB and Streamlit
        mongo_doc = {
            "event_id": event_id,
            "event_time": alert_time,
            "description": enriched_alert.get("description", ""),
            "latitude": alert_lat,
            "longitude": alert_lon,
            "alert_point": {
                "type": "Point",
                "coordinates": [alert_lon, alert_lat]
            },
            "notified_users": filtered_users,
            "ingestion_time": datetime.now(timezone.utc)
        }

        alertsLive_collection.insert_one(mongo_doc)
        print(f"=== Inserted alert: {event_id} for users {filtered_users} ===")

    except Exception as e:
        print(f"Failed to process message: {e}")
