import subprocess
import json
import redis
import urllib.request
import re
from pathlib import Path
from typing import Dict, List, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
SOURCE_VIDEO_DIR = "./videos/"
MINIO_BASE_URL = "http://localhost:9000/streamsync-videos-meen/videos/"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
VIDEOS = ["video1", "video2", "video3", "video4"]
EXPECTED_METADATA = {
    "video1": [14, 1.7],    # 14 segments, last at 1.7s
    "video2": [6, 1.9],     # 6 segments, last at 1.9s
    "video3": [20, 1.92],   # 20 segments, last at 1.92s
    "video4": [7, 1.472],   # 7 segments, last at 1.472s
}
PLAYLIST_EXTINF = {
    "video1": [(0, 12, 2.0), (13, 13, 1.7)],
    "video2": [(0, 4, 2.0), (5, 5, 1.9)],
    "video3": [(16, 18, 2.0), (19, 19, 1.92)],
    "video4": [(0, 5, 2.0), (6, 6, 1.472)],
}

def run_ffprobe(url_or_path: str) -> float:
    """Run ffprobe to get duration of a video or segment."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        url_or_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        logger.error(f"ffprobe failed for {url_or_path}: {e}")
        return -1.0

def get_source_video_duration(video_id: str) -> float:
    """Get duration of source video file."""
    video_path = Path(SOURCE_VIDEO_DIR) / f"{video_id}.mp4"
    if not video_path.exists():
        logger.error(f"Source video {video_path} not found")
        return -1.0
    return run_ffprobe(str(video_path))

def get_segment_duration(video_id: str, segment_index: int) -> float:
    """Get duration of a .ts segment in MinIO."""
    segment_url = f"{MINIO_BASE_URL}{video_id}/segment_{segment_index:03d}.ts"
    try:
        urllib.request.urlopen(segment_url)  # Check if segment exists
        return run_ffprobe(segment_url)
    except urllib.error.HTTPError as e:
        logger.error(f"Failed to access {segment_url}: {e}")
        return -1.0

def get_redis_metadata(video_id: str) -> Tuple[int, float]:
    """Fetch metadata from Redis."""
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    metadata_str = redis_client.get(f"video_metadata:{video_id}")
    if metadata_str:
        metadata = json.loads(metadata_str)
        return metadata[0], metadata[1]
    logger.error(f"No Redis metadata for {video_id}")
    return -1, -1.0

def compare_durations(
    video_id: str,
    source_duration: float,
    segment_durations: List[float],
    redis_metadata: Tuple[int, float],
    expected_metadata: Tuple[int, float]
) -> Dict:
    """Compare durations and return analysis."""
    result = {
        "video_id": video_id,
        "source_duration": source_duration,
        "segment_durations": segment_durations,
        "redis_metadata": redis_metadata,
        "expected_metadata": expected_metadata,
        "discrepancies": [],
        "conclusion": ""
    }

    # Check source duration
    expected_total = sum(2.0 for _ in range(expected_metadata[0] - 1)) + expected_metadata[1]
    if abs(source_duration - expected_total) > 0.1:
        result["discrepancies"].append(
            f"Source duration ({source_duration:.3f}s) differs from expected ({expected_total:.3f}s)"
        )

    # Check segment durations
    for i, duration in enumerate(segment_durations):
        if duration < 0:
            result["discrepancies"].append(f"Segment {i:03d} is missing or inaccessible")
            continue
        for start, end, expected_duration in PLAYLIST_EXTINF[video_id]:
            if start <= i <= end:
                if abs(duration - expected_duration) > 0.1:
                    result["discrepancies"].append(
                        f"Segment {i:03d} duration ({duration:.3f}s) differs from #EXTINF ({expected_duration:.3f}s)"
                    )
                break

    # Check Redis metadata
    if redis_metadata != expected_metadata:
        result["discrepancies"].append(
            f"Redis metadata {redis_metadata} differs from expected {expected_metadata}"
        )

    # Conclusion
    if result["discrepancies"]:
        result["conclusion"] = f"Issues found. Reprocess {video_id}.mp4 and update Redis metadata."
    else:
        result["conclusion"] = "All durations and metadata are consistent."

    return result

def suggest_fixes(video_id: str) -> List[str]:
    """Suggest commands to fix discrepancies."""
    return [
        f"# Reprocess {video_id}.mp4",
        f"ffmpeg -i ./videos/{video_id}.mp4 -c:v libx264 -c:a aac -f hls -hls_time 2 -hls_list_size 0 -hls_segment_filename \"{video_id}/segment_%03d.ts\" {video_id}/playlist.m3u8",
        f"mc cp {video_id}/segment_*.ts myminio/streamsync-videos-meen/videos/{video_id}/",
        f"# Update Redis metadata",
        f"python -c \"import redis, json; redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True); redis_client.set('video_metadata:{video_id}', json.dumps({EXPECTED_METADATA[video_id]}))\""
    ]

def main():
    """Main function to verify durations and print results."""
    results = []

    for video_id in VIDEOS:
        logger.info(f"Verifying {video_id}...")

        # Step 1: Source video duration
        source_duration = get_source_video_duration(video_id)
        logger.info(f"Source duration for {video_id}.mp4: {source_duration:.3f}s")

        # Step 2: Segment durations
        segment_count = EXPECTED_METADATA[video_id][0]
        segment_durations = []
        for i in range(segment_count):
            duration = get_segment_duration(video_id, i)
            segment_durations.append(duration)
            logger.info(f"Segment {video_id}/segment_{i:03d}.ts: {duration:.3f}s")

        # Step 3: Redis metadata
        redis_metadata = get_redis_metadata(video_id)
        logger.info(f"Redis metadata for {video_id}: {redis_metadata}")

        # Step 4: Compare durations
        result = compare_durations(
            video_id,
            source_duration,
            segment_durations,
            redis_metadata,
            EXPECTED_METADATA[video_id]
        )
        results.append(result)

    # Print results and conclusions
    print("\n=== Duration Verification Report ===")
    for result in results:
        video_id = result["video_id"]
        print(f"\nVideo: {video_id}")
        print(f"Source Duration: {result['source_duration']:.3f}s")
        print("Segment Durations:")
        for i, duration in enumerate(result["segment_durations"]):
            print(f"  segment_{i:03d}.ts: {duration:.3f}s")
        print(f"Redis Metadata: {result['redis_metadata']}")
        print(f"Expected Metadata: {result['expected_metadata']}")
        print("Discrepancies:")
        for discrepancy in result["discrepancies"]:
            print(f"  - {discrepancy}")
        print(f"Conclusion: {result['conclusion']}")
        if result["discrepancies"]:
            print("Suggested Fixes:")
            for fix in suggest_fixes(video_id):
                print(f"  {fix}")

    # Overall conclusion
    print("\n=== Overall Conclusion ===")
    if any(result["discrepancies"] for result in results):
        print("Issues detected. Reprocess affected videos and update Redis metadata as suggested.")
        print("Focus on video4/segment_003.ts (stall at ~14s). After fixes, test with:")
        print("  curl 'http://localhost:5001/playlist?user_id=test_user' > playlist.m3u8")
        print("  vlc playlist.m3u8")
        print("  Visit http://localhost:8080/dashboard/test_user")
    else:
        print("All durations and metadata are consistent. If stalls persist, check Flask playlist generation (app.py).")

if __name__ == "__main__":
    main()