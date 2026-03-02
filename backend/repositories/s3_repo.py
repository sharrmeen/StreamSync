import logging
from app.extensions import s3_client
from app.config import Config
from app.cache import local_cache


def get_segment_count(video_id: str) -> int:
 
    if video_id in local_cache.segment_count_cache:
        return local_cache.segment_count_cache[video_id]

    prefix = f"videos/{video_id}/"
    try:
        response = s3_client.list_objects_v2(Bucket=Config.BUCKET_NAME, Prefix=prefix)
        if 'Contents' not in response:
            logging.warning(f"No objects found in MinIO for prefix: {prefix}")
            return 0

        count = sum(1 for obj in response['Contents'] if obj['Key'].endswith('.ts'))
        logging.info(f"Segment count for {video_id} (from MinIO): {count}")
        local_cache.segment_count_cache[video_id] = count
        return count

    except Exception as e:
        logging.error(f"Error listing segments for {video_id}: {e}")
        return 0