BEGIN;

-- ============================================================
-- SAFEQUERY AI E-COMMERCE DATABASE SCHEMA
-- ============================================================

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL DEFAULT 'Pakistan',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL,
    name VARCHAR(200) NOT NULL,
    sku VARCHAR(50) NOT NULL UNIQUE,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    stock_quantity INTEGER NOT NULL DEFAULT 0
        CHECK (stock_quantity >= 0),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_products_category
        FOREIGN KEY (category_id)
        REFERENCES categories(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    status VARCHAR(30) NOT NULL,
    shipping_city VARCHAR(100) NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0
        CHECK (total_amount >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_order_status
        CHECK (
            status IN (
                'pending',
                'shipped',
                'completed',
                'cancelled'
            )
        )
);

CREATE TABLE order_items (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),

    line_total NUMERIC(12, 2)
        GENERATED ALWAYS AS (quantity * unit_price) STORED,

    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id)
        REFERENCES orders(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_order_items_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE payments (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL UNIQUE,
    payment_date DATE NOT NULL,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount >= 0),
    method VARCHAR(30) NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_payments_order
        FOREIGN KEY (order_id)
        REFERENCES orders(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT chk_payment_method
        CHECK (
            method IN (
                'card',
                'bank_transfer',
                'cash_on_delivery',
                'digital_wallet'
            )
        ),

    CONSTRAINT chk_payment_status
        CHECK (
            status IN (
                'pending',
                'completed',
                'failed',
                'refunded'
            )
        )
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_products_category_id
    ON products(category_id);

CREATE INDEX idx_orders_customer_id
    ON orders(customer_id);

CREATE INDEX idx_orders_order_date
    ON orders(order_date);

CREATE INDEX idx_orders_status
    ON orders(status);

CREATE INDEX idx_order_items_order_id
    ON order_items(order_id);

CREATE INDEX idx_order_items_product_id
    ON order_items(product_id);

CREATE INDEX idx_payments_payment_date
    ON payments(payment_date);

CREATE INDEX idx_payments_status
    ON payments(status);

-- ============================================================
-- DESCRIPTIONS FOR FUTURE SCHEMA INTROSPECTION
-- ============================================================

COMMENT ON TABLE categories IS
    'Product categories used to organize the product catalog.';

COMMENT ON TABLE customers IS
    'Customers who can place ecommerce orders.';

COMMENT ON TABLE products IS
    'Products available in the ecommerce catalog.';

COMMENT ON TABLE orders IS
    'Customer orders and their current processing status.';

COMMENT ON TABLE order_items IS
    'Individual products and quantities included in an order.';

COMMENT ON TABLE payments IS
    'Payment attempt and payment status for each order.';

COMMENT ON COLUMN products.price IS
    'Current listed product price. Historical sale price is stored in order_items.unit_price.';

COMMENT ON COLUMN orders.total_amount IS
    'Sum of all order item line totals for this order.';

COMMENT ON COLUMN order_items.unit_price IS
    'Product price captured at the time the order was placed.';

COMMENT ON COLUMN order_items.line_total IS
    'Quantity multiplied by unit price.';

COMMENT ON COLUMN customers.city IS
    'Customer home city.';

COMMENT ON COLUMN orders.shipping_city IS
    'City to which the order was shipped.';

COMMIT;