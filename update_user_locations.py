from pymongo import MongoClient, UpdateOne
from datetime import datetime, timedelta, timezone
import requests
import random

def update_user_locations():
    # MongoDB setup
    client = MongoClient("mongodb://mongo:27017/")
    db = client["AlertCircleProject"]
    collection = db["latest_user_location"]

    # Fetch active user locations -> Simulation for the sake of this example
    # response = requests.get("http://localhost:5000/users/active-locations")
    # users = response.json()

    # Simulated data for demonstration
    users = [
        {"user_id": "alice123", "latitude": random.randrange(-90,90), "longitude": random.randrange(-180,180)},
        {"user_id": "bob456", "latitude": random.randrange(-90,90), "longitude": random.randrange(-180,180)},
        {"user_id": "charlie789", "latitude": random.randrange(-90,90), "longitude": random.randrange(-180,180)}
    ]
    
    now = datetime.now(timezone.utc)

    # Prepare bulk operations
    operations = [
        UpdateOne(
            {"user_id": user["user_id"]},
            {
                "$set": {
                    "location": {
                        "type": "Point",
                        "coordinates": [user["longitude"], user["latitude"]]
                    },
                    "insert_time": now
                }
            },
            upsert=True
        ) for user in users
    ]

    if operations:
        collection.bulk_write(operations)

    # Delete outdated records
    cutoff_time = now - timedelta(minutes=5)
    deleted = collection.delete_many({"insert_time": {"$lt": cutoff_time}}).deleted_count

    print(f"Updated {len(users)} users, deleted {deleted} old records(>5min old).")

if __name__ == "__main__":
    update_user_locations()