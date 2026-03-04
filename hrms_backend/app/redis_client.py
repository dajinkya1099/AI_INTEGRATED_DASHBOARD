import redis

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Test connection
try:
    pong = r.ping()
    print("Redis connected:", pong)
except redis.ConnectionError:
    print("Redis connection failed")