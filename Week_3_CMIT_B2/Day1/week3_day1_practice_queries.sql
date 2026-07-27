SELECT COUNT(*)
FROM superstore_sales;

SELECT * 
FROM superstore_sales
LIMIT 10;

SELECT *
FROM information_schema.columns
WHERE table_name = 'superstore_sales';

SELECT
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'superstore_sales';

SELECT DISTINCT category
FROM superstore_sales;

SELECT *
FROM superstore_sales
WHERE sales > 500;

SELECT *
FROM superstore_sales
ORDER BY profit DESC;

SELECT sales AS total_sales
FROM superstore_sales;

SELECT SUM(sales)
FROM superstore_sales;

SELECT AVG(profit)
FROM superstore_sales;

SELECT MIN(discount)
FROM superstore_sales;

SELECT MAX(sales)
FROM superstore_sales;

SELECT
    region,
    AVG(profit)
FROM superstore_sales
GROUP BY region
ORDER BY AVG(profit) DESC;