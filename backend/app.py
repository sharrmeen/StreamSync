from flask import Flask, request, Response
import requests
import json

app = Flask(__name__)

# Supabase configuration (replace with your project details from Supabase dashboard)
SUPABASE_URL = "https://nvppiyxveocvvnzcvlkg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52cHBpeXh2ZW9jdnZuemN2bGtnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI1ODg1MjcsImV4cCI6MjA1ODE2NDUyN30.jVuG_KFmnmKN3_koUJcKKu-0M4nVfPgCuqsOJlZimgY"  # Anon key from Supabase settings

# Cloudflare R2 base URL (replace with your actual CDN URL)
R2_BASE_URL = "https://cdn.yourdomain.workers.dev/videos"

def get_sequence(user_id):
    # # Mock sequence for testing
    # return [
    #     {"video_id": "vid1", "start_time": 0, "duration": 10},
    #     {"video_id": "vid2", "start_time": 10, "duration": 5},
    #     {"video_id": "vid3", "start_time": 15, "duration": 15}
    # ]
    """Fetch user's sequence from Supabase."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }
    url = f"{SUPABASE_URL}/rest/v1/user_sequences?user_id=eq.{user_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200 and response.json():
        return response.json()[0]["sequence"]
    return []

def generate_playlist(user_id, T):
    """Generate an HLS playlist based on login time T (minutes since 00:00)."""
    sequence = get_sequence(user_id)
    if not sequence:
        return "#EXTM3U\n#EXT-X-ENDLIST"  # Empty playlist if no sequence

    playlist = "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:2\n"
    current_video, start_segment = None, None
    sequence_started = False

    # Find current video and segment
    for entry in sequence:
        start_time = entry["start_time"]
        duration = entry["duration"]
        if start_time <= T < start_time + duration:
            sequence_started = True
            current_video = entry["video_id"]
            offset_minutes = T - start_time
            offset_seconds = offset_minutes * 60
            start_segment = int(offset_seconds / 2)  # 2-second segments
            total_segments = int(duration * 60 / 2)
            # Add remaining segments of current video
            for i in range(start_segment, total_segments):
                playlist += f"#EXTINF:2.0,\n{R2_BASE_URL}/{current_video}/{i}.ts\n"
        elif sequence_started:
            # Add all segments of subsequent videos
            total_segments = int(duration * 60 / 2)
            for i in range(total_segments):
                playlist += f"#EXTINF:2.0,\n{R2_BASE_URL}/{entry['video_id']}/{i}.ts\n"

    playlist += "#EXT-X-ENDLIST"
    return playlist

@app.route('/playlist', methods=['GET'])
def playlist_endpoint():
    """API endpoint to serve the playlist."""
    user_id = request.args.get('user_id')
    T = float(request.args.get('time', 0))  # Time in minutes
    if not user_id:
        return "Missing user_id", 400
    playlist = generate_playlist(user_id, T)
    return Response(playlist, mimetype='application/vnd.apple.mpegurl')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)