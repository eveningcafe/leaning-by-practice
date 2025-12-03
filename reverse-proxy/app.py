from flask import Flask, jsonify, request
import os

app = Flask(__name__)
SERVER_NAME = os.getenv('SERVER_NAME', 'unknown')

@app.route('/')
def home():
    # Show how reverse proxy passes information to backend
    return jsonify({
        'server': SERVER_NAME,
        'message': f'Handled by {SERVER_NAME}',
        'client_info': {
            'real_ip': request.headers.get('X-Real-IP', 'unknown'),
            'forwarded_for': request.headers.get('X-Forwarded-For', 'unknown'),
            'protocol': request.headers.get('X-Forwarded-Proto', 'http'),
            'host': request.headers.get('Host', 'unknown')
        },
        'note': 'Backend receives plain HTTP, but client used HTTPS (SSL terminated at Nginx)'
    })

@app.route('/secure-data')
def secure_data():
    """Simulate sensitive endpoint - only accessible via HTTPS"""
    proto = request.headers.get('X-Forwarded-Proto', 'http')
    return jsonify({
        'server': SERVER_NAME,
        'protocol_used': proto,
        'data': 'This sensitive data was transmitted securely via HTTPS',
        'ssl_terminated_at': 'Nginx (reverse proxy)'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'server': SERVER_NAME})

if __name__ == '__main__':
    # Backend runs on plain HTTP - SSL is handled by Nginx
    app.run(host='0.0.0.0', port=5000)
