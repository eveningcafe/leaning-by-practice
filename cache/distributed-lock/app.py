from flask import Flask, jsonify
import redis
import time
import os
import uuid
import threading

app = Flask(__name__)

redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=6379, decode_responses=True)
APP_NAME = os.getenv('APP_NAME', 'app')

# Simulated shared resource (e.g., inventory count)
INVENTORY_KEY = 'product:1:stock'

def init_inventory():
    """Initialize inventory to 100 units"""
    redis_client.set(INVENTORY_KEY, 100)

# Statistics keys in Redis (shared across all apps)
STATS_SUCCESS_KEY = 'stats:successful_purchases'
STATS_FAILED_KEY = 'stats:failed_purchases'


def acquire_lock(lock_name, timeout=10):
    """
    Acquire a distributed lock using Redis SET NX (Set if Not eXists).
    Returns lock_id if acquired, None otherwise.
    """
    lock_id = str(uuid.uuid4())
    lock_key = f'lock:{lock_name}'

    # SET NX with expiration - atomic operation
    # Only one process can acquire the lock
    acquired = redis_client.set(lock_key, lock_id, nx=True, ex=timeout)

    if acquired:
        return lock_id
    return None


def release_lock(lock_name, lock_id):
    """
    Release lock only if we own it (compare lock_id).
    Uses Lua script for atomic check-and-delete.
    """
    lock_key = f'lock:{lock_name}'

    # Lua script: only delete if value matches (we own the lock)
    lua_script = """
    if redis.call('get', KEYS[1]) == ARGV[1] then
        return redis.call('del', KEYS[1])
    else
        return 0
    end
    """
    result = redis_client.eval(lua_script, 1, lock_key, lock_id)
    return result == 1


@app.route('/buy/no-lock')
def buy_without_lock():
    """
    Purchase WITHOUT distributed lock - causes race conditions!
    Simulates: Read stock → Process payment → Write new stock (non-atomic)
    """
    # Step 1: Read current stock
    stock = int(redis_client.get(INVENTORY_KEY) or 0)

    if stock <= 0:
        redis_client.incr(STATS_FAILED_KEY)
        return jsonify({
            'status': 'failed',
            'reason': 'out of stock',
            'app': APP_NAME,
            'stock_before': stock
        }), 400

    # Step 2: Simulate processing (payment API, validation, etc.)
    # RACE CONDITION WINDOW: Other processes read the SAME stock value!
    time.sleep(0.1)

    # Step 3: Write back new stock (NOT atomic - uses SET instead of DECR)
    # This simulates real-world: read → compute → write back
    new_stock = stock - 1
    redis_client.set(INVENTORY_KEY, new_stock)

    redis_client.incr(STATS_SUCCESS_KEY)
    return jsonify({
        'status': 'success',
        'app': APP_NAME,
        'stock_before': stock,
        'stock_after': new_stock,
        'warning': 'No lock used - race conditions possible!'
    })


@app.route('/buy/with-lock')
def buy_with_lock():
    """
    Purchase WITH distributed lock - prevents race conditions!
    Only one app can process purchase at a time.
    """
    lock_name = 'purchase:product:1'

    # Try to acquire lock
    lock_id = acquire_lock(lock_name, timeout=10)

    if not lock_id:
        return jsonify({
            'status': 'busy',
            'reason': 'Another purchase in progress, please retry',
            'app': APP_NAME
        }), 503

    try:
        # CRITICAL SECTION - only one app can be here at a time
        stock = int(redis_client.get(INVENTORY_KEY) or 0)

        if stock <= 0:
            redis_client.incr(STATS_FAILED_KEY)
            return jsonify({
                'status': 'failed',
                'reason': 'out of stock',
                'app': APP_NAME,
                'stock_before': stock
            }), 400

        # Simulate processing time
        time.sleep(0.1)

        # Safely write - we have exclusive access (no one else can read/write)
        new_stock = stock - 1
        redis_client.set(INVENTORY_KEY, new_stock)
        redis_client.incr(STATS_SUCCESS_KEY)

        return jsonify({
            'status': 'success',
            'app': APP_NAME,
            'stock_before': stock,
            'stock_after': new_stock,
            'lock_used': True
        })

    finally:
        # ALWAYS release the lock
        release_lock(lock_name, lock_id)


