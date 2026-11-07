
import os
import json
import psycopg2

def lambda_handler(event, context):
    for record in event["Records"]:
        order = json.loads(record["body"])

        order_id = order["order_id"]
        product_id = order["product_id"]
        quantity = order["quantity"]

        # Connect to PostgreSQL
        with psycopg2.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            sslmode="require"
        ) as db:
            with db.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO orders (order_id, product_id, quantity)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (order_id) DO NOTHING
                    RETURNING order_id
                    """,
                    (order_id, product_id, quantity)
                )

                inserted = cursor.fetchone()

        if inserted:
            print(f"NEW ORDER: {order_id}")
        else:
            print(f"DUPLICATE SKIPPED: {order_id}")

    return {"statusCode": 200}

