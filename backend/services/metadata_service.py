import math
import logging
from app.repositories import redis_repo, s3_repo

#return total .ts segment count for a video
def get_segment_count(video_id: str, metadata: dict = None) -> int:
    if metadata and video_id in metadata:
        count = metadata[video_id][0]
        return count

    return s3_repo.get_segment_count(video_id)


def get_last_segment_duration(video_id: str, video_duration: float,
                               total_segments: int, metadata: dict = None) -> float:
    if total_segments <= 0:
        logging.warning(f"Invalid segment count for {video_id}: {total_segments}")
        return 0.0

    if metadata and video_id in metadata:
        return metadata[video_id][1]

    expected_segments = math.ceil(video_duration / 2)
    total_segments = min(total_segments, expected_segments)
    full_segments_duration = (total_segments - 1) * 2
    last_duration = video_duration - full_segments_duration

    last_duration = min(max(last_duration, 0.1), 2.0)
    return round(last_duration, 3)


def batch_get_metadata(video_ids: list[str]) -> dict:
    return redis_repo.batch_get_video_metadata(video_ids)