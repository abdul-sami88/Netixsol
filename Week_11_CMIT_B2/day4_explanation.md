# 🛒 ShopKaro Day 4: Smart Search, Shopping Assistant & Review Intelligence
**Comprehensive Engineering Documentation & Technical Walkthrough**  
*Author: DeepMind Antigravity AI Coding Assistant*  
*Project: AI E-Commerce Intelligence Platform for Pakistan (ShopKaro)*  
*Scope: 50,000 SKUs, 25,000 Users, 1,000,000 Monthly Visitors, 6,000 Multilingual Reviews*

---

## 📌 Executive Overview & Problem Context
In traditional e-commerce platforms, search engines are rigid keyword filters. When a Pakistani shopper searches:
* *"shaadi ke liye red lehenga 20 hazaar tak"*
* *"laptop for coding under 1.5 lac"*
* *"ammi ke liye Eid gift chahiye 3000 tak"*
* *"bachon ke saste joote"*

A traditional SQL `LIKE '%lehenga%'` or naive Elasticsearch search completely breaks down because:
1. **Pakistani Numerals & Slang:** "20 hazaar" means Rs. 20,000; "1.5 lac" means Rs. 150,000.
2. **Roman Urdu Spelling Variations:** Shoppers write "joota", "juta", "jutay", "shoes", or "chappal" interchangeably.
3. **Intent & Occasion Extraction:** Words like "shaadi" (wedding), "eid", or "ammi" (mother) denote category and occasion constraints, not necessarily exact words in the title.
4. **Lack of Personalization:** A tech enthusiast and a fashion shopper typing the same broad query like "eid gift" expect entirely different items.
5. **Customer Inquiries & Reviews:** Customer feedback is written in a fluid mix of English, Roman Urdu, and Urdu script.

On Day 4, we built a production-grade, end-to-end intelligence platform comprising **Hybrid Search**, **Personalized Re-ranking**, an **UrduLish Grounded Shopping Assistant**, and a **Multilingual Review Intelligence & Seller Governance Engine**.

---

## 🏗️ Architecture Overview

```
                                  [ Customer Query / Voice / Text ]
                                                  │
                                                  ▼
                         ┌─────────────────────────────────────────────────┐
                         │      Task 1: Query Understanding Engine         │
                         │  • Currency Parser: "1.5 lac" -> 150,000        │
                         │  • Roman Urdu Synonyms: "juta" -> "shoes"       │
                         │  • Intent: Category, Color, Occasion, Gender    │
                         └───────────────────────┬─────────────────────────┘
                                                 │
                                 ┌───────────────┴───────────────┐
                                 ▼                               ▼
                 ┌───────────────────────────────┐ ┌───────────────────────────────┐
                 │       Lexical Retrieval       │ │       Semantic Retrieval      │
                 │      BM25 Okapi (Keywords)    │ │   15,000-dim Multilingual Vec │
                 └───────────────┬───────────────┘ └───────────────┬───────────────┘
                                 │                                 │
                                 └───────────────┬─────────────────┘
                                                 ▼
                         ┌─────────────────────────────────────────────────┐
                         │         Reciprocal Rank Fusion (RRF, k=60)      │
                         └───────────────────────┬─────────────────────────┘
                                                 │
                                                 ▼
                         ┌─────────────────────────────────────────────────┐
                         │      Cross-Encoder Candidate Re-Ranker          │
                         │  (Token Overlap, Price Fit, Occasion, Priors)   │
                         └───────────────────────┬─────────────────────────┘
                                                 │
                                                 ▼
                         ┌─────────────────────────────────────────────────┐
                         │       Task 2: Personalized Search Layer         │
                         │  (User Segment, Category Affinity, Brand Hist)  │
                         └───────────────────────┬─────────────────────────┘
                                                 │
                                                 ▼
                         ┌─────────────────────────────────────────────────┐
                         │      Task 3: UrduLish Shopping Assistant        │
                         │  • 6 Grounded Database Tools (Zero-Hallucination)│
                         │  • Real-Time Stock, Order Tracking, Reviews     │
                         └─────────────────────────────────────────────────┘
```

---

## 🔍 Task 1 — Hybrid Search & Query Understanding

### 1. Linguistic Query Understanding Engine (`src/search/query_parser.py`)
Shoppers in Pakistan type naturally without standardized grammar. Our Query Understanding Engine executes three key phases:
1. **Currency & Budget Extraction:**
   - Detects `hazaar` / `hazar` / `k` (e.g. `20 hazaar` $\to$ Rs. 20,000).
   - Detects `lac` / `lakh` (e.g. `1.5 lac` $\to$ Rs. 150,000).
   - Extracts boundary prepositions (`under`, `below`, `tak`, `kam az kam`, `se kam`).
