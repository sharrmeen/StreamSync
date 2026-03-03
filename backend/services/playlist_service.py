import time
import logging
from datetime import datetime, timezone

from app.config import Config
from app.repositories import redis_repo
from app.services import metadata_service

#calculates what every channel should be broadcasting at any given moment
#and builds the HLS M3U8 playlist string
def _calculate_total_duration(sequence: list) -> float:
    if not sequence:
        return 0.0
    last = sequence[-1]
    total = float(last['start_time']) + float(last['duration'])
    logging.info(f"Total sequence duration: {total:.3f}s")
    return total


def _resolve_T(T: float | None) -> float: 
    if T is not None:
        return T * 60 if Config.TIME_IN_MINUTES else T

    elapsed = time.time() - Config.GLOBAL_SYNC_REFERENCE
    logging.info(f"Derived T from global clock: {elapsed:.3f}s since {Config.STREAM_START}")
    return elapsed


def _find_current_video_index(sequence: list, looped_T: float) -> int:
    """Find which video in the sequence is playing at looped_T seconds."""
    for i, entry in enumerate(sequence):
        start = float(entry['start_time'])
        end = start + float(entry['duration'])
        if start <= looped_T < end:
            logging.info(
                f"Playing video[{i}] '{entry['video_id']}' "
                f"at T={looped_T:.3f}s (window: {start}s–{end}s)"
            )
            return i

    logging.warning(f"No video matched T={looped_T:.3f}s, defaulting to index 0")
    return 0


def generate_playlist(channel_id: str, T: float | None = None) -> str:
    """Build and return a full HLS M3U8 playlist string for the given channel."""
    start_time = time.time()

    sequence = redis_repo.get_sequence(channel_id)
    if not sequence:
        return "#EXTM3U\n#EXT-X-ENDLIST"

    total_duration = _calculate_total_duration(sequence)
    if total_duration == 0:
        return "#EXTM3U\n#EXT-X-ENDLIST"

    T_seconds = _resolve_T(T)
    looped_T = T_seconds % total_duration if Config.LOOP_BACK_TO_START else T_seconds
    logging.info(f"Looped T: {looped_T:.6f}s")

    #bulk-fetch all metadata 
    video_ids = [entry['video_id'] for entry in sequence]
    metadata = metadata_service.batch_get_metadata(video_ids)

    current_idx = _find_current_video_index(sequence, looped_T)

    now_utc = datetime.now(timezone.utc)
    playlist = (
        f"#EXTM3U\n"
        f"#EXT-X-VERSION:3\n"
        f"#EXT-X-TARGETDURATION:{Config.MAX_SEGMENT_DURATION}\n"
        f"#EXT-X-PROGRAM-DATE-TIME:{now_utc.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}\n"
    )

    #calculate sub segment offset so the player starts at the exact frame
    offset_in_video = looped_T - float(sequence[current_idx]['start_time'])
    current_segment = int(offset_in_video / Config.SEGMENT_DURATION)
    segment_time_offset = offset_in_video % Config.SEGMENT_DURATION
    playlist += f"#EXT-X-START:TIME-OFFSET={segment_time_offset:.6f},PRECISE=YES\n"
 
    if Config.INCLUDE_ALL_AFTER_T:
        indices = list(range(current_idx, len(sequence)))
        if Config.LOOP_BACK_TO_START:
            indices += list(range(0, current_idx))
    else:
        indices = [current_idx]
 
    first_video = True
    for idx in indices:
        entry = sequence[idx]
        video_id = entry['video_id']
        video_duration = float(entry['duration'])

        total_segments = metadata_service.get_segment_count(video_id, metadata)
        if total_segments == 0:
            logging.warning(f"No segments for {video_id}, skipping")
            continue

        start_segment = current_segment if (idx == current_idx and first_video) else 0
        first_video = False

        last_seg_dur = metadata_service.get_last_segment_duration(
            video_id, video_duration, total_segments, metadata
        )

        for i in range(start_segment, total_segments):
            seg_dur = last_seg_dur if i == total_segments - 1 else Config.SEGMENT_DURATION
            playlist += (
                f"#EXTINF:{seg_dur:.6f},\n"
                f"{Config.CDN_BASE_URL}/{video_id}/segment_{i:03d}.ts\n"
            )

    playlist += "#EXT-X-ENDLIST"

    
    elapsed_ms = (time.time() - start_time) * 1000
    stream_age = (datetime.now(timezone.utc) - Config.STREAM_START).total_seconds()
    first_seg = next((l for l in playlist.split('\n') if l.endswith('.ts')), "none")
    logging.info(
        f"[{channel_id}] Playlist generated in {elapsed_ms:.2f}ms | "
        f"stream_age={stream_age:.1f}s | looped_T={looped_T:.3f}s | "
        f"offset={offset_in_video:.3f}s | first_seg={first_seg} | "
        f"time_offset={segment_time_offset:.6f}"
    )

    return playlist