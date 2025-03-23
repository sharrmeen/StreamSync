from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import boto3
import redis
from collections import Counter
import logging
from datetime import datetime, timezone
import math
import time

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8080"}})

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Redis client
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Initialize Limiter
limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

# Request counter for metrics
request_counter = Counter()

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
s3_client = boto3.client('s3', region_name='ap-south-1')
CF_BASE_URL = "https://d3oe22crr7rljh.cloudfront.net/videos"
BUCKET_NAME = "streamsync-videos-meen"

INCLUDE_ALL_AFTER_T = True
LOOP_BACK_TO_START = True
TIME_IN_MINUTES = False  # From first file

# Stream start time (midnight UTC today)
STREAM_START = datetime(2025, 3, 23, 0, 0, 0, tzinfo=timezone.utc)
GLOBAL_SYNC_REFERENCE = STREAM_START.timestamp()

# Cache for sequence data and segment counts
sequence_cache = {}
segment_count_cache = {}
video_metadata_cache = {}

def get_sequence(user_id):
    if user_id in sequence_cache:
        return sequence_cache[user_id]
    
    table = dynamodb.Table('UserSequences')
    try:
        response = table.get_item(Key={'user_id': user_id})
        sequence = response.get('Item', {}).get('sequence', [])
        print(f"Sequence for user {user_id} (from DynamoDB): {sequence}")
        sequence_cache[user_id] = sequence
        return sequence
    except Exception as e:
        print(f"Error fetching sequence for user {user_id}: {e}")
        return []

def batch_get_video_metadata(video_ids):
    if not video_ids:
        return {}
    
    # Check cache first
    cached = {vid: video_metadata_cache[vid] for vid in video_ids if vid in video_metadata_cache}
    missing = [vid for vid in video_ids if vid not in video_metadata_cache]
    if not missing:
        return cached
    
    table = dynamodb.Table('VideoMetadata')
    keys = [{'video_id': vid} for vid in missing]
    try:
        response = dynamodb.batch_get_item(
            RequestItems={'VideoMetadata': {'Keys': keys, 'ConsistentRead': True}}
        )
        items = response.get('Responses', {}).get('VideoMetadata', [])
        metadata = {}
        for item in items:
            video_id = item['video_id']
            total_segments = int(item.get('total_segments', 0))
            last_segment_duration = float(item.get('last_segment_duration', 2.0))
            metadata[video_id] = (total_segments, last_segment_duration)
            video_metadata_cache[video_id] = (total_segments, last_segment_duration)
            print(f"Metadata for {video_id}: total_segments={total_segments}, last_segment_duration={last_segment_duration}s")
        
        for video_id in missing:
            if video_id not in metadata:
                print(f"No metadata for {video_id}, defaulting to 0 segments and 2.0s")
                metadata[video_id] = (0, 2.0)
                video_metadata_cache[video_id] = (0, 2.0)
        
        return {**cached, **metadata}
    except Exception as e:
        print(f"Error fetching batch metadata for {video_ids}: {e}")
        return {**cached, **{vid: (0, 2.0) for vid in missing}}

def get_segment_count(video_id, metadata=None):
    if video_id in segment_count_cache:
        return segment_count_cache[video_id]
    
    if metadata and video_id in metadata:
        count = metadata[video_id][0]
        segment_count_cache[video_id] = count
        return count
    
    prefix = f"videos/{video_id}/"
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
        if 'Contents' not in response:
            return 0
        count = sum(1 for obj in response['Contents'] if obj['Key'].endswith('.ts'))
        print(f"Segment count for {video_id} (from S3): {count}")
        segment_count_cache[video_id] = count
        return count
    except Exception as e:
        print(f"Error listing segments for {video_id}: {e}")
        return 0

def calculate_last_segment_duration(video_id, video_duration, total_segments, metadata=None):
    if total_segments <= 0:
        print(f"Invalid segment count for video {video_id}: {total_segments}")
        return 0
    if metadata and video_id in metadata:
        return metadata[video_id][1]
    
    expected_segments = math.ceil(video_duration / 2)
    total_segments = min(total_segments, expected_segments)
    full_segments_duration = (total_segments - 1) * 2
    last_segment_duration = video_duration - full_segments_duration
    if last_segment_duration <= 0 or last_segment_duration > 2:
        last_segment_duration = min(max(last_segment_duration, 0.1), 2.0)
    return round(last_segment_duration, 3)

def calculate_total_duration(sequence):
    if not sequence:
        return 0
    last_entry = sequence[-1]
    total_duration = float(last_entry['start_time']) + float(last_entry['duration'])
    print(f"Total duration of sequence: {total_duration:.3f}s")
    return total_duration

