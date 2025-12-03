from flask import Flask, jsonify
import redis
import pymysql
import time
import os
import json

app = Flask(__name__)

redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=6379, decode_responses=True)

# Counters to track database vs cache hits
stats = {
    'db_hits': 0,
    'cache_hits': 0
}

def get_db():
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user='user',
        password='pass',
        database='testdb',
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    time.sleep(10)
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                price DECIMAL(10,2),
                category VARCHAR(50),
                description TEXT
            )
        ''')
        cur.execute('SELECT COUNT(*) as cnt FROM products')
        if cur.fetchone()['cnt'] == 0:
            for i in range(100):
                values = ','.join([f"('Product {i*100+j}', {10+j*0.5}, 'Category {j%10}', 'Description for product {i*100+j}')" for j in range(100)])
                cur.execute(f"INSERT INTO products (name, price, category, description) VALUES {values}")

        # Customers table for TTL demo
        cur.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100),
                points INT DEFAULT 0
            )
        ''')
        cur.execute('SELECT COUNT(*) as cnt FROM customers')
        if cur.fetchone()['cnt'] == 0:
            cur.execute("INSERT INTO customers (name, email, points) VALUES ('Alice', 'alice@test.com', 100)")
            cur.execute("INSERT INTO customers (name, email, points) VALUES ('Bob', 'bob@test.com', 200)")
        conn.commit()
    conn.close()

def query_from_db():
    """Execute database query and increment counter"""
    stats['db_hits'] += 1
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('''
            SELECT category, COUNT(*) as count, AVG(price) as avg_price, MAX(price) as max_price
            FROM products
            GROUP BY category
            ORDER BY avg_price DESC
        ''')
        result = cur.fetchall()
    conn.close()
    # Convert Decimal to float for JSON
    for row in result:
        row['avg_price'] = float(row['avg_price'])
        row['max_price'] = float(row['max_price'])
    return result


@app.route('/products')
def products_with_cache():
    """
    Get products with Redis caching.
    Demonstrates: Cache reduces database load by serving repeated requests from memory.
    """
    cache_key = 'products:stats'
    cached = redis_client.get(cache_key)

    if cached:
        stats['cache_hits'] += 1
        return jsonify({
            'data': json.loads(cached),
            'source': 'CACHE (Redis)',
            'message': 'Data served from Redis - no database query needed',
            'db_hits_total': stats['db_hits'],
            'cache_hits_total': stats['cache_hits']
        })

    # Cache miss - must query database
    result = query_from_db()
    redis_client.setex(cache_key, 60, json.dumps(result))  # Cache for 60 seconds

    return jsonify({
        'data': result,
        'source': 'DATABASE (MySQL)',
        'message': 'Cache miss - data fetched from database and cached',
        'db_hits_total': stats['db_hits'],
        'cache_hits_total': stats['cache_hits']
    })


@app.route('/products/no-cache')
def products_no_cache():
    """
    Get products WITHOUT caching.
    Demonstrates: Every request hits the database.
    """
    result = query_from_db()
    return jsonify({
        'data': result,
        'source': 'DATABASE (MySQL)',
        'message': 'No caching - database queried directly',
        'db_hits_total': stats['db_hits'],
        'cache_hits_total': stats['cache_hits']
    })


CUSTOMER_CACHE_TTL = 10  # Short TTL for demo (10 seconds)

@app.route('/customers')
def get_customers():
    """
    Get customers with TTL-based caching.
    Cache expires after 10 seconds - then fresh data is fetched.
    """
    cache_key = 'customers:all'
    cached = redis_client.get(cache_key)
    ttl = redis_client.ttl(cache_key)

    if cached:
        stats['cache_hits'] += 1
        return jsonify({
            'data': json.loads(cached),
            'source': 'CACHE',
            'ttl_remaining': ttl,
            'message': f'From cache. Expires in {ttl}s. Update now and see stale data!'
        })

    # Cache miss - query DB
    stats['db_hits'] += 1
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM customers')
        result = cur.fetchall()
    conn.close()

    redis_client.setex(cache_key, CUSTOMER_CACHE_TTL, json.dumps(result))
    return jsonify({
        'data': result,
        'source': 'DATABASE',
        'ttl_remaining': CUSTOMER_CACHE_TTL,
        'message': 'Fresh from DB and cached for 10s'
    })


