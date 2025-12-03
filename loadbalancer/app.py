from flask import Flask, jsonify
import os
import time

app = Flask(__name__)
SERVER_NAME = os.getenv('SERVER_NAME', 'unknown')
REQUEST_COUNT = 0

@app.route('/')
def home():
    global REQUEST_COUNT
    REQUEST_COUNT += 1
    return jsonify({
        'server': SERVER_NAME,
        'request_count': REQUEST_COUNT,
        'message': f'Handled by {SERVER_NAME}'
    })

@app.route('/heavy')
def heavy():
    """Simulate heavy processing"""
    time.sleep(1)
    return jsonify({
        'server': SERVER_NAME,
        'task': 'heavy processing done'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'server': SERVER_NAME})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
