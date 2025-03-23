import os
import subprocess
import boto3
from pathlib import Path

# Configuration
VIDEO_DIR = "videos"
S3_BUCKET = "streamsync-videos-meen"
S3_REGION = "ap-south-1"
VIDEO_IDS = ["video1", "video2", "video3", "video4", "video5", "video6"]

# Initialize S3 client
s3_client = boto3.client('s3', region_name=S3_REGION)

def run_command(command, error_message):
    """Run a shell command and handle errors."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"{error_message}: {e}")
        print(f"Error output: {e.stderr}")
        return False

def get_video_duration(video_path):
    """Get the duration of a video or segment using ffprobe."""
    command = f'ffprobe -i "{video_path}" -show_entries format=duration -v quiet -of csv="p=0"'
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        duration = float(result.stdout.strip())
        return duration
    except subprocess.CalledProcessError as e:
        print(f"Error getting duration for {video_path}: {e}")
        return 0

def segment_video(video_id):
    """Segment a video into 2-second HLS segments with forced keyframes."""
    input_path = f"{VIDEO_DIR}/{video_id}.mp4"
    output_dir = f"{VIDEO_DIR}/{video_id}"
    segment_pattern = f"{output_dir}/segment_%03d.ts"
    playlist_path = f"{output_dir}/playlist.m3u8"

    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Verify input file exists
    if not os.path.exists(input_path):
        print(f"Input file {input_path} not found!")
        return False

    # Get video duration
    video_duration = get_video_duration(input_path)
    if video_duration <= 0:
        print(f"Could not determine duration for {video_id}!")
        return False
    print(f"{video_id} duration: {video_duration:.2f} seconds")

    # FFmpeg command to force keyframes every 2 seconds and segment
    command = (
        f'ffmpeg -i "{input_path}" -force_key_frames "expr:gte(t,n_forced*2)" '
        f'-c:v libx264 -c:a aac -hls_time 2 -hls_list_size 0 '
        f'-hls_segment_filename "{segment_pattern}" "{playlist_path}" -y'
    )
    if not run_command(command, f"Failed to segment {video_id}"):
        return False

    # Verify segment count
    expected_segments = int(video_duration // 2)
    if video_duration % 2 > 0:  # If there's a remainder, add one more segment
        expected_segments += 1
    actual_segments = len([f for f in os.listdir(output_dir) if f.startswith("segment_") and f.endswith(".ts")])
    print(f"{video_id}: Expected {expected_segments} segments, got {actual_segments} segments")
    
    if actual_segments != expected_segments:
        print(f"Warning: Segment count mismatch for {video_id}! Check FFmpeg output or video duration.")
        return False

    # Verify segment durations
    for i in range(actual_segments):
        segment_path = f"{output_dir}/segment_{i:03d}.ts"
        duration = get_video_duration(segment_path)
        if not (1.9 <= duration <= 2.1):  # Allow small variance
            print(f"Warning: Segment {segment_path} duration is {duration:.2f}s, expected ~2s")
            return False

    return True

def upload_to_s3(video_id):
    """Upload segmented files to S3."""
    local_dir = f"{VIDEO_DIR}/{video_id}"
    s3_prefix = f"videos/{video_id}"

    # Clear existing S3 contents
    print(f"Clearing existing S3 contents for {s3_prefix}...")
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=s3_prefix)
        if 'Contents' in response:
            objects = [{'Key': obj['Key']} for obj in response['Contents']]
            s3_client.delete_objects(Bucket=S3_BUCKET, Delete={'Objects': objects})
    except Exception as e:
        print(f"Error clearing S3 contents for {s3_prefix}: {e}")
        return False

    # Upload new segments
    command = (
        f'aws s3 sync "{local_dir}/" s3://{S3_BUCKET}/{s3_prefix}/ '
        f'--exclude "*" --include "*.ts" --include "playlist.m3u8"'
    )
    if not run_command(command, f"Failed to upload {video_id} to S3"):
        return False

    # Verify S3 segment count
    video_duration = get_video_duration(f"{local_dir}/../{video_id}.mp4")
    expected_segments = int(video_duration // 2)
    if video_duration % 2 > 0:
        expected_segments += 1
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=f"{s3_prefix}/")
        actual_segments = sum(1 for obj in response.get('Contents', []) 
                            if obj['Key'].endswith('.ts') and 'segment_' in obj['Key'])
        print(f"S3 {video_id}: Expected {expected_segments} segments, got {actual_segments} segments")
        if actual_segments != expected_segments:
            print(f"Error: S3 segment count mismatch for {video_id}!")
            return False
    except Exception as e:
        print(f"Error verifying S3 contents for {video_id}: {e}")
        return False

    return True

def main():
    """Main function to segment and upload all videos."""
    for video_id in VIDEO_IDS:
        print(f"\nProcessing {video_id}...")
        
        # Segment the video
        if not segment_video(video_id):
            print(f"Failed to segment {video_id}. Skipping upload.")
            continue
        
        # Upload to S3
        if not upload_to_s3(video_id):
            print(f"Failed to upload {video_id} to S3.")
            continue
        
        print(f"Successfully processed and uploaded {video_id}!")

if __name__ == "__main__":
    main()