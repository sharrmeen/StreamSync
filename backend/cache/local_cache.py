sequence_cache: dict      = {}
segment_count_cache: dict = {}
video_metadata_cache: dict = {}


def clear_all():
    sequence_cache.clear()
    segment_count_cache.clear()
    video_metadata_cache.clear()
