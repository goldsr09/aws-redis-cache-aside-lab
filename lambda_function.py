
import os
import json
import redis
import psycopg2

# Environment variables configured in AWS Lambda
REDIS_HOST = os.environ["REDIS_HOST"]
DB_HOST = os.environ["DB_HOST"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]


# Redis connection
cache = redis.Redis(
    host=REDIS_HOST,
    port=6379,
    ssl=True,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5
)


# PostgreSQL connection
def connect_db():
    return psycopg2.connect(
        host=DB_HOST,
        port=5432,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode="require",
        connect_timeout=5
    )


# AWS Lambda entry point
def lambda_handler(event, context):

    # 1. Extract product ID from API Gateway URL
    try:
        product_id = int(
            (event.get("pathParameters") or {}).get(
                "product_id",
                event.get("product_id", 3)
            )
        )
    except (ValueError, TypeError):
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid product ID"})
        }

    key = f"product:{product_id}"

    # 2. Check Redis first
    cached = cache.get(key)

    if cached is not None:
        print("CACHE HIT")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "product": cached,
                "source": "redis"
            })
        }

    # 3. Cache miss: query PostgreSQL
    print("CACHE MISS")

    with connect_db() as db:
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM products WHERE id = %s",
                (product_id,)
            )
            row = cursor.fetchone()

    # 4. Product doesn't exist
    if row is None:
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Product not found"
            })
        }

    # 5. Store PostgreSQL result in Redis
    product_name = row[0]

    cache.set(
        key,
        product_name,
        ex=60
    )

    # 6. Return result
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "product": product_name,
            "source": "postgresql"
        })
    }
