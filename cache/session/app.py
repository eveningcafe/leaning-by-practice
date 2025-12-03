from flask import Flask, jsonify, request
import redis
import time
import os
import json

app = Flask(__name__)

redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=6379, decode_responses=True)
APP_NAME = os.getenv('APP_NAME', 'app')

@app.route('/login/<username>')
def login(username):
    session_id = request.cookies.get('session_id') or f"sess_{int(time.time())}"
    session_data = {'user': username, 'logged_in': True, 'login_app': APP_NAME}
    redis_client.setex(f'session:{session_id}', 3600, json.dumps(session_data))

    response = jsonify({'status': 'logged in', 'user': username, 'session_id': session_id, 'app': APP_NAME})
    response.set_cookie('session_id', session_id)
    return response

@app.route('/profile')
def profile():
    session_id = request.cookies.get('session_id')
    if not session_id:
        return jsonify({'error': 'not logged in', 'app': APP_NAME}), 401

    session_data = redis_client.get(f'session:{session_id}')
    if not session_data:
        return jsonify({'error': 'session expired', 'app': APP_NAME}), 401

    data = json.loads(session_data)
    return jsonify({
        'user': data['user'],
        'login_app': data['login_app'],
        'current_app': APP_NAME,
        'message': f"Session from {data['login_app']}, accessed on {APP_NAME}"
    })

@app.route('/logout')
def logout():
    session_id = request.cookies.get('session_id')
    if session_id:
        redis_client.delete(f'session:{session_id}')
    return jsonify({'status': 'logged out', 'app': APP_NAME})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
