import json
import time
import random
from kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers = 'course-kafka:9092',
                         value_serializer = lambda v: v.encode('utf-8'))

# Define initial users
NUM_USERS = 100
users = {}

# Generate random initial positions (centered roughly in Tel Aviv)
BASE_LAT, BASE_LON = 32.0853, 34.7818

for i in range(NUM_USERS):
    user_id = f"user_{i}"
    users[user_id] = {
        'latitude': BASE_LAT + random.uniform(-0.05, 0.05),
        'longitude': BASE_LON + random.uniform(-0.05, 0.05)
    }

try:
    while True:
        for user_id, loc in users.items():
            # Simulate small random movement
            loc['latitude'] += random.uniform(-0.0005, 0.0005)
            loc['longitude'] += random.uniform(-0.0005, 0.0005)

            user_location = {
                'user_id': user_id,
                'latitude': loc['latitude'],
                'longitude': loc['longitude'],
                'timestamp': time.time()
            }

            message = json.dumps(user_location)
            print(message)

            producer.send(topic='user_location', value=message)

        time.sleep(2)

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    producer.flush()
    producer.close()