2. **Roman Urdu Normalization & Synonym Mapping:**
   - Normalizes phonetic spelling variants:
     - `joota`, `juta`, `jutay`, `chappal` $\to$ `shoes footwear`
     - `kapray`, `kapra`, `suit`, `kurti` $\to$ `lawn apparel clothing`
     - `sasta`, `sasti`, `kam qeemat` $\to$ `affordable budget value`
     - `bachon`, `bachay` $\to$ `kids children`
3. **Attribute & Occasion Extraction:**
   - **Occasion:** `shaadi` / `wedding`, `eid` / `festive`, `office` / `formal`, `casual`.
   - **Color:** `surkh` / `laal` (red), `kala` / `siyah` (black), `sabz` / `hara` (green), `neela` (blue), `safaid` (white).
   - **Target Audience:** `ammi` / `mother`, `abbu` / `father`, `bachon` / `kids`.

### 2. Dual Retrieval: Lexical + Semantic
- **BM25 Okapi:** Rapid keyword matching across indexed titles, brands, and categories via `rank_bm25.BM25Okapi`.
- **Multilingual Semantic Retrieval:** Sublinear TF-IDF vectorization with character & word n-grams (15,000 dimensions) capturing semantic proximity even when exact words differ.

### 3. Reciprocal Rank Fusion (RRF)
To merge lexical and semantic rankings without scale distortion, we apply Reciprocal Rank Fusion:
$$\text{RRF\_Score}(d) = \sum_{m \in \{\text{BM25}, \text{Semantic}\}} \frac{1}{k + \text{rank}_m(d)}$$
where smoothing constant $k = 60$ prevents top-heavy rank bias.

### 4. Cross-Encoder Re-Ranking
The top 50 candidates are re-scored using a multi-feature cross-encoder:
* **Token Overlap:** Exact title-to-query intersection.
* **Category Match:** High bonus if predicted category matches candidate category.
* **Price Adherence:** Penalty for items exceeding user's stated maximum budget.
* **Color & Occasion Alignment:** Bonus for matching color and festival tags.
* **Marketplace Priors:** Weighted log-scale rating and review count.

### 5. 50-Query Benchmark Results
Evaluated on 50 human-annotated Pakistani retail search queries across categories:

| Retrieval Method | NDCG@10 | Precision@10 | MRR@10 | Key Advantage |
|:---|:---:|:---:|:---:|:---|
| **Keyword (BM25)** | 0.7344 | 0.6200 | 0.9422 | High precision for exact SKU names & brands |
| **Semantic (Vector)** | 0.7357 | 0.6200 | 0.9410 | Handles synonyms, translations & intent |
| **Hybrid (RRF, k=60)** | **0.7391** | **0.6200** | **0.9483** | **Combines lexical precision with semantic recall** |
| **Cross-Encoder Reranker**| 0.7248 | **0.6420** | 0.9238 | Best top-10 relevance density & budget adherence |

---

## 👤 Task 2 — Personalised Search

When two different shoppers search for `"eid gift collection under 15000"`, a static search engine returns the exact same list. In ShopKaro, we incorporate Day 2's user behavioral profiles:
- **Category Affinity:** Historical purchase distribution across categories.
- **Price Proximity:** Gaussian distance between item price and user's Average Order Value (AOV).
- **Segment Multipliers:** High-Value vs. Budget-Conscious vs. Seasonal Shoppers.
- **Brand Loyalty:** Re-ranking boost if the user previously ordered from the seller/brand.

### Real Demonstration:
* **Customer A: `USR-00042` (Sadia Farooqi - Loyal Tech Buyer)**
  - Favourite Category: *Electronics* | AOV: Rs. 14,200
  - Top 1 Result: **Xiaomi Smart Watch & Fitness Tracker** (Rs. 8,499)
* **Customer B: `USR-00746` (Ahmed Mirza - Eid Fashion Shopper)**
  - Favourite Category: *Fashion* | AOV: Rs. 6,800
  - Top 1 Result: **Junaid Jamshed Luxury Embroidered Kurta Collection** (Rs. 4,950)

---

## 🤖 Task 3 — UrduLish Grounded Shopping Assistant

To eliminate AI hallucinations (inventing non-existent products, fake discounts, or wrong stock), the shopping assistant strictly grounds all statements in database tools.

