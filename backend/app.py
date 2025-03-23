from flask import Flask, request, Response
import boto3

app = Flask(__name__)
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
s3_client = boto3.client('s3', region_name='ap-south-1')
CF_BASE_URL = "https://d3oe22crr7rljh.cloudfront.net/videos"
BUCKET_NAME = "streamsync-videos-meen"

# Configurable options
INCLUDE_ALL_AFTER_T = True  # Tweak 1: Include all videos after T (True) or just current (False)
LOOP_BACK_TO_START = False  # Tweak 2: Loop to video1 after last video (True) or stop (False)
TIME_IN_MINUTES = False     # Tweak 3: Treat start_time/duration as minutes (True) or seconds (False)

def get_sequence(user_id):
    table = dynamodb.Table('UserSequences')
    response = table.get_item(Key={'user_id': user_id})
    return response.get('Item', {}).get('sequence', [])

def get_segment_count(video_id):
    prefix = f"videos/{video_id}/"
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
        if 'Contents' not in response:
            return 0
        return sum(1 for obj in response['Contents'] if obj['Key'].endswith('.ts'))
    except Exception as e:
        print(f"Error listing {video_id}: {e}")
        return 0

def generate_playlist(user_id, T):
    sequence = get_sequence(user_id)
    if not sequence:
        return "#EXTM3U\n#EXT-X-ENDLIST"
    
    # Convert T to seconds
    T_seconds = T * 60 if TIME_IN_MINUTES else T
    
    # Find the current video in the sequence
    current_video_index = 0
    for i, entry in enumerate(sequence):
        start_time = int(entry['start_time'])
        duration = int(entry['duration'])
        start_time_seconds = start_time * 60 if TIME_IN_MINUTES else start_time
        end_time_seconds = start_time_seconds + (duration * 60 if TIME_IN_MINUTES else duration)
        
        if start_time_seconds <= T_seconds < end_time_seconds:
            current_video_index = i
            break
        elif T_seconds >= end_time_seconds:
            current_video_index = i + 1
    
    # Handle case where T is past the last video
    if current_video_index >= len(sequence):
        if LOOP_BACK_TO_START:
            current_video_index = 0
        else:
            return "#EXTM3U\n#EXT-X-ENDLIST"
    
    # Generate playlist
    playlist = "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:2\n"
    
    # Add segments from current video
    current_entry = sequence[current_video_index]
    video_id = current_entry['video_id']
    start_time_seconds = int(current_entry['start_time']) * 60 if TIME_IN_MINUTES else int(current_entry['start_time'])
    offset_seconds = max(T_seconds - start_time_seconds, 0)
    total_segments = get_segment_count(video_id)
    start_segment = min(int(offset_seconds / 2), total_segments - 1)
    
    for i in range(start_segment, total_segments):
        playlist += f"#EXTINF:2.0,\n{CF_BASE_URL}/{video_id}/segment_{i:03d}.ts\n"
    
    # Add subsequent videos if INCLUDE_ALL_AFTER_T is True
    if INCLUDE_ALL_AFTER_T:
        for i in range(current_video_index + 1, len(sequence)):
            video_id = sequence[i]['video_id']
            total_segments = get_segment_count(video_id)
            for j in range(total_segments):
                playlist += f"#EXTINF:2.0,\n{CF_BASE_URL}/{video_id}/segment_{j:03d}.ts\n"
    
    # Add looping videos if enabled
    if LOOP_BACK_TO_START:
        for i in range(current_video_index):
            video_id = sequence[i]['video_id']
            total_segments = get_segment_count(video_id)
            for j in range(total_segments):
                playlist += f"#EXTINF:2.0,\n{CF_BASE_URL}/{video_id}/segment_{j:03d}.ts\n"
    
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
    app.run(host='0.0.0.0', port=5000)