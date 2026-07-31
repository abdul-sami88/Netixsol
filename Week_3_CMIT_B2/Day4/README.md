# Music Store Business Intelligence Implementation

## Task 1: Customer Spending Profiles

The foundation of the pipeline begins by building a reusable customer profile. To avoid Cartesian product duplication, the logic is strictly split into two pre-aggregation CTEs:

- **`Invoice_Agg`**: Calculates invoice-level metrics (`total_spent`, `total_invoices`, `avg_invoice_value`).
- **`Track_Agg`**: Calculates track-level metrics (`total_tracks_purchased`, `unique_genres`, `unique_artists`).
These are safely joined at the customer grain, ensuring all subsequent tasks have a clean, accurate dataset to pull from without recalculating totals.

## Task 2: Segmentation Logic & Justification

CCustomer segments are determined by a weighted loyalty score incorporating five key metrics converted into quartiles via NTILE(4):

Metric Weight
Total Spending 3
Invoice Count 2
Purchase Frequency 2
Genre Diversity 1
Artist Diversity 1
Loyalty Score Formula & Segments
Loyalty Score = (Spending *3) + (Invoice* 2) + (Frequency * 2) + Genre + Artist

Loyalty Score Segment
24 and above Platinum
18 – 23 Gold
11 – 17 Silver
Below 11 Bronze

## Task 3: Marketing Recommendation Strategy

Using the favorite genre calculated via `ROW_NUMBER()`,  dynamically assign campaigns:

- **Platinum**: Early access to new releases in their favorite genre (Rewards loyalty).
- **Gold**: Exclusive Album Bundles in their favorite genre (Encourages larger cart sizes).
- **Silver**: 20% Off all tracks in their favorite genre (Incentivizes moving up to Gold).
- **Bronze**: First purchase coupon for their favorite genre (Lowers the barrier to entry for their next purchase).

## Task 4: Country Ranking Methodology

To identify expansion opportunities, a Country Expansion Score balances market size and customer quality using normalized metrics:

Expansion Score = (0.30 *Avg Rev/Cust) + (0.25* Total Rev) + (0.15 *Total Cust) + (0.10* Avg Invoice) + (0.10 *Genre Breadth) + (0.10* Cust Diversity)

Countries are ranked using the RANK() window function based on this final score.

## Task 5 & Bonus Challenge: Executive Dashboard Pipeline

The final report consolidates pipeline insights into a single view without redundant calculations, featuring:

Customer Segment Summary & Revenue Contribution
Top Customers, Genres, Artists, and Albums by Revenue
Top Employees and Top Three Expansion Countries

## 5 Actionable Recommendations

1. **Focus retention efforts on Platinum and Gold members**, who likely drive the vast majority of total revenue (Pareto Principle).
2. **Execute hyper-targeted genre campaigns**. Since we now know every customer's favorite genre through our pipeline, generic marketing emails should be completely replaced with genre-specific recommendations.
3. **Expand localized digital presence in the Top 3 Ranked Countries**, as they show both high total revenue and high customer density based on our custom weighted score.
4. **Offer targeted discounts to Bronze members** using the "First purchase coupon" strategy specifically targeted at their identified favorite genre to convert them to active buyers.
5. **Analyze the top genres within the Platinum segment** to influence future licensing or artist signing decisions, maximizing ROI where the most money is spent.

## Challenges Faced

Redundant Calculations: Solved by utilizing modular, chained CTEs across pipeline stages.
Accurate Customer Segmentation: Replaced spending-only metrics with a multi-variable weighted scoring model using NTILE().
Favorite Genre Identification: Leveraged ROW_NUMBER() to rank and isolate top music preferences per customer.
Objective Country Ranking: Developed a normalized 6-variable weighted expansion model.
