from flask import Flask, request, Response
from flask_cors import CORS
import boto3

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8080"}})
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
s3_client = boto3.client('s3', region_name='ap-south-1')
CF_BASE_URL = "https://streamsync-videos-meen.s3.ap-south-1.amazonaws.com/videos"
BUCKET_NAME = "streamsync-videos-meen"

# Configurable options
INCLUDE_ALL_AFTER_T = True  # Include all videos after current
LOOP_BACK_TO_START = True   # Enable looping
TIME_IN_MINUTES = False     # Use seconds

def get_sequence(user_id):
    """Fetch the user's sequence from DynamoDB."""
    table = dynamodb.Table('UserSequences')
    try:
        response = table.get_item(Key={'user_id': user_id})
        sequence = response.get('Item', {}).get('sequence', [])
        print(f"Sequence for user {user_id}: {sequence}")
        return sequence
    except Exception as e:
        print(f"Error fetching sequence for user {user_id}: {e}")
        return []

def get_segment_count(video_id):
    """Get the number of .ts segments for a video in S3."""
    prefix = f"videos/{video_id}/"
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
        if 'Contents' not in response:
            print(f"No segments found for {video_id} in S3!")
            return 0
        count = sum(1 for obj in response['Contents'] if obj['Key'].endswith('.ts'))
        print(f"Segment count for {video_id}: {count}")
        return count
    except Exception as e:
        print(f"Error listing segments for {video_id}: {e}")
        return 0

def calculate_last_segment_duration(video_duration, total_segments):
    """Calculate the duration of the last segment."""
    if total_segments <= 0:
        print(f"Invalid segment count for video: {total_segments}")
        return 0
    # Calculate the duration covered by full 2-second segments
    full_segments = total_segments - 1
    full_segments_duration = full_segments * 2
    # Last segment duration is the remainder
    last_segment_duration = video_duration - full_segments_duration
    # Ensure the duration is positive and reasonable
    if last_segment_duration <= 0 or last_segment_duration > 2:
        print(f"Warning: Invalid last segment duration ({last_segment_duration}s) for {total_segments} segments and total duration {video_duration}s")
        return 2.0  # Fallback to 2 seconds
    return round(last_segment_duration, 2)

def calculate_total_duration(sequence):
    """Calculate the total duration of the sequence."""
    if not sequence:
        return 0
    last_entry = sequence[-1]
    total_duration = float(last_entry['start_time']) + float(last_entry['duration'])
    print(f"Total duration of sequence: {total_duration}s")
    return total_duration

