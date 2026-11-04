# 📘 ShopKaro AI Platform: Stakeholder User Guides

---

## 🎯 1. Marketing Team User Guide

### How to Leverage Customer Personas for Campaigns
1. **Targeting by Persona:**
   * **🌙 Eid & Festive Shoppers (34.2%):** Schedule high-impact lawn and ethnic wear promotions 3 weeks before Ramadan and Eid.
   * **💻 Loyal Tech Enthusiasts (18.5%):** Target with high-ticket electronics, trade-in programs, and premium warranties.
   * **🛒 Routine Replenishers (22.1%):** Activate automated subscription replenishment emails for groceries and baby care every 25 days.
   * **🏷️ Bargain Hunters (15.8%):** Send notifications when clearance items drop below Rs. 2,999.
2. **Promoting High-Margin Items in Recommendations:**
   * Marketing can configure margin weights in `src/recommender/reranker.py`. By default, products with margins $\ge 40\%$ receive a $+20\%$ ranking multiplier.

---

## 🏭 2. Operations & Supply Chain User Guide

### How to Act on Inventory & Stockout Alerts
1. **Navigating the Operations Dashboard:**
   * Open the **Operations & Inventory** tab in the dashboard (`http://localhost:8000/`).
   * Review the **Imminent Stock-Out Risk Alerts** table.
2. **Executing Reorders:**
   * SKUs with **Days of Cover $\le 7$ days** must be reordered immediately from local suppliers.
   * Use the **P90 surge forecast** during festival prep (e.g., March/April for Eid) to stock enough buffer inventory for top-100 sellers.
3. **Liquidating Overstock:**
   * Inspect the **Overstock Liquidation Engine** table.
   * SKUs flagged with velocity $< 0.2$ units/day and warehouse stock $> 80$ units should be enrolled in **30%–50% flash promotional markdowns** to free up working capital.

---

## 📊 3. Executive Management User Guide

### Interpreting Platform Health & Experimentation
1. **Tracking Core KPIs:**
   * **Conversion Rate (CVR):** Benchmark target is $\ge 5.0\%$.
   * **Revenue Per Visitor (RPV):** Benchmark target is $\ge$ Rs. 380 PKR.
   * **Repeat Purchase Rate:** Maintained at $\approx 48.5\%$.
2. **Reviewing Weekly Intelligence Reports:**
   * The automated weekly report is located at [`reports/weekly_seller_management_report.md`](file:///c:/Users/MEE/Anti-Gravity_projects/AI_E-Commerce_Intelligence_Platform/reports/weekly_seller_management_report.md).
   * Key actions:
     - Check the **Top Delivery Bottleneck Sellers** table to place substandard couriers/sellers on probation.
     - Review the **Products with Severe Sentiment Degradation** table to recall defective batches.

