# Concept Check Questions

## 1. Why do relational databases split data into multiple tables?

Relational databases split data into multiple tables to reduce duplication, improve organization, and maintain consistency. Instead of storing the same information repeatedly, related data is stored once and connected using keys.

## 2. Difference between INNER JOIN and LEFT JOIN

INNER JOIN

- Returns only the matching records from both tables.
- Rows without a match are excluded.

LEFT JOIN

- Returns all rows from the left table and the matching rows from the right table.
- If there is no match, the right-side columns contain NULL.

## 3. When would you use a FULL OUTER JOIN?

A FULL OUTER JOIN is used when you want all records from both tables, whether they match or not.
This is useful for comparing two datasets and finding missing records on either side.

Example:

- Comparing customers with orders.
- Finding customers without orders and orders without valid customers.

## 4. Why are Primary Keys and Foreign Keys important?

Primary Key

- Uniquely identifies each row in a table.
- Prevents duplicate records.
- Cannot contain duplicate values or NULL.

Foreign Key

- Connects one table to another by referencing a Primary Key.
- Maintains relationships between tables.
- Helps ensure data integrity by preventing invalid references.

Together, they keep the database organized and consistent.

## 5. Explain normalization in simple words

Normalization is the process of organizing a database to remove duplicate data and store information efficiently. Instead of repeating the same information in multiple places, it is stored once and linked using keys.

Example:

Instead of writing the customer's name in every order:

| OrderID | Customer Name |
| ------- | ------------- |
| 101     | John          |
| 102     | John          |
| 103     | John          |

Store it like this:

Customers

| CustomerID | Name |
| ---------- | ---- |
| 1          | John |

Orders

| OrderID | CustomerID |
| ------- | ---------- |
| 101     | 1          |
| 102     | 1          |
| 103     | 1          |

This saves space and makes updates much easier.

## 6. What is an ER Diagram?

An Entity-Relationship (ER) Diagram is a visual representation of a database.

It shows:

- Entities (tables)
- Attributes (columns)
- Relationships between tables

It helps database designers understand how different tables are connected before creating the database.

## 7. What happens if a JOIN condition is incorrect?

If the JOIN condition is incorrect, the query may produce incorrect or misleading results.

Possible problems include:

- Missing records
- Duplicate records
- Completely unrelated rows being matched
- A Cartesian product (every row in one table matched with every row in another), resulting in an extremely large dataset

Example:

Incorrect JOIN:

```sql
SELECT *
FROM customers c
JOIN orders o
ON c.customer_id = o.order_id;
```

Since customer_id and order_id represent different things, the results will be incorrect or mostly empty.
