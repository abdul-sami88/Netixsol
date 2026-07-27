# Superstore Sales SQL Analysis

## Overview

This project demonstrates the fundamentals of SQL using PostgreSQL and the Superstore Sales dataset. It covers database creation, table import, and basic SQL queries for data retrieval and analysis.

---

## Dataset

Name: Superstore Sales Dataset

Source:
<https://www.kaggle.com/datasets/vivek468/superstore-dataset-final>

File used:

- Sample - Superstore.csv

---

## Software Used

- PostgreSQL 18
- pgAdmin 4

---

## Setup Steps

### 1. Install PostgreSQL

Download and install PostgreSQL from:

<https://www.postgresql.org/download/>

During installation:

- Install PostgreSQL Server
- Install pgAdmin 4
- Install Command Line Tools
- (Optional) Install Stack Builder

---

### 2. Create a Database

Open pgAdmin.

Right-click Databases → Create → Database

Database Name:

week3_day1_SQL

---

### 3. Create the Table

Open Query Tool and execute:

```sql
CREATE TABLE superstore_sales (
    row_id INT,
    order_id VARCHAR(20),
    order_date DATE,
    ship_date DATE,
    ship_mode VARCHAR(50),
    customer_id VARCHAR(20),
    customer_name VARCHAR(100),
    segment VARCHAR(50),
    country VARCHAR(100),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    region VARCHAR(50),
    product_id VARCHAR(30),
    category VARCHAR(50),
    sub_category VARCHAR(50),
    product_name TEXT,
    sales NUMERIC(10,2),
    quantity INT,
    discount NUMERIC(4,2),
    profit NUMERIC(10,2)
);
```

---

### 4. Import the Dataset

- Right-click superstore_sales
- Select Import/Export Data
- Choose Import
- Select the CSV file
- Format: CSV
- Header: Enabled
- Delimiter: ,
- Quote: "
- Escape: "
- Encoding: Latin1 (or UTF8 if applicable)

Click OK.

---

### 5. Verify Import

Run:

```sql
SELECT COUNT(*)
FROM superstore_sales;
```

---

## Example SQL Queries

```sql
SELECT *
FROM superstore_sales
LIMIT 10;
```

```sql
SELECT DISTINCT category
FROM superstore_sales;
```

```sql
SELECT category,
       SUM(sales)
FROM superstore_sales
GROUP BY category;
```

---

## Repository Structure

```bash
├── README.md
├── concept_check.md
├── day1_sql_practice.sql
├── screenshots/
└── Sample - Superstore.csv
```

---

## Author

Abdul Sami
