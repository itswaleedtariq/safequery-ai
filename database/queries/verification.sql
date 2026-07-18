-- ============================================================
-- 1. TABLE COUNTS
-- ============================================================

SELECT 'categories' AS table_name, COUNT(*) AS row_count
FROM categories

UNION ALL

SELECT 'customers', COUNT(*)
FROM customers

UNION ALL

SELECT 'products', COUNT(*)
FROM products

UNION ALL

SELECT 'orders', COUNT(*)
FROM orders

UNION ALL

SELECT 'order_items', COUNT(*)
FROM order_items

UNION ALL

SELECT 'payments', COUNT(*)
FROM payments;


-- ============================================================
-- 2. TOP FIVE PRODUCTS BY REVENUE
-- ============================================================

SELECT
    products.id,
    products.name,
    ROUND(
        SUM(order_items.line_total),
        2
    ) AS revenue

FROM products

JOIN order_items
    ON order_items.product_id = products.id

JOIN orders
    ON orders.id = order_items.order_id

WHERE orders.status IN ('completed', 'shipped')

GROUP BY
    products.id,
    products.name

ORDER BY revenue DESC

LIMIT 5;


-- ============================================================
-- 3. REVENUE BY SHIPPING CITY
-- ============================================================

SELECT
    orders.shipping_city,

    ROUND(
        SUM(order_items.line_total),
        2
    ) AS revenue

FROM orders

JOIN order_items
    ON order_items.order_id = orders.id

WHERE orders.status IN ('completed', 'shipped')

GROUP BY orders.shipping_city

ORDER BY revenue DESC;


-- ============================================================
-- 4. AVERAGE ORDER VALUE BY CUSTOMER CITY
-- ============================================================

SELECT
    customers.city,

    ROUND(
        AVG(orders.total_amount),
        2
    ) AS average_order_value

FROM customers

JOIN orders
    ON orders.customer_id = customers.id

WHERE orders.status IN ('completed', 'shipped')

GROUP BY customers.city

ORDER BY average_order_value DESC;


-- ============================================================
-- 5. ORDER STATUS DISTRIBUTION
-- ============================================================

SELECT
    status,
    COUNT(*) AS order_count

FROM orders

GROUP BY status

ORDER BY order_count DESC;


-- ============================================================
-- 6. CATEGORY REVENUE
-- ============================================================

SELECT
    categories.name AS category_name,

    ROUND(
        SUM(order_items.line_total),
        2
    ) AS revenue

FROM categories

JOIN products
    ON products.category_id = categories.id

JOIN order_items
    ON order_items.product_id = products.id

JOIN orders
    ON orders.id = order_items.order_id

WHERE orders.status IN ('completed', 'shipped')

GROUP BY categories.id, categories.name

ORDER BY revenue DESC;