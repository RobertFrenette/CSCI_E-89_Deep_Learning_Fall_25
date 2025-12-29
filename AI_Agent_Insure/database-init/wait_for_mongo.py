import sys
import time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

host = sys.argv[1] if len(sys.argv) > 1 else "mongodb"
port = int(sys.argv[2]) if len(sys.argv) > 2 else 27017
tries = int(sys.argv[3]) if len(sys.argv) > 3 else 20
sleep = int(sys.argv[4]) if len(sys.argv) > 4 else 3

for i in range(1, tries + 1):
    try:
        client = MongoClient(host=host, port=port, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        print("MongoDB is ready!")
        sys.exit(0)
    except ConnectionFailure:
        print(f"Waiting for MongoDB ({host}:{port})... ({i}/{tries})")
        time.sleep(sleep)

print(f"MongoDB is still not ready after {tries * sleep} seconds.")
sys.exit(1)
