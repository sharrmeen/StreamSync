import boto3
import os
import subprocess
import tempfile
import shutil

# Configuration
S3_BUCKET = "streamsync-videos-meen"
S3_REGION = "ap-south-1"
VIDEO_IDS = ["video1", "video2", "video3", "video4", "video5", "video6"]

# Initialize AWS clients
s3_client = boto3.client('s3', region_name=S3_REGION)

def get_segment_duration(segment_path):
    """Get the duration of a segment using ffprobe."""
    command = f'ffprobe -i "{segment_path}" -show_entries format=duration -v quiet -of csv="p=0"'
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        duration = float(result.stdout.strip())
        return duration
    except (subprocess.CalledProcessError, ValueError) as e:
        print(f"Error getting duration for {segment_path}: {e}")
        return 0

def calculate_video_duration(video_id):
    """Calculate the total duration of a video by summing its segment durations from S3."""
    prefix = f"videos/{video_id}/"
    temp_dir = tempfile.mkdtemp()
    total_duration = 0.0

    try:
        # List all .ts segments in S3
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
        if 'Contents' not in response:
            print(f"No segments found for {video_id} in S3!")
            return 0

        segments = [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.ts')]
        if not segments:
            print(f"No .ts files found for {video_id} in S3!")
            return 0

        print(f"Calculating duration for {video_id} ({len(segments)} segments)...")
        for segment_key in segments:
            # Download the segment to a temporary file
            segment_filename = os.path.basename(segment_key)
            local_path = os.path.join(temp_dir, segment_filename)
            s3_client.download_file(S3_BUCKET, segment_key, local_path)

            # Get the segment duration
            duration = get_segment_duration(local_path)
            total_duration += duration
            print(f"Segment {segment_filename}: {duration:.2f}s")

            # Clean up the temporary file
            os.remove(local_path)

        total_duration = round(total_duration, 2)
        print(f"Total duration for {video_id}: {total_duration}s")
        return total_duration

    except Exception as e:
        print(f"Error calculating duration for {video_id}: {e}")
        return 0
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir)

def main():
    """Calculate durations for all videos."""
    video_durations = {}
    for video_id in VIDEO_IDS:
        duration = calculate_video_duration(video_id)
        if duration > 0:
            video_durations[video_id] = duration
    print("\nCalculated durations:", video_durations)

if __name__ == "__main__":
    main()