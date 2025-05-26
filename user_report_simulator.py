import random
import json
import uuid
import time
from datetime import datetime, timezone
from kafka import KafkaProducer
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
EC2_EXTERNAL_IP = os.getenv("EC2_EXTERNAL_IP")

# Config
RAW_TOPIC = "raw_alerts"
KAFKA_BOOTSTRAP_SERVERS = f"{EC2_EXTERNAL_IP}:9092"

# Kafka producer setup
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: v.encode('utf-8')
)

# Known users
known_users = [
    "niv123", "charlie789", "tamar456", "shira321", "amir888",
    "lior111", "gal654", "eden990", "yossi555", "noa007"
]

# Descriptions
descriptions = [
    "Inspector just fined a woman with a dog",
    "Dog inspector writing tickets again...",
    "Bylaw officer arguing with a guy at the park",
    "Saw an inspector near the dog area",
    "Someone's getting a ticket for no leash"
]

# Location bounds: Tel Aviv – Ramat Gan – Givatayim
lat_range = (32.04, 32.10)
lon_range = (34.78, 34.83)

# Event generator
def generate_event():
    return {
        "event_id": str(uuid.uuid4()),
        "event_time": datetime.now(timezone.utc).isoformat(),
        "event_type": "bylaw_dog_inspector",
        "user_id": random.choice(known_users),
        "description": random.choice(descriptions),
        "latitude": round(random.uniform(*lat_range), 6),
        "longitude": round(random.uniform(*lon_range), 6)
    }

# Send demo alert
demo_alert = {
    "event_id": "demo001",
    "event_time": datetime.now(timezone.utc).isoformat(),
    "event_type": "bylaw_dog_inspector",
    "user_id": "lior111",
    "description": "Inspector giving a ticket by the playground",
    "latitude": 32.069,
    "longitude": 34.794
}
producer.send(RAW_TOPIC, value=json.dumps(demo_alert).encode("utf-8"))
print("Demo alert sent.")

# Producer loop
try:
    while True:
        event = json.dumps(generate_event())
        print(f"Sending: {event}")
        producer.send(RAW_TOPIC, value=event)
        time.sleep(20)

except Exception as e:
    print(f"Error occurred: {e}")

finally:
    producer.flush()
    producer.close()
