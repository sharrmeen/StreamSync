from flask import Blueprint, jsonify
from app.extensions import request_counter
from app.repositories import redis_repo
from app.cache import local_cache

bp = Blueprint('admin', __name__)


@bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "StreamSync is running!"}), 200


@bp.route('/metrics', methods=['GET'])
def metrics():
    return jsonify({
        "total_requests": request_counter['playlist_requests'],
        "redis_keys": redis_repo.get_db_size(),
    }), 200


@bp.route('/clear-cache', methods=['GET'])
def clear_cache():
    local_cache.clear_all()
    return jsonify({"status": "success", "message": "Local caches cleared"}), 200