def generate_playlist(user_id, T):
    """Generate an HLS playlist for the user at time T."""
    sequence = get_sequence(user_id)
    if not sequence:
        print(f"No sequence found for user {user_id}")
        return "#EXTM3U\n#EXT-X-ENDLIST"
    
    # Convert T to seconds
    T_seconds = T * 60 if TIME_IN_MINUTES else T
    print(f"Requested time T: {T_seconds}s")
    
    # Calculate total duration of the sequence
    total_duration = calculate_total_duration(sequence)
    if total_duration == 0:
        print("Total duration is 0, returning empty playlist")
        return "#EXTM3U\n#EXT-X-ENDLIST"
    
    # Adjust T to loop position
    looped_T = T_seconds % total_duration if LOOP_BACK_TO_START else T_seconds
    print(f"Looped T (after applying LOOP_BACK_TO_START): {looped_T}s")
    
    # Find the current video in the sequence
    current_video_index = 0
    for i, entry in enumerate(sequence):
        start_time = float(entry['start_time'])
        duration = float(entry['duration'])
        start_time_seconds = start_time * 60 if TIME_IN_MINUTES else start_time
        end_time_seconds = start_time_seconds + (duration * 60 if TIME_IN_MINUTES else duration)
        
        if start_time_seconds <= looped_T < end_time_seconds:
            current_video_index = i
            print(f"Current video at T={looped_T}s: {entry['video_id']} (start: {start_time_seconds}s, end: {end_time_seconds}s)")
            break
    else:
        print(f"No video found at T={looped_T}s, defaulting to first video")
        current_video_index = 0
    
    # Generate playlist
    playlist = "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:2\n"
    
    # Add segments from current video
    current_entry = sequence[current_video_index]
    video_id = current_entry['video_id']
    video_duration = float(current_entry['duration'])
    start_time_seconds = float(current_entry['start_time']) * 60 if TIME_IN_MINUTES else float(current_entry['start_time'])
    offset_seconds = max(looped_T - start_time_seconds, 0)
    total_segments = get_segment_count(video_id)
    if total_segments == 0:
        print(f"No segments available for {video_id}, returning empty playlist")
        return "#EXTM3U\n#EXT-X-ENDLIST"
    
    # Validate segment count against duration
    expected_segments = int(video_duration // 2) + (1 if video_duration % 2 > 0 else 0)
    if total_segments != expected_segments:
        print(f"Warning: Segment count mismatch for {video_id}. Expected {expected_segments}, got {total_segments}")
    
    # Calculate the last segment's duration
    last_segment_duration = calculate_last_segment_duration(video_duration, total_segments)
    print(f"Last segment duration for {video_id}: {last_segment_duration}s")
    
    # Determine the starting segment based on the offset
    start_segment = min(int(offset_seconds / 2), total_segments - 1)
    print(f"Starting segment for {video_id}: {start_segment} (offset: {offset_seconds}s)")
    
    # Add segments for the current video
    for i in range(start_segment, total_segments):
        segment_duration = last_segment_duration if i == total_segments - 1 else 2.0
        playlist += f"#EXTINF:{segment_duration},\n{CF_BASE_URL}/{video_id}/segment_{i:03d}.ts\n"
    
    # Add subsequent videos if INCLUDE_ALL_AFTER_T is True
    if INCLUDE_ALL_AFTER_T:
        # Remaining videos in current loop
        for i in range(current_video_index + 1, len(sequence)):
            video_id = sequence[i]['video_id']
            video_duration = float(sequence[i]['duration'])
            total_segments = get_segment_count(video_id)
            if total_segments == 0:
                print(f"Skipping {video_id}: No segments available")
                continue
            # Validate segment count
            expected_segments = int(video_duration // 2) + (1 if video_duration % 2 > 0 else 0)
            if total_segments != expected_segments:
                print(f"Warning: Segment count mismatch for {video_id}. Expected {expected_segments}, got {total_segments}")
            last_segment_duration = calculate_last_segment_duration(video_duration, total_segments)
            print(f"Last segment duration for {video_id}: {last_segment_duration}s")
            for j in range(total_segments):
                segment_duration = last_segment_duration if j == total_segments - 1 else 2.0
                playlist += f"#EXTINF:{segment_duration},\n{CF_BASE_URL}/{video_id}/segment_{j:03d}.ts\n"
        
        # Full loop if looping is enabled
        if LOOP_BACK_TO_START:
            for i in range(current_video_index):
                video_id = sequence[i]['video_id']
                video_duration = float(sequence[i]['duration'])
                total_segments = get_segment_count(video_id)
                if total_segments == 0:
                    print(f"Skipping {video_id}: No segments available")
                    continue
                # Validate segment count
                expected_segments = int(video_duration // 2) + (1 if video_duration % 2 > 0 else 0)
                if total_segments != expected_segments:
                    print(f"Warning: Segment count mismatch for {video_id}. Expected {expected_segments}, got {total_segments}")
                last_segment_duration = calculate_last_segment_duration(video_duration, total_segments)
                print(f"Last segment duration for {video_id}: {last_segment_duration}s")
                for j in range(total_segments):
                    segment_duration = last_segment_duration if j == total_segments - 1 else 2.0
                    playlist += f"#EXTINF:{segment_duration},\n{CF_BASE_URL}/{video_id}/segment_{j:03d}.ts\n"
    
    playlist += "#EXT-X-ENDLIST"
    return playlist

@app.route('/playlist', methods=['GET'])
def playlist_endpoint():
    user_id = request.args.get('user_id')
    T = float(request.args.get('time', 0))
    if not user_id:
        return "Missing user_id", 400
    playlist = generate_playlist(user_id, T)
    return Response(playlist, mimetype='application/vnd.apple.mpegurl')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)