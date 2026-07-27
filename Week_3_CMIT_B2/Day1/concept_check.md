# Concept Check Questions

## 1. What problem does SQL solve that CSV files cannot?

CSV files simply store data and become slow or difficult to manage with millions of rows. SQL databases efficiently store, search, filter, and retrieve only the required data without loading the entire dataset into memory.

## 2. What is the difference between a database table and a spreadsheet?

A spreadsheet is mainly used for manual data entry, calculations, and small datasets. A database table stores structured data in a relational database, supports relationships between tables, handles millions of records efficiently, and can be queried using SQL.

## 3. What is a Primary Key?

A Primary Key is a unique column that identifies each record in a table. Its values cannot be duplicated or NULL.

## 4. What is a Foreign Key?

A Foreign Key is a column that references the Primary Key of another table, creating a relationship between the two tables.

## 5. Difference between WHERE and HAVING?

WHERE filters individual rows before grouping, while HAVING filters grouped or aggregated results after a GROUP BY.
Example:
-- Before grouping
WHERE sales > 100
-- After grouping
HAVING AVG(sales) > 200

## 6. Difference between ORDER BY and GROUP BY?

ORDER BY sorts the query results in ascending or descending order, while GROUP BY combines rows with the same values so aggregate functions like SUM() or AVG() can be calculated.

## 7. What does DISTINCT do?

It removes duplicate values and returns only unique values from a column.

## 8. When should you use LIMIT?

Use LIMIT when you only need a specific number of rows, such as previewing data or returning the top 10 results.

## 9. What are aggregate functions?

Aggregate functions perform calculations across multiple rows and return a single value. Common examples are COUNT(), SUM(), AVG(), MIN(), and MAX().

## 10. Why do Data Scientists prefer databases over Excel?

Databases can efficiently store and query millions of records, support multiple users, maintain data integrity through relationships, and retrieve only the required data. Excel is better suited for smaller datasets and manual analysis.
