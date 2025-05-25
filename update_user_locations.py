from pymongo import MongoClient, UpdateOne
from pymongo.errors import PyMongoError
from datetime import datetime, timedelta, timezone
import requests
import random
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
EC2_EXTERNAL_IP = os.getenv("EC2_EXTERNAL_IP")

def update_user_locations():
    try:
        print("🔄 Starting user location update process...")

        # MongoDB setup - EC2 private IP
        print(f"🔗 Connecting to MongoDB at {EC2_EXTERNAL_IP}...")
        client = MongoClient(f"mongodb://{EC2_EXTERNAL_IP}:27017/")  # For local: "mongodb://mongo:27017/"
        db = client["AlertCircleProject"]
        collection = db["latest_user_location"]

        # Simulated data for demonstration
        users = [
            {"user_id": "alice123", "latitude": round(random.uniform(-90, 90.0), 6), "longitude": round(random.uniform(-180.0, 180.0), 6)},
            {"user_id": "bob456", "latitude": round(random.uniform(-90.0, 90.0), 6), "longitude": round(random.uniform(-180.0, 180.0), 6)},
            {"user_id": "charlie789", "latitude": round(random.uniform(-90.0, 90.0), 6), "longitude": round(random.uniform(-180.0, 180.0), 6)}
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

if __name__ == "__main__":
    update_user_locations()