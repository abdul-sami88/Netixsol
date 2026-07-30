# Concept Check Answers

## 1. What is the difference between WHERE and HAVING?

WHERE filters rows before grouping happens.
HAVING filters groups after GROUP BY and can use aggregate functions.

Example:

SELECT customer_id, SUM(amount)
FROM payment
GROUP BY customer_id
HAVING SUM(amount) > 100;

--------------------------------------------------

## 2. When would you use a correlated subquery instead of a JOIN?

Use a correlated subquery when the inner query depends on the current row of the outer query.

Example:
Find employees who earn more than the average salary of their own department.

SELECT employee_id, salary
FROM employees e
WHERE salary >
(
    SELECT AVG(salary)
    FROM employees
    WHERE department_id = e.department_id
);

--------------------------------------------------

## 3. What is a CTE, and why is it more readable than a nested subquery?

A CTE (Common Table Expression) is a temporary named result set created with WITH.

It is more readable because:

- It breaks large queries into smaller parts.
- It gives meaningful names to intermediate results.
- It is easier to debug and maintain.

It is like giving a variable name to query.

Example:

WITH customer_totals AS (
    SELECT customer_id, SUM(amount) AS total
    FROM payment
    GROUP BY customer_id
)

SELECT *
FROM customer_totals
WHERE total > 100;

--------------------------------------------------

## 4. Explain the difference between RANK() and DENSE_RANK()

RANK():
If there is a tie, the next rank is skipped.

Scores:
100 -> Rank 1
95  -> Rank 2
95  -> Rank 2
90  -> Rank 4

DENSE_RANK():
If there is a tie, no ranks are skipped.

Scores:
100 -> Rank 1
95  -> Rank 2
95  -> Rank 2
90  -> Rank 3

--------------------------------------------------

## 5. What does PARTITION BY do differently from GROUP BY?

GROUP BY combines rows into one row per group.

Example:

    SELECT department_id, AVG(salary)
    FROM employees
    GROUP BY department_id;

PARTITION BY keeps all rows but performs calculations separately within each group for window functions.

Example:

    SELECT employee_name,
        department_id,
        salary,
        AVG(salary) OVER (PARTITION BY department_id) AS dept_avg
    FROM employees;

GROUP BY reduces rows.
PARTITION BY keeps all rows.

--------------------------------------------------

## 6. Can a subquery return multiple rows? What operator would you use in that case?

Yes, a subquery can return multiple rows.

In that case you usually use:

- IN
- ANY
- ALL

Example:

SELECT *
FROM customer
WHERE customer_id IN (
    SELECT customer_id
    FROM payment
    WHERE amount > 10
);

--------------------------------------------------

## 7. Give an example of when (CASE WHEN) is useful inside an aggregate function

CASE WHEN is useful for conditional aggregation.

Example:

SELECT
    SUM(CASE WHEN amount > 5 THEN amount ELSE 0 END) AS large_payments
FROM payment;

### This calculates the total amount only for payments greater than 5

OR

SELECT
    COUNT(CASE WHEN active = 1 THEN 1 END) AS active_customers,
    COUNT(CASE WHEN active = 0 THEN 1 END) AS inactive_customers
FROM customer;

### Count active and inactive customer
