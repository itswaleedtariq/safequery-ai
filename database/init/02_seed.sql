BEGIN;

-- ============================================================
-- CLEAR EXISTING DATA
-- ============================================================

TRUNCATE TABLE
    payments,
    order_items,
    orders,
    products,
    customers,
    categories
RESTART IDENTITY CASCADE;

-- ============================================================
-- CATEGORIES: 8 RECORDS
-- ============================================================

INSERT INTO categories (name, description)
VALUES
    ('Electronics', 'Computers, mobile devices and electronic accessories.'),
    ('Clothing', 'Men and women clothing products.'),
    ('Home and Kitchen', 'Furniture, appliances and kitchen products.'),
    ('Books', 'Technical, academic and general reading books.'),
    ('Sports', 'Sports, fitness and outdoor equipment.'),
    ('Beauty', 'Personal care, beauty and grooming products.'),
    ('Office', 'Office supplies and workplace equipment.'),
    ('Gaming', 'Gaming hardware, accessories and merchandise.');

-- ============================================================
-- PRODUCTS: 100 RECORDS
-- ============================================================

INSERT INTO products (
    category_id,
    name,
    sku,
    price,
    stock_quantity,
    active
)
SELECT
    ((series_number - 1) % 8) + 1 AS category_id,

    category.name
        || ' Item '
        || LPAD(series_number::TEXT, 3, '0') AS product_name,

    'SKU-'
        || LPAD(series_number::TEXT, 5, '0') AS sku,

    ROUND(
        (
            25
            + ((series_number * 17) % 475)
            + ((series_number % 10) * 0.95)
        )::NUMERIC,
        2
    ) AS price,

    20 + ((series_number * 11) % 180) AS stock_quantity,

    CASE
        WHEN series_number % 25 = 0 THEN FALSE
        ELSE TRUE
    END AS active

FROM generate_series(1, 100) AS generated(series_number)

JOIN categories AS category
    ON category.id = ((series_number - 1) % 8) + 1;

-- ============================================================
-- CUSTOMERS: 500 RECORDS
-- ============================================================

INSERT INTO customers (
    full_name,
    email,
    city,
    country,
    created_at
)
SELECT
    'Customer '
        || LPAD(series_number::TEXT, 4, '0'),

    'customer'
        || series_number
        || '@safequery-demo.com',

    (
        ARRAY[
            'Karachi',
            'Lahore',
            'Islamabad',
            'Rawalpindi',
            'Peshawar',
            'Quetta',
            'Multan',
            'Faisalabad',
            'Sialkot',
            'Hyderabad'
        ]
    )[1 + ((series_number - 1) % 10)],

    'Pakistan',

    TIMESTAMPTZ '2024-01-01 09:00:00+00'
        + (series_number || ' hours')::INTERVAL

FROM generate_series(1, 500) AS generated(series_number);

-- ============================================================
-- ORDERS: 2,000 RECORDS
--
-- Fixed date anchor is used so evaluation results remain
-- reproducible across different computers and dates.
-- ============================================================

INSERT INTO orders (
    customer_id,
    order_date,
    status,
    shipping_city,
    total_amount
)
SELECT
    1 + ((series_number * 37) % 500) AS customer_id,

    DATE '2026-06-30'
        - ((series_number * 11) % 730)::INTEGER AS order_date,

    CASE
        WHEN series_number % 20 = 0 THEN 'cancelled'
        WHEN series_number % 11 = 0 THEN 'pending'
        WHEN series_number % 7 = 0 THEN 'shipped'
        ELSE 'completed'
    END AS status,

    (
        ARRAY[
            'Karachi',
            'Lahore',
            'Islamabad',
            'Rawalpindi',
            'Peshawar',
            'Quetta',
            'Multan',
            'Faisalabad',
            'Sialkot',
            'Hyderabad'
        ]
    )[1 + ((series_number * 3) % 10)] AS shipping_city,

    0

FROM generate_series(1, 2000) AS generated(series_number);

-- ============================================================
-- ORDER ITEMS: EXACTLY 4,000 RECORDS
-- Each order receives two order items.
-- ============================================================

WITH item_candidates AS (
    SELECT
        orders.id AS order_id,

        item_number,

        1 + (
            (
                orders.id * 7
                + item_number * 13
            ) % 100
        )::INTEGER AS product_id,

        1 + (
            (
                orders.id
                + item_number
            ) % 4
        )::INTEGER AS quantity

    FROM orders

    CROSS JOIN generate_series(1, 2)
        AS generated_items(item_number)
)

INSERT INTO order_items (
    order_id,
    product_id,
    quantity,
    unit_price
)
SELECT
    item_candidates.order_id,
    item_candidates.product_id,
    item_candidates.quantity,
    products.price

FROM item_candidates

JOIN products
    ON products.id = item_candidates.product_id;

-- ============================================================
-- CALCULATE ORDER TOTALS
-- ============================================================

UPDATE orders
SET total_amount = calculated_totals.order_total

FROM (
    SELECT
        order_id,
        SUM(line_total) AS order_total

    FROM order_items

    GROUP BY order_id
) AS calculated_totals

WHERE orders.id = calculated_totals.order_id;

-- ============================================================
-- PAYMENTS: 2,000 RECORDS
-- ============================================================

INSERT INTO payments (
    order_id,
    payment_date,
    amount,
    method,
    status
)
SELECT
    orders.id,

    orders.order_date
        + (orders.id % 4)::INTEGER,

    orders.total_amount,

    CASE
        WHEN orders.id % 4 = 0 THEN 'card'
        WHEN orders.id % 4 = 1 THEN 'bank_transfer'
        WHEN orders.id % 4 = 2 THEN 'cash_on_delivery'
        ELSE 'digital_wallet'
    END,

    CASE
        WHEN orders.status = 'cancelled' THEN 'refunded'
        WHEN orders.status = 'pending' THEN 'pending'
        WHEN orders.id % 17 = 0 THEN 'failed'
        ELSE 'completed'
    END

FROM orders;

-- Update PostgreSQL statistics after inserting data.
ANALYZE;

COMMIT;