def generate_playlist(user_id, T=None):
    request_start = time.time()
    sequence = get_sequence(user_id)
    if not sequence:
        print(f"No sequence found for user {user_id}")
        return "#EXTM3U\n#EXT-X-ENDLIST"
    
    total_duration = calculate_total_duration(sequence)
    if total_duration == 0:
        return "#EXTM3U\n#EXT-X-ENDLIST"
    
    # Use T if provided, otherwise sync to global reference
    if T is not None:
        T_seconds = T * 60 if TIME_IN_MINUTES else T
        print(f"Requested time T: {T_seconds}s")
    else:
        current_time = time.time()
        precise_elapsed = current_time - GLOBAL_SYNC_REFERENCE
        T_seconds = precise_elapsed
        print(f"Syncing to global reference: {T_seconds:.3f}s since {STREAM_START}")
    
    looped_T = T_seconds % total_duration if LOOP_BACK_TO_START else T_seconds
    print(f"Looped T: {looped_T:.6f}s (using global sync reference)")
    
    video_ids = [entry['video_id'] for entry in sequence]
    metadata = batch_get_video_metadata(video_ids)
    
    current_video_index = 0
    for i, entry in enumerate(sequence):
        start_time = float(entry['start_time'])
        duration = float(entry['duration'])
        start_time_seconds = start_time * 60 if TIME_IN_MINUTES else start_time
        end_time_seconds = start_time_seconds + (duration * 60 if TIME_IN_MINUTES else duration)
        if start_time_seconds <= looped_T < end_time_seconds:
            current_video_index = i
            print(f"Current video at T={looped_T:.3f}s: {entry['video_id']} "
                  f"(start: {start_time_seconds}s, end: {end_time_seconds}s)")
            break
    else:
        print(f"No video found at T={looped_T:.3f}s, defaulting to first")
        current_video_index = 0
    
    current_date_time = datetime.now(timezone.utc)
    playlist = "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:2\n"
    playlist += f"#EXT-X-PROGRAM-DATE-TIME:{current_date_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}\n"
    
    offset_seconds = looped_T - float(sequence[current_video_index]['start_time'])
    current_segment = int(offset_seconds / 2)
    segment_internal_offset = offset_seconds % 2
    playlist += f"#EXT-X-START:TIME-OFFSET={segment_internal_offset:.6f},PRECISE=YES\n"
    
    videos_to_process = []
    if INCLUDE_ALL_AFTER_T:
        videos_to_process = list(range(current_video_index, len(sequence)))
        if LOOP_BACK_TO_START:
            videos_to_process.extend(range(0, current_video_index))
    else:
        videos_to_process = [current_video_index]
    
    first_video = True
    for idx in videos_to_process:
        entry = sequence[idx]
        video_id = entry['video_id']
        video_duration = float(entry['duration'])
        total_segments = get_segment_count(video_id, metadata)
        if total_segments == 0:
            print(f"No segments for {video_id}, skipping")
            continue
        
        start_segment = current_segment if idx == current_video_index and first_video else 0
        first_video = False
        last_segment_duration = calculate_last_segment_duration(video_id, video_duration, total_segments, metadata)
        
        for i in range(start_segment, total_segments):
            segment_duration = last_segment_duration if i == total_segments - 1 else 2.0
            playlist += f"#EXTINF:{segment_duration:.3f},\n{CF_BASE_URL}/{video_id}/segment_{i:03d}.ts\n"
    
    playlist += "#EXT-X-ENDLIST"
    
    processing_time = (time.time() - request_start) * 1000
    playlist_lines = playlist.split('\n')
    first_segment = next((l for l in playlist_lines if l.endswith('.ts')), "No segments")
    
    stream_elapsed = (datetime.now(timezone.utc) - STREAM_START).total_seconds()
    print(f"User {user_id} joined at {stream_elapsed:.3f}s since stream start")
    print(f"Generated playlist summary for {user_id}:")
    print(f"  Position: {looped_T:.3f}s in loop, offset: {offset_seconds:.3f}s in current video")
    print(f"  First segment: {first_segment}")
    print(f"  Timing: EXT-X-START:TIME-OFFSET={segment_internal_offset:.6f}")
    print(f"  Request processing time: {processing_time:.2f}ms")
    
    return playlist

@app.before_request
def log_request_info():
    logging.info(f"Request: {request.method} {request.url} from {request.remote_addr}")

@app.errorhandler(Exception)
def handle_exception(e):
    print(f"Unexpected error: {e}")
    return jsonify({"error": "An unexpected error occurred", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "StreamSync is running!"}), 200

@app.route('/metrics', methods=['GET'])
def metrics():
    return jsonify({
        "total_requests": request_counter['playlist_requests'],
        "redis_keys": redis_client.dbsize()
    }), 200

@app.route('/clear-cache', methods=['GET'])
def clear_cache_endpoint():
    global sequence_cache, segment_count_cache, video_metadata_cache
    sequence_cache.clear()
    segment_count_cache.clear()
    video_metadata_cache.clear()
    return {"status": "success", "message": "Caches cleared"}

@app.route('/playlist', methods=['GET'])
@limiter.limit("10 per minute")
def playlist_endpoint():
    request_counter['playlist_requests'] += 1
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "Missing user_id", "message": "Please provide a user_id parameter"}), 400
    
    T = request.args.get('time')
    if T is not None:
        try:
            T = float(T)
        except ValueError:
            return jsonify({"error": "Invalid time parameter", "message": "Time must be a valid number"}), 400
    
    segment_duration = 2.0
    cache_T = segment_duration * round((T or time.time() - GLOBAL_SYNC_REFERENCE) / segment_duration)
    cache_key = f"playlist:{user_id}:T={cache_T}"
    
    cached_playlist = redis_client.get(cache_key)
    if cached_playlist:
        print(f"Cache hit for {cache_key}")
        response = Response(cached_playlist.decode('utf-8'), mimetype='application/vnd.apple.mpegurl')
    else:
        print(f"Cache miss for {cache_key}, generating playlist")
        playlist = generate_playlist(user_id, T)
        redis_client.setex(cache_key, 300, playlist)
        response = Response(playlist, mimetype='application/vnd.apple.mpegurl')
    
    response.headers['X-Server-Time'] = str(time.time())
    response.headers['X-Global-Reference'] = str(GLOBAL_SYNC_REFERENCE)
    response.headers['Access-Control-Expose-Headers'] = 'X-Server-Time, X-Global-Reference'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)