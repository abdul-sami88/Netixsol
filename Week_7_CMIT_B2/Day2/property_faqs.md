# Pakistan Property Assistant — FAQ Dataset

## 1. Purpose

This document contains frequently asked questions that a user may ask about the `properties` PostgreSQL table.

The questions are designed around the fields available in the dataset:

- `property_id`
- `location_id`
- `page_url`
- `property_type`
- `price`
- `price_bin`
- `location`
- `city`
- `province_name`
- `locality`
- `latitude`
- `longitude`
- `baths`
- `area`
- `area_marla`
- `area_sqft`
- `purpose`
- `bedrooms`
- `date_added`
- `year`
- `month`
- `day`
- `agency`
- `agent`

The question categories are also aligned with common Pakistani property-search patterns. Zameen.com, for example, exposes filters for city, location, property type, area, beds and price, while other Pakistani property platforms also commonly use bathrooms, purpose and keywords. [Zameen](https://www.zameen.com/) and [Raabty](https://raabty.com/homesearch/sell_homes/) provide examples of these search patterns.

> **Important:** The exact numeric answers below must come from the PostgreSQL `properties` table. Since this document is created from the schema rather than the actual database contents, answer templates are provided where a database calculation is required. The chatbot should execute SQL against the table rather than inventing values.

---

# 2. Basic Property Questions

## Q1. How many properties are in the dataset?

**Answer:**  
There are **[COUNT] properties** in the dataset.

**SQL:**

```sql
SELECT COUNT(*) AS total_properties
FROM properties;
```

## Q2. What cities are available?

**Answer:**  
The dataset contains properties from **[LIST OF CITIES]**.

**SQL:**

```sql
SELECT DISTINCT city
FROM properties
WHERE city IS NOT NULL
ORDER BY city;
```

## Q3. What property types are available?

**Answer:**  
The available property types are **[PROPERTY TYPES]**.

**SQL:**

```sql
SELECT DISTINCT property_type
FROM properties
WHERE property_type IS NOT NULL
ORDER BY property_type;
```

## Q4. What provinces are represented?

**Answer:**  
The dataset contains properties from **[PROVINCES]**.

**SQL:**

```sql
SELECT DISTINCT province_name
FROM properties
WHERE province_name IS NOT NULL
ORDER BY province_name;
```

## Q5. What localities are available?

**Answer:**  
The dataset contains listings across **[NUMBER] localities**.

**SQL:**

```sql
SELECT COUNT(DISTINCT locality) AS locality_count
FROM properties
WHERE locality IS NOT NULL;
```

---

# 3. Price Questions

## Q6. What is the cheapest property?

**Answer:**  
The cheapest listed property costs **PKR [PRICE]**.

**SQL:**

```sql
SELECT property_id, property_type, city, locality, price
FROM properties
WHERE price IS NOT NULL
ORDER BY price ASC
LIMIT 1;
```

## Q7. What is the most expensive property?

**Answer:**  
The most expensive listed property costs **PKR [PRICE]**.

**SQL:**

```sql
SELECT property_id, property_type, city, locality, price
FROM properties
WHERE price IS NOT NULL
ORDER BY price DESC
LIMIT 1;
```

## Q8. What is the average property price?

**Answer:**  
The average listed property price is approximately **PKR [AVERAGE PRICE]**.

**SQL:**

```sql
SELECT ROUND(AVG(price), 2) AS average_price
FROM properties
WHERE price IS NOT NULL;
```

## Q9. What is the median property price?

**Answer:**  
The median listed property price is **PKR [MEDIAN PRICE]**.

**SQL:**

```sql
SELECT PERCENTILE_CONT(0.5)
       WITHIN GROUP (ORDER BY price) AS median_price
FROM properties
WHERE price IS NOT NULL;
```

## Q10. Which city has the highest average property price?

**Answer:**  
**[CITY]** has the highest average property price at approximately **PKR [PRICE]**.

**SQL:**

```sql
SELECT city, AVG(price) AS average_price
FROM properties
WHERE city IS NOT NULL
  AND price IS NOT NULL
GROUP BY city
ORDER BY average_price DESC
LIMIT 1;
```

## Q11. Which locality has the cheapest average property price?

**Answer:**  
**[LOCALITY]** has the lowest average listed property price at approximately **PKR [PRICE]**.

**SQL:**

```sql
SELECT locality, AVG(price) AS average_price
FROM properties
WHERE locality IS NOT NULL
  AND price IS NOT NULL
GROUP BY locality
ORDER BY average_price ASC
LIMIT 1;
```

## Q12. What properties are available under PKR 1 crore?

**Answer:**  
There are **[COUNT] properties** listed below PKR 1 crore.

**SQL:**

```sql
SELECT COUNT(*) AS property_count
FROM properties
WHERE price < 10000000;
```

---

# 4. Location Questions

## Q13. What properties are available in Lahore?

**Answer:**  
There are **[COUNT] properties** available in Lahore.

**SQL:**

```sql
SELECT COUNT(*) AS property_count
FROM properties
WHERE LOWER(city) = 'lahore';
```

## Q14. What properties are available in Karachi?

**Answer:**  
There are **[COUNT] properties** available in Karachi.

**SQL:**

```sql
SELECT COUNT(*) AS property_count
FROM properties
WHERE LOWER(city) = 'karachi';
```

## Q15. What properties are available in Islamabad?

**Answer:**  
There are **[COUNT] properties** available in Islamabad.

**SQL:**

```sql
SELECT COUNT(*) AS property_count
FROM properties
WHERE LOWER(city) = 'islamabad';
```

## Q16. Which city has the most property listings?

**Answer:**  
**[CITY]** has the largest number of listings, with **[COUNT] properties**.

**SQL:**

```sql
SELECT city, COUNT(*) AS property_count
FROM properties
WHERE city IS NOT NULL
GROUP BY city
ORDER BY property_count DESC
LIMIT 1;
```

## Q17. Which province has the most listings?

**Answer:**  
**[PROVINCE]** has the largest number of listings, with **[COUNT] properties**.

**SQL:**

```sql
SELECT province_name, COUNT(*) AS property_count
FROM properties
WHERE province_name IS NOT NULL
GROUP BY province_name
ORDER BY property_count DESC
LIMIT 1;
```

---

# 5. Bedrooms and Bathrooms

## Q18. Find properties with 3 bedrooms.

**Answer:**  
There are **[COUNT] properties** with 3 bedrooms.

**SQL:**

```sql
SELECT COUNT(*) AS property_count
FROM properties
WHERE bedrooms = 3;
```

## Q19. Find properties with at least 4 bedrooms.

**Answer:**  
There are **[COUNT] properties** with at least 4 bedrooms.

**SQL:**

```sql
SELECT COUNT(*) AS property_count
FROM properties
WHERE bedrooms >= 4;
```

## Q20. What is the average number of bedrooms?

**Answer:**  
The average property has approximately **[NUMBER] bedrooms**.

**SQL:**

```sql
SELECT ROUND(AVG(bedrooms), 2) AS average_bedrooms
FROM properties
WHERE bedrooms IS NOT NULL;
```

## Q21. What is the average number of bathrooms?

**Answer:**  
The average property has approximately **[NUMBER] bathrooms**.

**SQL:**

```sql
SELECT ROUND(AVG(baths), 2) AS average_baths
FROM properties
WHERE baths IS NOT NULL;
```

## Q22. Find properties with at least 3 bedrooms and 2 bathrooms.

**Answer:**  
There are **[COUNT] properties** meeting those requirements.

**SQL:**

```sql
SELECT COUNT(*) AS property_count
FROM properties
WHERE bedrooms >= 3
  AND baths >= 2;
```

---

# 6. Area Questions

## Q23. What is the average property size?

**Answer:**  
The average property size is approximately **[AREA] square feet**.

**SQL:**

```sql
SELECT ROUND(AVG(area_sqft), 2) AS average_area_sqft
FROM properties
WHERE area_sqft IS NOT NULL;
```

## Q24. What is the largest property?

**Answer:**  
The largest property has an area of approximately **[AREA] square feet**.

**SQL:**

```sql
SELECT property_id, city, locality, area_sqft
FROM properties
WHERE area_sqft IS NOT NULL
ORDER BY area_sqft DESC
LIMIT 1;
```

## Q25. Find properties larger than 10 marla.

**Answer:**  
There are **[COUNT] properties** larger than 10 marla.

**SQL:**

```sql
SELECT COUNT(*) AS property_count
FROM properties
WHERE area_marla > 10;
```

## Q26. Find properties between 5 and 10 marla.

**Answer:**  
There are **[COUNT] properties** between 5 and 10 marla.

**SQL:**

```sql
SELECT COUNT(*) AS property_count
FROM properties
WHERE area_marla BETWEEN 5 AND 10;
```

## Q27. What is the average price per square foot?

**Answer:**  
The average price per square foot is approximately **PKR [PRICE PER SQFT]**.

**SQL:**

```sql
SELECT ROUND(AVG(price / NULLIF(area_sqft, 0)), 2)
       AS average_price_per_sqft
FROM properties
WHERE price IS NOT NULL
  AND area_sqft IS NOT NULL
  AND area_sqft > 0;
```

---

# 7. Property Type Questions

## Q28. How many houses are available?

**Answer:**  
There are **[COUNT] house listings**.

**SQL:**

```sql
SELECT COUNT(*)
FROM properties
WHERE LOWER(property_type) = 'house';
```

## Q29. How many flats are available?

**Answer:**  
There are **[COUNT] flat listings**.

**SQL:**

```sql
SELECT COUNT(*)
FROM properties
WHERE LOWER(property_type) = 'flat';
```

## Q30. Which property type is most common?

**Answer:**  
**[PROPERTY TYPE]** is the most common property type, with **[COUNT] listings**.

**SQL:**

```sql
SELECT property_type, COUNT(*) AS property_count
FROM properties
WHERE property_type IS NOT NULL
GROUP BY property_type
ORDER BY property_count DESC
LIMIT 1;
```

## Q31. What is the average price of houses?

**Answer:**  
The average house price is approximately **PKR [PRICE]**.

**SQL:**

```sql
SELECT ROUND(AVG(price), 2) AS average_house_price
FROM properties
WHERE LOWER(property_type) = 'house'
  AND price IS NOT NULL;
```

---

# 8. Purpose Questions

## Q32. How many properties are for sale?

**Answer:**  
There are **[COUNT] properties** listed for sale.

**SQL:**

```sql
SELECT COUNT(*)
FROM properties
WHERE LOWER(purpose) = 'for sale';
```

## Q33. How many properties are for rent?

**Answer:**  
There are **[COUNT] properties** listed for rent.

**SQL:**

```sql
SELECT COUNT(*)
FROM properties
WHERE LOWER(purpose) = 'for rent';
```

## Q34. What purposes are available?

**Answer:**  
The dataset contains these purposes: **[PURPOSES]**.

**SQL:**

```sql
SELECT purpose, COUNT(*) AS property_count
FROM properties
WHERE purpose IS NOT NULL
GROUP BY purpose
ORDER BY property_count DESC;
```

---

# 9. Agency and Agent Questions

## Q35. Which agency has the most listings?

**Answer:**  
**[AGENCY]** has the most listings, with **[COUNT] properties**.

**SQL:**

```sql
SELECT agency, COUNT(*) AS property_count
FROM properties
WHERE agency IS NOT NULL
GROUP BY agency
ORDER BY property_count DESC
LIMIT 1;
```

## Q36. Which agent has listed the most properties?

**Answer:**  
**[AGENT]** has listed the most properties, with **[COUNT] listings**.

**SQL:**

```sql
SELECT agent, COUNT(*) AS property_count
FROM properties
WHERE agent IS NOT NULL
GROUP BY agent
ORDER BY property_count DESC
LIMIT 1;
```

## Q37. How many properties has a particular agency listed?

**Answer:**  
**[AGENCY]** has listed **[COUNT] properties**.

**SQL:**

```sql
SELECT COUNT(*) AS property_count
FROM properties
WHERE LOWER(agency) = LOWER('[AGENCY]');
```

## Q38. What properties were listed by a particular agent?

**Answer:**  
The agent has listed **[COUNT] properties**. Here are the matching listings: **[RESULTS]**.

**SQL:**

```sql
SELECT property_id, property_type, price, city, locality,
       bedrooms, baths, area_marla
FROM properties
WHERE LOWER(agent) = LOWER('[AGENT]')
ORDER BY date_added DESC;
```

---

# 10. Date and Trend Questions

## Q39. How many properties were added in 2024?

**Answer:**  
**[COUNT] properties** were added in 2024.

**SQL:**

```sql
SELECT COUNT(*)
FROM properties
WHERE year = 2024;
```

## Q40. Which year had the most listings?

**Answer:**  
**[YEAR]** had the most listings, with **[COUNT] properties**.

**SQL:**

```sql
SELECT year, COUNT(*) AS property_count
FROM properties
WHERE year IS NOT NULL
GROUP BY year
ORDER BY property_count DESC
LIMIT 1;
```

## Q41. Which month had the most listings?

**Answer:**  
**[MONTH]** had the most listings, with **[COUNT] properties**.

**SQL:**

```sql
SELECT month, COUNT(*) AS property_count
FROM properties
WHERE month IS NOT NULL
GROUP BY month
ORDER BY property_count DESC
LIMIT 1;
```

## Q42. Show the most recently added properties.

**Answer:**  
The most recently added properties are **[RESULTS]**.

**SQL:**

```sql
SELECT property_id, property_type, price, city,
       locality, bedrooms, baths, area_marla, date_added
FROM properties
WHERE date_added IS NOT NULL
ORDER BY date_added DESC
LIMIT 10;
```

---

# 11. Real-World Combined Questions

## Q43. Find me a 3-bedroom house in Lahore under PKR 2 crore.

**Answer:**  
I found **[COUNT] matching properties**.

**SQL:**

```sql
SELECT property_id, price, locality, bedrooms,
       baths, area_marla, page_url
FROM properties
WHERE LOWER(city) = 'lahore'
  AND LOWER(property_type) = 'house'
  AND bedrooms = 3
  AND price < 20000000
ORDER BY price ASC;
```

## Q44. Find 10-marla houses in Lahore under PKR 3 crore.

**Answer:**  
I found **[COUNT] matching properties**.

**SQL:**

```sql
SELECT property_id, price, locality, bedrooms,
       baths, area_marla, page_url
FROM properties
WHERE LOWER(city) = 'lahore'
  AND LOWER(property_type) = 'house'
  AND area_marla >= 10
  AND price < 30000000
ORDER BY price ASC;
```

## Q45. Find properties in Karachi with at least 3 bedrooms and 2 bathrooms.

**Answer:**  
I found **[COUNT] matching properties**.

**SQL:**

```sql
SELECT property_id, property_type, price, locality,
       bedrooms, baths, area_marla, page_url
FROM properties
WHERE LOWER(city) = 'karachi'
  AND bedrooms >= 3
  AND baths >= 2
ORDER BY price ASC;
```

## Q46. Find properties in Islamabad under PKR 5 crore.

**Answer:**  
I found **[COUNT] properties** in Islamabad below PKR 5 crore.

**SQL:**

```sql
SELECT property_id, property_type, price, locality,
       bedrooms, baths, area_marla, page_url
FROM properties
WHERE LOWER(city) = 'islamabad'
  AND price < 50000000
ORDER BY price ASC;
```

## Q47. Find a property with 3 bedrooms, 2 bathrooms, at least 5 marla, under PKR 2 crore in Lahore.

**Answer:**  
I found **[COUNT] properties** matching all of those requirements.

**SQL:**

```sql
SELECT property_id, property_type, price, locality,
       bedrooms, baths, area_marla, area_sqft, page_url
FROM properties
WHERE LOWER(city) = 'lahore'
  AND bedrooms >= 3
  AND baths >= 2
  AND area_marla >= 5
  AND price < 20000000
ORDER BY price ASC;
```

---

# 12. Ranking and Analytical Questions

## Q48. What are the top 5 cities by number of listings?

**Answer:**  
The top five cities are **[RESULTS]**.

**SQL:**

```sql
SELECT city, COUNT(*) AS property_count
FROM properties
WHERE city IS NOT NULL
GROUP BY city
ORDER BY property_count DESC
LIMIT 5;
```

## Q49. What are the top 10 localities by number of listings?

**Answer:**  
The top ten localities are **[RESULTS]**.

**SQL:**

```sql
SELECT locality, COUNT(*) AS property_count
FROM properties
WHERE locality IS NOT NULL
GROUP BY locality
ORDER BY property_count DESC
LIMIT 10;
```

## Q50. Which property type has the highest average price?

**Answer:**  
**[PROPERTY TYPE]** has the highest average price at approximately **PKR [PRICE]**.

**SQL:**

```sql
SELECT property_type, AVG(price) AS average_price
FROM properties
WHERE property_type IS NOT NULL
  AND price IS NOT NULL
GROUP BY property_type
ORDER BY average_price DESC
LIMIT 1;
```

---

# 13. Recommended Chatbot Behavior

The property assistant should:

1. Use PostgreSQL data for factual answers.
2. Never invent a property, price, locality, agent or agency.
3. Apply every filter mentioned by the user.
4. Explain when no matching property exists.
5. Ask for clarification when a request is ambiguous.
6. Treat prices as PKR unless the dataset specifies otherwise.
7. Distinguish between `for sale` and `for rent`.
8. Use `area_marla` for Marla-based questions.
9. Use `area_sqft` for square-foot questions.
10. Use `date_added` for date-based questions.
11. Use `year`, `month`, and `day` for aggregation when appropriate.
12. Return useful property identifiers such as `property_id` and `page_url` when showing individual listings.
13. Avoid exposing internal SQL unless the user asks for it.
14. If the requested information does not exist in the table, clearly say that the dataset does not contain the required information.

---

# 14. Example Natural-Language Responses

### User:
> Find me a 3-bedroom house in Lahore under 2 crore.

### Assistant:
> I found 8 properties matching your requirements. The cheapest option is PKR 1.55 crore, followed by PKR 1.68 crore and PKR 1.75 crore. I can show you the full list with location, area, bathrooms and listing links.

### User:
> Which city has the most properties?

### Assistant:
> Lahore has the most property listings in the dataset, with 12,450 properties.

> **Note:** The number above is an example. Your chatbot must calculate the actual number from PostgreSQL.

### User:
> What is the average property price in Lahore?

### Assistant:
> The average listed property price in Lahore is approximately PKR 2.85 crore.

> **Note:** This is also an example. The production chatbot should calculate the actual value from your database.

---

# 15. Evaluation Questions

For testing the chatbot, use a mixture of:

### Simple retrieval
- What cities are available?
- What property types are available?
- How many properties are in the database?

### Filtering
- Find 3-bedroom properties.
- Find properties under PKR 1 crore.
- Find properties larger than 10 marla.

### Multi-condition filtering
- Find 3-bedroom houses in Lahore under PKR 2 crore.
- Find properties in Karachi with at least 3 bedrooms and 2 bathrooms.
- Find 10-marla houses in Lahore under PKR 3 crore.

### Aggregation
- What is the average property price?
- What is the median property price?
- What is the average price per square foot?

### Grouping
- Which city has the most listings?
- Which locality has the highest average price?
- Which agency has the most listings?

### Ranking
- What are the top 5 cities by listings?
- What are the top 10 localities by listings?
- What are the 5 cheapest properties?

### Date analysis
- How many properties were added in 2024?
- Which year had the most listings?
- Which month had the most listings?
- Show the newest properties.

---

# 16. Sources Used for Question Design

The FAQ structure was informed by current Pakistani property-search interfaces and datasets:

- [Zameen.com](https://www.zameen.com/) — uses city, location, property type, area, bedrooms and price as major search filters.
- [Zameen Property Search](https://zameen.world/) — uses city, location, property type, price, area, beds and baths.
- [Raabty Property Search](https://raabty.com/homesearch/sell_homes/) — uses purpose, city, location, property type, area, price, beds, baths and keywords.
- [OG Landmark](https://oglandmark.com/search) — supports natural-language property search and filters including city, property type, purpose, price, area, bedrooms and bathrooms.
- [Kaggle — Pakistan/Zameen property dataset](https://www.kaggle.com/datasets/azharsaleem/explore-pakistans-property-landscape-zameen-com) — provides examples of structured property fields such as price, area, city, address, bedrooms, bathrooms, square feet, latitude, longitude and date added.

These sources support the choice of questions around **price, location, property type, purpose, area, bedrooms, bathrooms, dates and listing information**.

---

# 17. Important Note for the Project

This FAQ document is a **question-and-answer specification** for the property assistant, not a static database of verified numeric answers.

The best architecture for the chatbot is:

```text
User Question
      ↓
LLM / Intent Understanding
      ↓
SQL Generation
      ↓
PostgreSQL `properties`
      ↓
Query Result
      ↓
Natural Language Answer
```

This allows questions such as:

> "Show me 3-bedroom houses in Lahore under 2 crore"

to be converted into a SQL query and answered using your **real dataset**, rather than relying on hallucinated answers.
