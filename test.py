from pymongo import MongoClient, UpdateOne
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
EC2_EXTERNAL_IP = os.getenv("EC2_EXTERNAL_IP")

print(EC2_EXTERNAL_IP)

client = MongoClient(f"mongodb://{EC2_EXTERNAL_IP}:27017/")
db = client["AlertCircleProject"]
collection = db["latest_user_location"]

for doc in collection.find():
    print(doc)
