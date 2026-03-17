from flask import Flask
import redis
import os

app = Flask(__name__)
cache = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'))

@app.route('/')
def hello():
    visits = cache.incr('visits')
    return f'Hello! Visits: {visits}'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)