@app.route('/customers/<int:customer_id>/add-points')
def add_points(customer_id):
    """
    Add points to customer - demonstrates stale cache problem.
    Data is updated in DB but cache still shows old value until TTL expires!
    """
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('UPDATE customers SET points = points + 50 WHERE id = %s', (customer_id,))
        conn.commit()
        cur.execute('SELECT * FROM customers WHERE id = %s', (customer_id,))
        customer = cur.fetchone()
    conn.close()

    ttl = redis_client.ttl('customers:all')
    return jsonify({
        'updated': customer,
        'cache_invalidated': False,
        'cache_ttl_remaining': ttl if ttl > 0 else 'expired',
        'message': f'DB updated! But /customers will show OLD data for {ttl}s until cache expires'
    })


@app.route('/customers/<int:customer_id>/add-points-invalidate')
def add_points_with_invalidation(customer_id):
    """
    Add points AND invalidate cache - proper way to handle updates.
    """
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('UPDATE customers SET points = points + 50 WHERE id = %s', (customer_id,))
        conn.commit()
        cur.execute('SELECT * FROM customers WHERE id = %s', (customer_id,))
        customer = cur.fetchone()
    conn.close()

    # Invalidate cache so next read gets fresh data
    redis_client.delete('customers:all')

    return jsonify({
        'updated': customer,
        'cache_invalidated': True,
        'message': 'DB updated AND cache invalidated. /customers will show fresh data immediately!'
    })


@app.route('/stats')
def get_stats():
    """
    Show cache effectiveness statistics.
    This is the KEY metric: how many DB queries were avoided?
    """
    total_requests = stats['db_hits'] + stats['cache_hits']
    cache_hit_rate = (stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0

    return jsonify({
        'total_requests': total_requests,
        'db_hits': stats['db_hits'],
        'cache_hits': stats['cache_hits'],
        'cache_hit_rate': f"{cache_hit_rate:.1f}%",
        'db_queries_avoided': stats['cache_hits'],
        'message': f"Redis cache prevented {stats['cache_hits']} database queries!"
    })


@app.route('/stats/reset')
def reset_stats():
    """Reset statistics counters and clear all caches"""
    stats['db_hits'] = 0
    stats['cache_hits'] = 0
    redis_client.delete('products:stats')
    redis_client.delete('customers:all')
    return jsonify({'status': 'Stats and cache reset', 'db_hits': 0, 'cache_hits': 0})


@app.route('/')
def index():
    """API documentation"""
    return jsonify({
        'lab': 'Redis Cache - Reduce Database Load',
        'demos': {
            'demo1_reduce_db_load': {
                'endpoints': {
                    '/products': 'Get products WITH caching',
                    '/products/no-cache': 'Get products WITHOUT caching',
                },
                'try_this': [
                    '1. /stats/reset',
                    '2. /products (10 times)',
                    '3. /stats → see 1 db_hit, 9 cache_hits'
                ]
            },
            'demo2_cache_invalidation': {
                'endpoints': {
                    '/customers': 'Get customers (cached 10s TTL)',
                    '/customers/1/add-points': 'Update WITHOUT invalidation (stale data!)',
                    '/customers/1/add-points-invalidate': 'Update WITH invalidation (fresh data)'
                },
                'try_this': [
                    '1. /customers → see points value',
                    '2. /customers/1/add-points → adds 50 points',
                    '3. /customers → STILL shows old points (stale cache!)',
                    '4. Wait 10s or call /customers/1/add-points-invalidate',
                    '5. /customers → now shows updated points'
                ]
            }
        },
        'stats': {
            '/stats': 'View db_hits vs cache_hits',
            '/stats/reset': 'Reset all stats and clear cache'
        }
    })


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
