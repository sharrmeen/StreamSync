import time
from flask import Blueprint, request, Response, jsonify
from app.extensions import limiter, request_counter
from app.repositories import redis_repo
from app.services import playlist_service
from app.config import Config

bp = Blueprint('playlist', __name__)


@bp.route('/playlist', methods=['GET'])
@limiter.limit("40 per minute")
def playlist_endpoint():
    request_counter['playlist_requests'] += 1

    channel_id = request.args.get('user_id')
    if not channel_id:
        return jsonify({"error": "Missing user_id", "message": "Please provide a user_id parameter"}), 400

    T = request.args.get('time')
    if T is not None:
        try:
            T = float(T)
        except ValueError:
            return jsonify({"error": "Invalid time parameter", "message": "Time must be a number"}), 400

    raw_T = T if T is not None else time.time() - Config.GLOBAL_SYNC_REFERENCE
    cache_T = Config.SEGMENT_DURATION * round(raw_T / Config.SEGMENT_DURATION)
    cache_key = f"playlist:{channel_id}:T={cache_T}"

    cached = redis_repo.get_playlist_cache(cache_key)
    if cached:
        m3u8 = cached
    else:
        m3u8 = playlist_service.generate_playlist(channel_id, T)
        redis_repo.set_playlist_cache(cache_key, m3u8, Config.PLAYLIST_CACHE_TTL)

    response = Response(m3u8, mimetype='application/vnd.apple.mpegurl')
    response.headers['X-Server-Time'] = str(time.time())
    response.headers['X-Global-Reference'] = str(Config.GLOBAL_SYNC_REFERENCE)
    response.headers['Access-Control-Expose-Headers'] = 'X-Server-Time, X-Global-Reference'
    return response