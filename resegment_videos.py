import os
import subprocess
import json
import redis
import boto3
from botocore.client import Config
from pathlib import Path

# Configuration
VIDEO_DIR = "./videos"  # Directory containing video1.mp4, video2.mp4, etc.
OUTPUT_BASE_DIR = "./output_videos"  # Temporary output directory
MINIO_ENDPOINT = "http://localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin`"
MINIO_BUCKET = "streamsync-videos-meen"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
VIDEO_IDS = [f"video{i}" for i in range(1, 7)]  # video1 to video6

# Initialize clients
s3_client = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version="s3v4"),
)
redis_client = redis.Redis(
    host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
)

def resegment_video(video_id, input_file, output_dir):
    """Re-segment a video into ~2-second .ts files with proper naming."""
    output_dir = Path(output_dir) / video_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_m3u8 = output_dir / "output.m3u8"

    # FFmpeg command for 2-second segments
    cmd = [
        "ffmpeg",
        "-i", str(input_file),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-f", "hls",
        "-hls_time", "2",
        "-force_key_frames", "expr:gte(t,n_forced*2)",
        "-reset_timestamps", "1",
        "-hls_segment_type", "mpegts",
        "-hls_flags", "independent_segments",
        "-hls_segment_filename", f"{output_dir}/segment_%03d.ts",
        "-hls_playlist_type", "event",
        str(output_m3u8),
    ]

    print(f"Re-segmenting {video_id}...")
    subprocess.run(cmd, check=True)

    # Verify segment durations using ffprobe
    segments = sorted(output_dir.glob("segment_*.ts"))
    durations = []
    for seg in segments:
        cmd = [
            "ffprobe",
            "-i", str(seg),
            "-show_entries", "format=duration",
            "-v", "quiet",
            "-of", "csv=p=0",
        ]
        duration = float(subprocess.check_output(cmd).decode().strip())
        durations.append(duration)
        print(f"{seg.name}: {duration:.6f} seconds")

    segment_count = len(segments)
    last_duration = durations[-1] if durations else 2.0
    return segment_count, last_duration

def upload_to_minio(video_id, output_dir):
    """Upload .ts files to MinIO."""
    output_dir = Path(output_dir) / video_id
    for ts_file in output_dir.glob("segment_*.ts"):
        minio_path = f"videos/{video_id}/{ts_file.name}"
        print(f"Uploading {ts_file} to {minio_path}...")
        s3_client.upload_file(
            str(ts_file),
            MINIO_BUCKET,
            minio_path,
            ExtraArgs={"ContentType": "video/MP2T"},
        )

def update_redis(video_id, segment_count, last_duration):
    """Update Redis with segment count and last segment duration."""
    metadata = [segment_count, last_duration]
    redis_client.set(f"video_metadata:{video_id}", json.dumps(metadata))
    print(f"Updated Redis: video_metadata:{video_id} = {metadata}")

def main():
    # Create output base directory
    Path(OUTPUT_BASE_DIR).mkdir(exist_ok=True)

    for video_id in VIDEO_IDS:
        input_file = Path(VIDEO_DIR) / f"{video_id}.mp4"
        if not input_file.exists():
            print(f"Skipping {video_id}: {input_file} not found.")
            continue

        # Re-segment video
        segment_count, last_duration = resegment_video(
            video_id, input_file, OUTPUT_BASE_DIR
        )

        # Upload to MinIO
        upload_to_minio(video_id, OUTPUT_BASE_DIR)

        # Update Redis
        update_redis(video_id, segment_count, last_duration)

    print("All videos processed.")

if __name__ == "__main__":
    main()