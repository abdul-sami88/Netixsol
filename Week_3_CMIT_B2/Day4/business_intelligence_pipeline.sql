-- =============================================================================
-- Music Store — Business Intelligence Pipeline
-- =============================================================================
WITH
-- ==========================================================
-- Stage 1: Build Customer Spending Profile
-- ==========================================================
-- Aggregate invoice-level metrics for each customer.
invoice_metrics AS (
    SELECT
        customer_id,
        COUNT(invoice_id)                                        AS total_invoices,
        SUM(total)                                                AS total_spent,
        AVG(total)                                                AS avg_invoice_value,
        COUNT(DISTINCT TO_CHAR(invoice_date, 'YYYY-MM'))          AS purchase_months
    FROM invoice
    GROUP BY customer_id
),

-- Calculate purchasing diversity (genres, artists, tracks).
customer_purchase_metrics AS (
    SELECT
        i.customer_id,
        COUNT(il.track_id)              AS total_tracks_purchased,
        COUNT(DISTINCT t.genre_id)      AS unique_genres,
        COUNT(DISTINCT a.artist_id)     AS unique_artists
    FROM invoice i
    JOIN invoice_line il ON i.invoice_id = il.invoice_id
    JOIN track t        ON il.track_id  = t.track_id
    JOIN album al        ON t.album_id   = al.album_id
    JOIN artist a        ON al.artist_id = a.artist_id
    GROUP BY i.customer_id
),

-- Combine all customer KPIs into a reusable profile.
-- NOTE: inner-joining invoice_metrics/customer_purchase_metrics means a
-- customer with zero invoices (or invoices with no line items) will not
-- appear here. That's expected for a "spending profile" — a customer who
-- never purchased has nothing to profile.
customer_profile AS (
    SELECT
        c.customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        c.country,
        im.total_spent,
        im.total_invoices,
        cpm.total_tracks_purchased,
        cpm.unique_genres,
        cpm.unique_artists,
        im.purchase_months,
        ROUND(im.avg_invoice_value, 2) AS avg_invoice_value
    FROM customer c
    JOIN invoice_metrics im            ON c.customer_id = im.customer_id
    JOIN customer_purchase_metrics cpm ON c.customer_id = cpm.customer_id
),

-- ==========================================================
-- Stage 2: Customer Segmentation
-- ==========================================================
-- Classify customers using spending, purchase frequency,
-- and purchasing diversity. Any one qualifying condition per
-- tier is sufficient (OR), so a customer can earn Gold/Silver
-- through spend OR frequency OR diversity alone; Platinum
-- requires spend AND artist diversity together. See README for
-- the full rationale behind these thresholds.
customer_segments AS (
    SELECT
        *,
        CASE
            WHEN total_spent > 41 AND unique_artists >= 5 THEN 'Platinum'
            WHEN total_spent > 39 AND unique_genres  >= 4 THEN 'Gold'
            WHEN total_spent > 37 OR  unique_artists >= 4 THEN 'Silver'
            ELSE 'Bronze'
        END AS segment
    FROM customer_profile
),

-- ==========================================================
-- Stage 3: Personalized Marketing Recommendation
-- ==========================================================
-- Rank each customer's genres by tracks purchased (window function).
genre_counts AS (
    SELECT
        i.customer_id,
        g.name AS genre_name,
        COUNT(il.track_id) AS purchase_count,
        ROW_NUMBER() OVER (PARTITION BY i.customer_id ORDER BY COUNT(il.track_id) DESC) AS rn
    FROM invoice i
    JOIN invoice_line il ON i.invoice_id = il.invoice_id
    JOIN track t        ON il.track_id  = t.track_id
    JOIN genre g         ON t.genre_id   = g.genre_id
    GROUP BY i.customer_id, g.name
),

-- Keep only each customer's #1 genre.
favorite_genres AS (
    SELECT customer_id, genre_name AS favorite_genre
    FROM genre_counts
    WHERE rn = 1
),