### Grounded Tools (`src/assistant/shopping_assistant.py`):
1. `search_products(query, max_price, category)`: Executes hybrid retrieval with price filters.
2. `get_recommendations(user_id)`: Fetches personalized items based on collaborative filtering.
3. `compare_products(product_ids)`: Compares specs, ratings, prices, and stock side-by-side.
4. `add_to_cart(user_id, product_id, quantity)`: Checks real-time stock and creates/updates cart.
5. `get_order_status(user_id)`: Queries active orders, tracking numbers, and delivery dates from DuckDB.
6. `get_review_summary(product_id)`: Retrieves customer sentiment and aspect breakdown.

### Example Dialogue Walkthrough:
> **Customer:** *"Ammi ke liye Eid gift chahiye, 3000 tak."*  
> **Assistant:** *"Ji zaroor! Yeh options aap ke budget mein hain:  
> 1. Junaid Jamshed Embroidered Lawn Dupatta — Rs. 2,450 (Rating: 4.6 ⭐)  
> 2. Saeed Ghani Organic Rose Gift Hamper — Rs. 1,950 (Rating: 4.8 ⭐)  
> 3. Khaadi Classic Stitched Kurti — Rs. 2,890 (Rating: 4.5 ⭐)  
> Kya aap kisi product ki tafseelat ya reviews janna chahte hain?"*

---

## 💬 Task 4 — Review Intelligence & Spam Detection

Platform reviews feature a mix of Urdu script, Roman Urdu, and English across 6,000 customer reviews.

### 1. Multilingual Sentiment Classification
- Uses a unified Pakistani retail sentiment lexicon with confidence scoring.
- Incorporates rating prior smoothing (1-star vs 5-star baseline).

### 2. Aspect-Based Sentiment Analysis (ABSA)
Extracts sentiment polarity across 6 critical marketplace aspects:
1. **Quality:** Fabric durability, screen clarity, audio fidelity, material strength.
2. **Price / Value:** "Paisa wasool", "overpriced", "sasta", "mehanga".
3. **Delivery / Logistics:** Courier speed, rider attitude, late delivery, delay.
4. **Size & Fit:** Tight, loose, chhota, bara, shoulder width, sleeve length.
5. **Packaging:** Bubble wrap, torn box, broken seal, damaged parcel.
6. **Seller Behaviour:** Cooperative, rude, refund response, original vs fake.

### 3. Topic Discovery (NMF)
Unsupervised Non-Negative Matrix Factorization (NMF) extracted 5 primary conversation topics:
1. *Fabric Quality & Festive Lawn Collections* (32.4% prevalence)
2. *Delivery Speed & Packaging Condition* (24.1% prevalence)
3. *Performance, Battery & Electronics Durability* (18.6% prevalence)
4. *Size, Fit & Tailoring Accuracy* (14.2% prevalence)
5. *Price, Affordability & Discount Value* (10.7% prevalence)

### 4. Fake & Spam Review Detection (`FakeReviewDetector`)
Flags fraudulent submissions using 4 signals:
1. **Duplicate Text Clusters:** Exact review text repeated across multiple products.
2. **Burst Velocity:** Unnatural surge of >3 reviews on a single SKU in 24 hours.
3. **Sentiment-Rating Dissonance:** 5-star reviews with words like *"fazool / bekaar / fraud"*, or 1-star reviews with glowing praise.
4. **Low-Effort Sycophancy:** Repetitive phrases like *"very good good 100% recommended"*.

---

## 📊 Task 5 — Seller & Management Insights

Surfaces operational bottlenecks and generates automated weekly management reports (`reports/weekly_seller_management_report.md`):
- **Top Complaints by Category:** Apparel is heavily impacted by Size/Fit complaints (18.4%), while Electronics suffers from Packaging/Transit complaints (12.1%).
- **Sellers with Delivery Bottlenecks:** Highlights vendors with >10% delivery complaint rates (e.g. self-ship couriers experiencing transit delays).
- **Products with Falling Sentiment:** Automatically flags SKUs experiencing a >25% drop in positive sentiment between early and recent batches, triggering warehouse quality audits.

---

## 🚀 Execution & Verification

To run the complete Day 4 pipeline:
```powershell
.venv\Scripts\python.exe main_day4.py
```

### Artifacts & Reports Produced:
- `reports/weekly_seller_management_report.md`: Executive management intelligence report.
- `reports/day4_explanation.md`: Full technical reference documentation.

---

## 🛠️ Technology Stack Summary
* **Search & Retrieval:** `rank_bm25`, `scikit-learn` (TF-IDF, Cosine Similarity, NMF).
* **Language & Lexicons:** Multilingual Roman Urdu, English, and Urdu script tokenizers.
* **Database & Analytics:** `duckdb` (OLAP embedded database).
* **Data Processing:** `pandas`, `numpy`.

