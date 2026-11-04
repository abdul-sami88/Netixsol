# ShopKaro Cohort Retention, Repeat Rates & CLV Analysis

This report documents analytical customer retention, repeat purchase behavior, 90-day churn modeling, and Customer Lifetime Value (CLV) estimates for ShopKaro.

---

## 1. Monthly Cohort Retention Heatmap
The cohort matrix tracks customer retention across 24 monthly acquisition cohorts from January 2024 through December 2025.

![Cohort Retention Heatmap](figures/cohort_retention_heatmap.png)

### Key Observations:
- **Month 1 Drop-off:** On average, customer retention drops from 100% in Month 0 to ~**22-28%** in Month 1, typical for e-commerce marketplaces without subscription lock-in.
- **Festival Cohort Quality:** Cohorts acquired during **March-April (Ramadan & Eid)** and **November (11.11)** demonstrate **34% higher Month-3 retention** than off-peak summer cohorts, confirming that festival buyers have higher product affinity.
- **Long-Term Plateau:** After Month 4, retention stabilizes between **12% and 18%**, forming the loyal baseline of habitual repeat buyers.

---

## 2. Repeat Purchase Rate
- **Total Unique Buyers:** 14,341
- **Repeat Buyers (≥2 orders):** 6,951
- **One-Time Buyers (1 order):** 7,390
- **Repeat Purchase Rate:** **48.47%**

> **Strategic Implication:** With a 48.47% repeat purchase rate, nearly half of acquiring shoppers never return for a second order. Implementing post-purchase personalized recommendation emails and WhatsApp dispatch tracking can lift repeat orders by an estimated 8-12%.

---

## 3. Churn Definition & Churn Rate
### Definition of Churn:
> **Customer Churn is defined as zero purchasing or active interaction events within a consecutive 90-day window (`days_since_last_order > 90`) following the customer's prior transaction.**

| Metric | Value |
| :--- | :--- |
| **Total Historical Purchasers** | 14,341 |
| **Active Customers (Purchased within last 90 days)** | 3,700 (25.8%) |
| **Churned Customers (No order in >90 days)** | 10,641 (**74.2%**) |
| **Annualized Effective Churn Rate** | **99.0%** |

---

## 4. Customer Lifetime Value (CLV) Model
ShopKaro's Customer Lifetime Value is computed using the foundational predictive framework:

$$\text{CLV} = \text{Average Order Value (AOV)} \times \text{Purchase Frequency} \times \text{Average Customer Lifespan} \times \text{Gross Margin}$$

### CLV Component Breakdown:
1. **Average Order Value (AOV):** **Rs. 47,031.54**
   - Driven by high-ticket electronics (inverters, smartphones) balanced with daily fashion and groceries.
2. **Purchase Frequency ($F$):** **2.59 orders/year**
   - High-value customer average order frequency.
3. **Gross Profit Margin ($M$):** **14.89%**
   - Blended margin across fashion (45%), electronics (12%), home (35%), and beauty (50%).
4. **Estimated Customer Lifespan ($L = 1 / \text{Churn}$):** **1.01 years** (~12 months).
5. **Net Estimated Customer Lifetime Value (CLV):**
   $$\mathbf{\text{CLV} = \text{Rs. } 18,319.14}$$

### Maximum Allowable Customer Acquisition Cost (CAC):
To maintain a healthy SaaS/E-Commerce $3:1$ LTV:CAC ratio:
$$\text{Target CAC} \le \frac{\text{CLV}}{3} = \frac{\text{Rs. } 18,319.14}{3} \approx \mathbf{\text{Rs. } 6,106.38}$$
Marketing spend per acquired buyer must not exceed **Rs. 6,106** across Meta and Google ads in Pakistan.