-- Attach a promotional campaign per customer, driven by their segment
-- and their favorite genre.
customer_marketing AS (
    SELECT
        cs.customer_id,
        cs.customer_name,
        cs.country,
        cs.total_spent,
        cs.segment,
        fg.favorite_genre,
        CASE
            WHEN cs.segment = 'Platinum' THEN 'Early access to new releases in ' || fg.favorite_genre
            WHEN cs.segment = 'Gold'     THEN 'Exclusive Album Bundles in ' || fg.favorite_genre
            WHEN cs.segment = 'Silver'   THEN '15% Off all ' || fg.favorite_genre || ' Tracks'
            WHEN cs.segment = 'Bronze'   THEN 'First purchase coupon for ' || fg.favorite_genre
        END AS promotional_campaign
    FROM customer_segments cs
    JOIN favorite_genres fg ON cs.customer_id = fg.customer_id
),

-- ==========================================================
-- Stage 4: Country Expansion Strategy
-- ==========================================================
-- Roll customer_segments up to country-level business metrics.
country_metrics AS (
    SELECT
        country,
        SUM(total_spent)                                    AS total_revenue,
        COUNT(customer_id)                                  AS total_customers,
        ROUND(SUM(total_spent) / COUNT(customer_id), 2)     AS avg_revenue_per_customer,
        ROUND(AVG(avg_invoice_value), 2)                    AS average_invoice_value,
        ROUND(AVG(unique_genres), 2)                        AS avg_genres_purchased,
        COUNT(DISTINCT segment)                             AS customer_diversity
    FROM customer_segments
    GROUP BY country
),

-- Weighted scoring formula (weights sum to 100):
-- revenue 30, customer base 20, revenue/customer 20,
-- avg invoice value 10, genre breadth 10, segment diversity 10.
country_scoring AS (
    SELECT
        country,
        total_revenue,
        total_customers,
        avg_revenue_per_customer,
        average_invoice_value,
        avg_genres_purchased,
        customer_diversity,
        ROUND(
            (total_revenue            / MAX(total_revenue)            OVER() * 30) +
            (total_customers::numeric / MAX(total_customers)          OVER() * 20) +
            (avg_revenue_per_customer / MAX(avg_revenue_per_customer) OVER() * 20) +
            (average_invoice_value    / MAX(average_invoice_value)    OVER() * 10) +
            (avg_genres_purchased     / MAX(avg_genres_purchased)     OVER() * 10) +
            (customer_diversity::numeric / MAX(customer_diversity)    OVER() * 10)
        , 2) AS performance_score
    FROM country_metrics
),

-- Rank countries and compute each one's share of total revenue.
country_ranking AS (
    SELECT
        country,
        total_revenue,
        total_customers,
        avg_revenue_per_customer,
        average_invoice_value,
        avg_genres_purchased,
        customer_diversity,
        performance_score,
        ROUND((total_revenue / (SELECT SUM(total_spent) FROM customer_segments)) * 100, 2) AS revenue_contribution_pct,
        RANK() OVER (ORDER BY performance_score DESC) AS country_rank
    FROM country_scoring
),

-- ==========================================================
-- Stage 5: Executive SQL Report (final output)
-- ==========================================================
-- Top-spending customer within each segment.
top_customer_per_segment AS (
    SELECT segment, customer_name, favorite_genre, total_spent
    FROM (
        SELECT
            segment, customer_name, favorite_genre, total_spent,
            ROW_NUMBER() OVER (PARTITION BY segment ORDER BY total_spent DESC) AS rn
        FROM customer_marketing
    ) ranked
    WHERE rn = 1
),

-- Most-purchased genre within each segment.
segment_genre_counts AS (
    SELECT
        cs.segment,
        g.name AS genre_name,
        COUNT(il.track_id) AS purchase_count,
        ROW_NUMBER() OVER (PARTITION BY cs.segment ORDER BY COUNT(il.track_id) DESC) AS rn
    FROM customer_segments cs
    JOIN invoice i       ON cs.customer_id = i.customer_id
    JOIN invoice_line il ON i.invoice_id   = il.invoice_id
    JOIN track t         ON il.track_id    = t.track_id
    JOIN genre g          ON t.genre_id     = g.genre_id
    GROUP BY cs.segment, g.name
),
top_genre_per_segment AS (
    SELECT segment, genre_name
    FROM segment_genre_counts
    WHERE rn = 1
),

