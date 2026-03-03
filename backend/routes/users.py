from flask import Blueprint, jsonify
from app.repositories import redis_repo

bp = Blueprint('users', __name__)


@bp.route('/users', methods=['GET'])
def get_users():
    channel_ids = redis_repo.get_all_channel_ids()
    return jsonify(channel_ids)