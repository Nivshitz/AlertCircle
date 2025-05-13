from pymongo import MongoClient, UpdateOne
from pymongo.errors import PyMongoError
from datetime import datetime, timedelta, timezone
import requests
import random

def update_user_locations():
    try:
        print("🔄 Starting user location update process...")

        # MongoDB setup - EC2 private IP
        print("🔗 Connecting to MongoDB at 172.31.44.221...")
        client = MongoClient("mongodb://172.31.44.221:27017/")  # For local: "mongodb://mongo:27017/"
        db = client["AlertCircleProject"]
        collection = db["latest_user_location"]

        # Simulated data for demonstration
        users = [
            {"user_id": "alice123", "latitude": random.randrange(-90,90), "longitude": random.randrange(-180,180)},
            {"user_id": "bob456", "latitude": random.randrange(-90,90), "longitude": random.randrange(-180,180)},
            {"user_id": "charlie789", "latitude": random.randrange(-90,90), "longitude": random.randrange(-180,180)}
        ]

        print(f"📦 Preparing updates for {len(users)} users...")

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
            result = collection.bulk_write(operations)
            print(f"✅ Bulk write complete. Upserts: {result.upserted_count}, Modified: {result.modified_count}")

        # Delete outdated records
        cutoff_time = now - timedelta(minutes=5)
        deleted = collection.delete_many({"insert_time": {"$lt": cutoff_time}}).deleted_count

        print(f"🧹 Deleted {deleted} outdated records (>5min old).")

    except PyMongoError as e:
        print(f"❌ MongoDB error: {e}")
    except Exception as e:
        print(f"❌ General error: {e}")
