import boto3
import redis
import json
from collections import Counter
import subprocess
import re
import math
import tempfile
import os

# Initialize MinIO client
s3_client = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='minioadmin',  
    aws_secret_access_key='minioadmin',  
    region_name='us-east-1'
)
BUCKET_NAME = "streamsync-videos-meen"

# Initialize Redis client
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def get_video_data():
    """Scan MinIO for .mp4 files and their .ts segments."""
    print(f"Listing objects in bucket: {BUCKET_NAME}, prefix: videos/")
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix="videos/")
        if 'Contents' not in response:
            print("No objects found in MinIO response.")
            return {}, {}
        
        video_files = {}
        segment_counts = Counter()
        print(f"Found {len(response['Contents'])} objects:")
        for obj in response['Contents']:
            key = obj['Key']
            print(f" - {key}")
            parts = key.split('/')
            if len(parts) < 2:
                continue
            
            if key.endswith('.mp4') and len(parts) == 2:
                video_id = parts[1].replace('.mp4', '')  # e.g., "video1" from "videos/video1.mp4"
                video_files[video_id] = key
            elif key.endswith('.ts') and len(parts) == 3:
                video_id = parts[1]  # e.g., "video1" from "videos/video1/segment_000.ts"
                segment_counts[video_id] += 1
        
        print(f"Detected video files: {video_files}")
        print(f"Segment counts: {dict(segment_counts)}")
        return video_files, segment_counts
    except Exception as e:
        print(f"Error listing objects in MinIO: {e}")
        return {}, {}

def get_video_duration(video_id, video_key):
    """Use FFmpeg to get the total duration of an .mp4 file."""
    print(f"Analyzing duration for {video_key}")
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            s3_client.download_file(BUCKET_NAME, video_key, tmp_file.name)
            result = subprocess.run(
                ['ffmpeg', '-i', tmp_file.name],
                stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True
            )
            os.remove(tmp_file.name)
            
            duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d+)', result.stderr)
            if duration_match:
                hours, minutes, seconds = duration_match.groups()
                duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                print(f"Duration parsed: {duration}s")
                return round(duration, 3)
            else:
                print(f"Could not parse duration for {video_key}, defaulting to segment-based estimate")
                return None
    except Exception as e:
        print(f"Error analyzing {video_key}: {e}")
        return None

def calculate_last_segment_duration(total_duration, total_segments):
    """Calculate the last segment duration based on total duration and segment count."""
    if total_segments <= 0:
        return 0
    full_segments_duration = (total_segments - 1) * 2
    last_segment_duration = total_duration - full_segments_duration
    last_segment_duration = max(min(last_segment_duration, 2.0), 0.1)
    return round(last_segment_duration, 3)

def populate_video_metadata():
    """Populate Redis with video metadata using .mp4 durations and .ts counts."""
    video_files, segment_counts = get_video_data()
    if not video_files:
        print("No .mp4 video files found to process.")
        return
    
    for video_id, video_key in video_files.items():
        total_segments = segment_counts.get(video_id, 0)
        if total_segments == 0:
            print(f"No segments found for {video_id}, skipping.")
            continue
        
        total_duration = get_video_duration(video_id, video_key)
        if total_duration is None:
            total_duration = total_segments * 2
            last_segment_duration = 2.0
        else:
            last_segment_duration = calculate_last_segment_duration(total_duration, total_segments)
        
        metadata = (total_segments, last_segment_duration)
        redis_key = f"video_metadata:{video_id}"
        redis_client.set(redis_key, json.dumps(metadata))
        print(f"Stored metadata for {video_id}: total_segments={total_segments}, "
              f"last_segment_duration={last_segment_duration}s (total_duration={total_duration}s)")

if __name__ == "__main__":
    print("Populating video_metadata in Redis using original .mp4 files...")
    populate_video_metadata()
    print("Done! Checking stored metadata:")
    for key in redis_client.keys("video_metadata:*"):
        data = redis_client.get(key)
        print(f"{key}: {data}")