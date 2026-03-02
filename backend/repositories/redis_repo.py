import json
import logging
from app.extensions import redis_client
from app.cache import local_cache

#return the order of videos for a specific channel, use cache if available
def get_sequence(channel_id: str) -> list:
    if channel_id in local_cache.sequence_cache:
        return local_cache.sequence_cache[channel_id]

    data = redis_client.get(f"user_sequence:{channel_id}")
    if data:
        sequence = json.loads(data)
        logging.info(f"Sequence for channel {channel_id} loaded from Redis ({len(sequence)} entries)")
        local_cache.sequence_cache[channel_id] = sequence
        return sequence

    logging.warning(f"No sequence found for channel {channel_id}")
    return []

#return total duration,last segment duration
def get_video_metadata(video_id: str) -> tuple | None: 
    if video_id in local_cache.video_metadata_cache:
        return local_cache.video_metadata_cache[video_id]

    data = redis_client.get(f"video_metadata:{video_id}")
    if data:
        total_segments, last_segment_duration = json.loads(data)
        result = (total_segments, last_segment_duration)
        logging.info(f"Metadata for {video_id}: segments={total_segments}, last_dur={last_segment_duration}s")
        local_cache.video_metadata_cache[video_id] = result
        return result

    logging.warning(f"No metadata in Redis for {video_id}, defaulting")
    return None


def batch_get_video_metadata(video_ids: list[str]) -> dict:
    result = {}
    missing = []

    for vid in video_ids:
        if vid in local_cache.video_metadata_cache:
            result[vid] = local_cache.video_metadata_cache[vid]
        else:
            missing.append(vid)

    for vid in missing:
        meta = get_video_metadata(vid)
        result[vid] = meta if meta is not None else (0, 2.0)

    return result


def get_playlist_cache(cache_key: str) -> str | None:
    return redis_client.get(cache_key)


def set_playlist_cache(cache_key: str, playlist: str, ttl: int):
    redis_client.setex(cache_key, ttl, playlist)


def get_all_channel_ids() -> list[str]:
    keys = redis_client.keys("user_sequence:*")
    return [key.split(":")[1] for key in keys]


def get_db_size() -> int:
    return redis_client.dbsize()