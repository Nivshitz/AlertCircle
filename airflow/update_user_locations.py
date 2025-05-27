from pymongo import MongoClient, UpdateOne
from pymongo.errors import PyMongoError
from datetime import datetime, timedelta, timezone
import random

# Known users – match with producer
known_users = [
    "niv123", "charlie789", "tamar456", "shira321", "amir888",
    "lior111", "gal654", "eden990", "yossi555"
]

# Location bounds: Tel Aviv – Ramat Gan – Givatayim
lat_range = (32.04, 32.10)
lon_range = (34.78, 34.83)

def update_user_locations():
    try:
        print("Starting user location update process...")

        client = MongoClient("mongodb://mongo:27017/")
        db = client["AlertCircleProject"]
        collection = db["latest_user_location"]

        now = datetime.now(timezone.utc).isoformat()

        users = []
        for user in known_users:
            if user == "niv123": # Demo user - fixed location (BITSARON)
                users.append({
                    "user_id": user,
                    "latitude": 32.069,
                    "longitude": 34.794
                })
            else:
                users.append({
                    "user_id": user,
                    "latitude": round(random.uniform(*lat_range), 6),
                    "longitude": round(random.uniform(*lon_range), 6)
                })

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
            result = collection.bulk_write(operations)
            print(f"Updated {len(users)} users - Upserts: {result.upserted_count}, Modified: {result.modified_count}")

    except PyMongoError as e:
        print(f"MongoDB error: {e}")
    except Exception as e:
        print(f"General error: {e}")

if __name__ == "__main__":
    update_user_locations()
