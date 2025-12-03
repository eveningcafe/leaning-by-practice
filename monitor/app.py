from flask import Flask, jsonify, Response
import os
import time

app = Flask(__name__)
SERVER_NAME = os.getenv('SERVER_NAME', 'unknown')
REQUEST_COUNT = 0
START_TIME = time.time()

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
    """Health check endpoint for Prometheus"""
    return jsonify({'status': 'ok', 'server': SERVER_NAME})

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    uptime = time.time() - START_TIME
    metrics_output = f"""# HELP app_requests_total Total requests handled
# TYPE app_requests_total counter
app_requests_total{{server="{SERVER_NAME}"}} {REQUEST_COUNT}

# HELP app_up Server is up
# TYPE app_up gauge
app_up{{server="{SERVER_NAME}"}} 1

# HELP app_uptime_seconds Server uptime in seconds
# TYPE app_uptime_seconds gauge
app_uptime_seconds{{server="{SERVER_NAME}"}} {uptime:.2f}
"""
    return Response(metrics_output, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
