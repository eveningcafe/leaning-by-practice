from flask import Flask, jsonify
import redis
import pymysql
import time
import os
import json

app = Flask(__name__)

redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=6379, decode_responses=True)

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
            # Insert 10000 rows
            for i in range(100):
                values = ','.join([f"('Product {i*100+j}', {10+j*0.5}, 'Category {j%10}', 'Description for product {i*100+j}')" for j in range(100)])
                cur.execute(f"INSERT INTO products (name, price, category, description) VALUES {values}")
        conn.commit()
    conn.close()

@app.route('/products/no-cache')
def products_no_cache():
    start = time.time()
    conn = get_db()
    with conn.cursor() as cur:
        # Complex query: aggregation + sorting
        cur.execute('''
            SELECT category, COUNT(*) as count, AVG(price) as avg_price, MAX(price) as max_price
            FROM products
            GROUP BY category
            ORDER BY avg_price DESC
        ''')
        result = cur.fetchall()
    conn.close()
    return jsonify({
        'data': result,
        'source': 'database',
        'time_ms': round((time.time() - start) * 1000, 2)
    })

@app.route('/products/cached')
def products_cached():
    start = time.time()
    cached = redis_client.get('products_cache')

    if cached:
        return jsonify({
            'data': json.loads(cached),
            'source': 'redis_cache',
            'time_ms': round((time.time() - start) * 1000, 2)
        })

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

    redis_client.setex('products_cache', 60, json.dumps(result))
    return jsonify({
        'data': result,
        'source': 'database',
        'time_ms': round((time.time() - start) * 1000, 2)
    })

@app.route('/clear-cache')
def clear_cache():
    redis_client.delete('products_cache')
    return jsonify({'status': 'cache cleared'})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
