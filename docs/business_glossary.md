# SafeQuery AI Business Glossary

## Revenue

Revenue is calculated as the sum of `order_items.line_total` for
orders whose status is either `completed` or `shipped`.

Pending and cancelled orders are excluded from revenue.

## Order value

Order value is stored in `orders.total_amount`.

It is calculated as the sum of all related
`order_items.line_total` values.

## Customer city

A customer's home city is stored in `customers.city`.

## Shipping city

The destination city of an order is stored in
`orders.shipping_city`.

Customer city and shipping city are not always the same.

## Successful payment

A successful payment has:

`payments.status = 'completed'`

## Active product

A currently available catalog product has:

`products.active = true`

## Historical product price

`products.price` is the current catalog price.

`order_items.unit_price` is the price at the time the order
was placed. Sales and revenue calculations should use
`order_items.unit_price`.