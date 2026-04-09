from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    hostname = os.environ.get('HOSTNAME', 'unknown')
    return f'Hello from Fargate! Container: {hostname}\n'

@app.route('/health')
def health():
    return 'healthy\n'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)