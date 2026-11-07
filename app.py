import redis

cache = redis.Redis(
    host = "master.redis-lab-cache.l2qwjn.use1.cache.amazonaws.com",
    port=6379,
    ssl=True,
    decode_responses=True

)

print("Redis Connected:", cache.ping())

import psycopg2
import getpass

db_password = getpass.getpass("PostgreSQL password: ")

db = psycopg2.connect(
    host="redis-lab-db.cj40qiqco8wb.us-east-1.rds.amazonaws.com",
    port=5432,
    dbname="labdb",
    user="postgres",
    password=db_password,
    sslmode="require"
)

print("PostgreSQL connected:", db.closed == 0)


def get_product(product_id):
    key = f"product:{product_id}"

    #1 Check Redis first
    cached = cache.get(key)

    if cached is not None:
        print("Cache Hit")
        return cached

    # 2. Redis didn't have it — query PostgreSQL
    print("CACHE MISS")
    

    cursor = db.cursor()

    cursor.execute(
        "SELECT name FROM products WHERE id = %s",
        (product_id,)
    )

    row = cursor.fetchone()
    cursor.close()

    if row is None:
        return None

    #3. Store the result in redis for 60 seconds

    product_name = row[0]

    cache.set(key,product_name,ex=60)

    return product_name


print(get_product(3))
print(get_product(3))