-- Customer count and revenue per segment.
segment_agg AS (
    SELECT
        segment,
        COUNT(customer_id)  AS total_customers,
        SUM(total_spent)    AS segment_revenue
    FROM customer_marketing
    GROUP BY segment
),

-- Top employee (support rep) by revenue generated.
employee_revenue AS (
    SELECT
        e.first_name || ' ' || e.last_name AS employee_name,
        SUM(i.total) AS total_revenue
    FROM employee e
    JOIN customer c ON e.employee_id = c.support_rep_id
    JOIN invoice i  ON c.customer_id = i.customer_id
    GROUP BY e.employee_id, e.first_name, e.last_name
    ORDER BY total_revenue DESC
    LIMIT 1
),

-- Top artist by revenue.
artist_revenue AS (
    SELECT
        a.name AS artist_name,
        SUM(il.unit_price * il.quantity) AS total_revenue
    FROM artist a
    JOIN album al        ON a.artist_id  = al.artist_id
    JOIN track t         ON al.album_id  = t.album_id
    JOIN invoice_line il ON t.track_id   = il.track_id
    GROUP BY a.artist_id, a.name
    ORDER BY total_revenue DESC
    LIMIT 1
),

-- Top album by revenue.
album_revenue AS (
    SELECT
        al.title AS album_title,
        a.name   AS artist_name,
        SUM(il.unit_price * il.quantity) AS total_revenue
    FROM album al
    JOIN artist a        ON al.artist_id = a.artist_id
    JOIN track t         ON al.album_id  = t.album_id
    JOIN invoice_line il ON t.track_id   = il.track_id
    GROUP BY al.album_id, al.title, a.name
    ORDER BY total_revenue DESC
    LIMIT 1
)

-- =============================================================================
-- Final Output: UNION ALL assembles the full Executive Dashboard as one result
-- set. Swap this for "SELECT * FROM <stage_name>;" to inspect any single stage.
-- =============================================================================

-- Customer Segment Summary + Revenue by Segment + Top Customer/Genre per Segment
SELECT
    'SEGMENT: ' || sa.segment AS metric_category,
    'Customers: ' || sa.total_customers
        || ' | Rev: $' || sa.segment_revenue
        || ' | Top Cust: ' || tc.customer_name
        || ' | Top Genre: ' || tg.genre_name AS metric_details
FROM segment_agg sa
JOIN top_customer_per_segment tc ON sa.segment = tc.segment
JOIN top_genre_per_segment tg    ON sa.segment = tg.segment

UNION ALL

-- Best Performing Country
SELECT
    'TOP COUNTRY: ' || country,
    'Rank: ' || country_rank || ' | Score: ' || performance_score || ' | Rev: $' || total_revenue
FROM country_ranking
WHERE country_rank = 1

UNION ALL

-- Revenue Contribution by Country (every country, not just the top 3)
SELECT
    'COUNTRY CONTRIBUTION: ' || country,
    'Rank: ' || country_rank || ' | Contribution: ' || revenue_contribution_pct || '% of Global Revenue'
FROM country_ranking

UNION ALL

-- Explicit top-3 expansion recommendation
SELECT
    'EXPANSION CANDIDATE #' || country_rank || ': ' || country,
    'Score: ' || performance_score || ' | Contribution: ' || revenue_contribution_pct || '%'
FROM country_ranking
WHERE country_rank <= 3

UNION ALL

-- Top Employee by Revenue
SELECT
    'TOP EMPLOYEE',
    employee_name || ' | Rev: $' || total_revenue
FROM employee_revenue

UNION ALL

-- Top Artist by Revenue
SELECT
    'TOP ARTIST',
    artist_name || ' | Rev: $' || total_revenue
FROM artist_revenue

UNION ALL

-- Top Album by Revenue
SELECT
    'TOP ALBUM',
    album_title || ' by ' || artist_name || ' | Rev: $' || total_revenue
FROM album_revenue;
