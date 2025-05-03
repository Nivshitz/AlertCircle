import random
import time
import json
import uuid
from kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers = 'course-kafka:9092',
                         value_serializer = lambda v: v.encode('utf-8'))

report_options = ['inspector_dog', 'inspector_parking']

def generate_event(report_options):
    return {
        "event_id": str(uuid.uuid4()),
        "event_time": time.time(),
        "event_type": random.choice(report_options),
        "user_id": f"user_{random.randint(1000, 9999)}",
        "description": "Saw an insepctor giving reports to dog owners", # Event description provided by the user (optionally)
        "location": {
            "latitude": round(random.uniform(-90.0, 90.0), 6),
            "longitude": round(random.uniform(-180.0, 180.0), 6),
            #"accuracy": round(random.uniform(3.0, 50.0), 1)  # meters
        },
        "device_id": f"device_{random.randint(1000, 9999)}"
        #"app_version": f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
        #"photo_url": None  # Placeholder, can be extended later
    }

try:
    while True:
        event = json.dumps(generate_event(report_options))
        print(event)
        producer.send(topic = 'raw_alerts', value = event)

        time.sleep(10)

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    producer.flush()
    producer.close()
