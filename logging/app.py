#!/usr/bin/env python3
"""
Sample Application with Structured Logging

This app demonstrates:
1. JSON structured logging (better for log aggregation)
2. Different log levels (INFO, WARNING, ERROR)
3. Request logging with metadata
4. Error logging with stack traces
"""

import os
import json
import logging
import random
import time
import traceback
from datetime import datetime
from flask import Flask, request

app = Flask(__name__)
APP_NAME = os.environ.get('APP_NAME', 'app')

# Configure JSON structured logging
class JSONFormatter(logging.Formatter):
    """Format log messages as JSON for easy parsing by Filebeat."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "app": APP_NAME,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'path'):
            log_entry['path'] = record.path
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = traceback.format_exception(*record.exc_info)

        return json.dumps(log_entry)


# Setup file handler with JSON formatting
log_dir = '/var/log/app'
os.makedirs(log_dir, exist_ok=True)

file_handler = logging.FileHandler(f'{log_dir}/{APP_NAME}.log')
file_handler.setFormatter(JSONFormatter())

# Also log to console for debugging
console_handler = logging.StreamHandler()
console_handler.setFormatter(JSONFormatter())

# Configure root logger
logger = logging.getLogger(APP_NAME)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


@app.before_request
def before_request():
    """Log incoming request."""
    request.start_time = time.time()
    request.request_id = f"{APP_NAME}-{int(time.time() * 1000)}"


@app.after_request
def after_request(response):
    """Log completed request with timing."""
    duration_ms = (time.time() - request.start_time) * 1000

    extra = {
        'request_id': request.request_id,
        'method': request.method,
        'path': request.path,
        'status_code': response.status_code,
        'duration_ms': round(duration_ms, 2)
    }

    log_record = logging.LogRecord(
        name=APP_NAME,
        level=logging.INFO,
        pathname='',
        lineno=0,
        msg=f"{request.method} {request.path} - {response.status_code}",
        args=(),
        exc_info=None
    )

    for key, value in extra.items():
        setattr(log_record, key, value)

    logger.handle(log_record)
    return response


@app.route('/')
def index():
    """Main endpoint."""
    logger.info(f"Homepage accessed from {APP_NAME}")
    return json.dumps({
        "app": APP_NAME,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route('/health')
def health():
    """Health check endpoint."""
    return json.dumps({"status": "healthy", "app": APP_NAME})


@app.route('/user/<user_id>')
def get_user(user_id):
    """Simulate user lookup with logging."""
    extra = {'user_id': user_id}

    log_record = logging.LogRecord(
        name=APP_NAME,
        level=logging.INFO,
        pathname='',
        lineno=0,
        msg=f"User lookup: {user_id}",
        args=(),
        exc_info=None
    )
    log_record.user_id = user_id
    logger.handle(log_record)

    return json.dumps({"user_id": user_id, "name": f"User {user_id}"})


@app.route('/slow')
def slow_endpoint():
    """Simulate slow request - generates WARNING log."""
    delay = random.uniform(1, 3)
    logger.warning(f"Slow operation starting, expected delay: {delay:.2f}s")
    time.sleep(delay)
    logger.warning(f"Slow operation completed after {delay:.2f}s")
    return json.dumps({"message": "slow operation complete", "delay": delay})


@app.route('/error')
def error_endpoint():
    """Simulate error - generates ERROR log with stack trace."""
    try:
        # Intentionally cause an error
        result = 1 / 0
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)}), 500


@app.route('/random')
def random_endpoint():
    """Generate random log levels for testing."""
    level = random.choice(['info', 'warning', 'error'])

    if level == 'info':
        logger.info("Random INFO log generated")
    elif level == 'warning':
        logger.warning("Random WARNING log generated")
    else:
        logger.error("Random ERROR log generated")

    return json.dumps({"level": level, "app": APP_NAME})


@app.route('/generate')
def generate_logs():
    """Generate multiple log entries for testing."""
    count = int(request.args.get('count', 10))

    for i in range(count):
        level = random.choice(['info', 'info', 'info', 'warning', 'error'])
        if level == 'info':
            logger.info(f"Generated log {i+1}/{count}")
        elif level == 'warning':
            logger.warning(f"Generated warning {i+1}/{count}")
        else:
            logger.error(f"Generated error {i+1}/{count}")

    return json.dumps({"generated": count, "app": APP_NAME})


if __name__ == '__main__':
    logger.info(f"Starting {APP_NAME}...")
    app.run(host='0.0.0.0', port=5000)
