import redis

try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    r.ping()
    print("Redis connected")
except redis.exceptions.ConnectionError:
    print("Redis connection failed")
    r = None