import boto3
import redis as redis_lib
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from collections import Counter
from app.config import Config

#common redis client across app
redis_client = redis_lib.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=Config.REDIS_DB,
    decode_responses=True
)

#minio client
s3_client = boto3.client(
    's3',
    endpoint_url=Config.MINIO_ENDPOINT,
    aws_access_key_id=Config.MINIO_ACCESS_KEY,
    aws_secret_access_key=Config.MINIO_SECRET_KEY,
    region_name='us-east-1'
)

#rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

request_counter = Counter()