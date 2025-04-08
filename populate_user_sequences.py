import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def populate_test_user_sequence():
    user_id = "test_user"
    sequence = [
        {"video_id": "video1", "start_time": "0", "duration": "27.7"},
        {"video_id": "video2", "start_time": "27.7", "duration": "11.91"},
        {"video_id": "video3", "start_time": "39.61", "duration": "39.92"},
        {"video_id": "video4", "start_time": "79.53", "duration": "13.46"},
        {"video_id": "video5", "start_time": "92.99", "duration": "44.34"},
        {"video_id": "video6", "start_time": "137.33", "duration": "63.9"}
    ]
    redis_key = f"user_sequence:{user_id}"
    redis_client.set(redis_key, json.dumps(sequence))
    print(f"Stored sequence for {user_id}: {sequence}")

if __name__ == "__main__":
    print("Populating test user sequence in Redis...")
    populate_test_user_sequence()
    print("Done! Checking stored sequence:")
    data = redis_client.get("user_sequence:test_user")
    print(f"user_sequence:test_user: {data}")