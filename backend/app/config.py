import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

class Config:
    MINIO_ENDPOINT    = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    MINIO_ACCESS_KEY  = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY  = os.getenv("MINIO_SECRET_KEY")
    BUCKET_NAME       = os.getenv("BUCKET_NAME", "streamsync-videos-meen")
    REDIS_HOST        = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT        = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB          = int(os.getenv("REDIS_DB", 0))

    STREAM_START        = datetime(2025, 3, 23, 0, 0, 0, tzinfo=timezone.utc)
    GLOBAL_SYNC_REFERENCE = STREAM_START.timestamp()
    LOOP_BACK_TO_START  = True
    INCLUDE_ALL_AFTER_T = True
    TIME_IN_MINUTES     = False
    
    INCLUDE_ALL_AFTER_T = True
    LOOP_BACK_TO_START  = True
    TIME_IN_MINUTES     = False
    
    STREAM_START            = datetime(2026, 3, 7, 0, 0, 0, tzinfo=timezone.utc)
    GLOBAL_SYNC_REFERENCE   = STREAM_START.timestamp()
    
    SEGMENT_DURATION        = 2.0
    MAX_SEGMENT_DURATION    = 3
    PLAYLIST_CACHE_TTL      = 300