@app.route('/buy/with-lock-retry')
def buy_with_lock_retry():
    """
    Purchase with lock + automatic retry logic.
    Will wait and retry if lock is held by another process.
    """
    lock_name = 'purchase:product:1'
    max_retries = 10
    retry_delay = 0.15

    for attempt in range(max_retries):
        lock_id = acquire_lock(lock_name, timeout=10)

        if lock_id:
            try:
                stock = int(redis_client.get(INVENTORY_KEY) or 0)

                if stock <= 0:
                    redis_client.incr(STATS_FAILED_KEY)
                    return jsonify({
                        'status': 'failed',
                        'reason': 'out of stock',
                        'app': APP_NAME,
                        'attempts': attempt + 1
                    }), 400

                time.sleep(0.1)  # Simulate processing
                new_stock = stock - 1
                redis_client.set(INVENTORY_KEY, new_stock)
                redis_client.incr(STATS_SUCCESS_KEY)

                return jsonify({
                    'status': 'success',
                    'app': APP_NAME,
                    'stock_before': stock,
                    'stock_after': new_stock,
                    'attempts': attempt + 1
                })

            finally:
                release_lock(lock_name, lock_id)

        # Lock not acquired, wait and retry
        time.sleep(retry_delay)

    return jsonify({
        'status': 'timeout',
        'reason': f'Could not acquire lock after {max_retries} attempts',
        'app': APP_NAME
    }), 503


@app.route('/stock')
def get_stock():
    """Get current stock level"""
    stock = redis_client.get(INVENTORY_KEY)
    return jsonify({
        'product_id': 1,
        'stock': int(stock) if stock else 0
    })


@app.route('/stock/reset')
def reset_stock():
    """Reset stock to 100 and clear stats"""
    redis_client.set(INVENTORY_KEY, 100)
    redis_client.delete('lock:purchase:product:1')
    redis_client.set(STATS_SUCCESS_KEY, 0)
    redis_client.set(STATS_FAILED_KEY, 0)
    return jsonify({
        'status': 'reset',
        'stock': 100
    })


@app.route('/stats')
def get_stats():
    """Get purchase statistics"""
    stock = int(redis_client.get(INVENTORY_KEY) or 0)
    successful = int(redis_client.get(STATS_SUCCESS_KEY) or 0)
    failed = int(redis_client.get(STATS_FAILED_KEY) or 0)
    expected_stock = 100 - successful
    return jsonify({
        'current_stock': stock,
        'successful_purchases': successful,
        'failed_purchases': failed,
        'expected_stock': expected_stock,
        'stock_matches_expected': stock == expected_stock
    })


@app.route('/')
def index():
    """API documentation"""
    return jsonify({
        'lab': 'Redis Distributed Lock - Prevent Race Conditions',
        'scenario': 'Multiple app instances trying to purchase same product',
        'endpoints': {
            '/buy/no-lock': 'Purchase WITHOUT lock (causes race conditions!)',
            '/buy/with-lock': 'Purchase WITH lock (safe, but may fail if busy)',
            '/buy/with-lock-retry': 'Purchase WITH lock + retry (safe + resilient)',
            '/stock': 'Check current stock',
            '/stock/reset': 'Reset stock to 100',
            '/stats': 'View purchase statistics'
        },
        'try_this': [
            '1. /stock/reset - Reset to 100 units',
            '2. Run concurrent requests to /buy/no-lock from multiple apps',
            '3. Check /stats - race_conditions_detected > 0 means overselling!',
            '4. /stock/reset again',
            '5. Run concurrent requests to /buy/with-lock',
            '6. Check /stats - no race conditions, stock is accurate'
        ],
        'app': APP_NAME
    })


if __name__ == '__main__':
    init_inventory()
    app.run(host='0.0.0.0', port=5000)
