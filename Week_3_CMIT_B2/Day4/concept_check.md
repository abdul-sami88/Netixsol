# Concept Check

## 1. Why are multiple CTEs preferred over one large nested query?

Multiple CTEs make a query easier to read, understand, and debug. Each CTE performs one specific task, making the query more organized and easier to modify.

Example:

```sql
WITH dept_avg AS (
    SELECT department, AVG(salary) AS avg_salary
    FROM employees
    GROUP BY department
),
high_paid AS (
    SELECT e.*
    FROM employees e
    JOIN dept_avg d
        ON e.department = d.department
    WHERE e.salary > d.avg_salary
)
SELECT * FROM high_paid;
```

---

## 2. When would you use a window function instead of GROUP BY?

Use a window function when you want to perform calculations while keeping all the original rows. Use `GROUP BY` when you want one row for each group.

Example using GROUP BY:

```sql
SELECT department, AVG(salary)
FROM employees
GROUP BY department;
```

Example using a window function:

```sql
SELECT
    name,
    department,
    salary,
    AVG(salary) OVER(PARTITION BY department) AS dept_avg
FROM employees;
```

---

## 3. Explain the difference between ROW_NUMBER(), RANK(), and DENSE_RANK().

- `ROW_NUMBER()` gives every row a unique number.
- `RANK()` gives the same rank to tied rows but skips the next rank.
- `DENSE_RANK()` gives the same rank to tied rows without skipping any ranks.

Example:

```sql
SELECT
    name,
    salary,
    ROW_NUMBER() OVER(ORDER BY salary DESC) AS row_num,
    RANK() OVER(ORDER BY salary DESC) AS rank_num,
    DENSE_RANK() OVER(ORDER BY salary DESC) AS dense_rank
FROM employees;
```

---

## 4. What is conditional aggregation?

Conditional aggregation uses `CASE WHEN` with aggregate functions such as `SUM()` or `COUNT()` to calculate values based on a condition.

Example:

```sql
SELECT
    SUM(CASE WHEN department = 'IT' THEN 1 ELSE 0 END) AS it_count,
    SUM(CASE WHEN department = 'HR' THEN 1 ELSE 0 END) AS hr_count
FROM employees;
```

---

## 5. How does CASE WHEN improve analytical reporting?

`CASE WHEN` helps classify data into categories, making reports easier to understand and analyze.

Example:

```sql
SELECT
    name,
    salary,
    CASE
        WHEN salary >= 60000 THEN 'High'
        WHEN salary >= 50000 THEN 'Medium'
        ELSE 'Low'
    END AS salary_level
FROM employees;
```

---

## 6. Why should SQL queries be broken into logical stages?

Breaking queries into logical stages makes them easier to read, test, debug, and maintain. Using CTEs allows each step to focus on one task.

Example:

```sql
WITH filtered_emp AS (
    SELECT *
    FROM employees
    WHERE age > 25
),
ranked_emp AS (
    SELECT *,
           ROW_NUMBER() OVER(ORDER BY salary DESC) AS rn
    FROM filtered_emp
)
SELECT *
FROM ranked_emp
WHERE rn <= 3;
```

---

## 7. What makes a SQL query maintainable?

A maintainable SQL query is well-organized, properly formatted, uses meaningful aliases, avoids repeated code, and is easy for others to understand and modify using CTE's, window functions and conditional aggregation for reports.  

Example:

```sql
WITH dept_avg AS (
    SELECT
        department,
        AVG(salary) AS avg_salary
    FROM employees
    GROUP BY department
)

SELECT
    e.name,
    e.department,
    e.salary,
    d.avg_salary
FROM employees e
JOIN dept_avg d
    ON e.department = d.department;
```
