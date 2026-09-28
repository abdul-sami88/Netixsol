# Comprehensive Data Dictionary: Real Estate Valuation & Lead Scoring

**Project:** AI Property Valuation & Intelligent Lead Scoring System  
**Stage:** Day 1 — Data Understanding, Cleaning & Feature Engineering  
**Market Context:** Pakistan Real Estate (Lahore, Karachi, Islamabad, Rawalpindi, Faisalabad)

---

## 1. Property Listings Dataset (`property_listings.csv`)

- **Total Records:** 6,500
- **Total Attributes:** 23
- **Primary Source:** Major Pakistani real estate portals (Zameen.com, Graana.com, agency CRM feeds)
- **Target Variable (Valuation Model):** `price_pkr`

| Column Name | Data Type | Description | Unit | Source | Known Issues & Data Quality Nuances |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `property_id` | String (`object`) | Unique identifier for the listing (e.g., `PROP-10001`). | Categorical ID | Portal Scraper / Internal DB | Non-predictive identifier; must be excluded from modeling to avoid leakage. |
| `city` | String (`object`) | Metropolitan city where the property is located (Karachi, Lahore, Islamabad, Rawalpindi, Faisalabad). | Administrative Boundary | Portal metadata | Needs validation against location to prevent cross-city misattribution. |
| `location` | String (`object`) | Specific neighborhood, sector, or housing scheme (e.g., DHA Phase 5, Bahria Town, Clifton). | Geographic Sector | Portal listing text | High cardinality (32+ unique sectors); contains abbreviations and variant spellings ("DHA Ph 5" vs "DHA Phase 5"). |
| `property_type` | String (`object`) | Architectural form (House, Flat, Upper Portion, Lower Portion, Farmhouse, Penthouse). | Categorical Type | Listing classification | Farmhouses and Penthouses exhibit extreme non-linear price escalations compared to standard residential units. |
| `plot_size_marla` | Float (`float64`) | Land surface area normalized to Marlas. | Marla | Portal listing | Unit conversion discrepancies in Pakistan (1 Marla is standardized to 225 sq ft in modern CDA/LDA schemes, but traditionally 272.25 sq ft in older revenue records). |
| `plot_size_unit` | String (`object`) | Original measurement unit stated by seller (`Marla`, `Kanal`). | Unit descriptor | User input | Redundant with `plot_size_marla`; serves as reference metadata. |
| `plot_size_display`| String (`object`) | Human-readable string representation (e.g., "5 Marla", "1 Kanal"). | Text display | User input | String format with units; not suitable for direct mathematical modeling. |
| `covered_area_sqft`| Integer (`int64`) | Total constructed enclosed floor space in square feet. | Square Feet (sq ft)| Architectural specification | Multi-storey houses have covered area > plot size; single-storey portions or flats have smaller ratios. Watch for typo entries. |
| `bedrooms` | Integer (`int64`) | Total number of dedicated bedrooms. | Count | User input | Zero or extreme values (e.g., >8) require validation against property type. |
| `bathrooms` | Integer (`int64`) | Total number of bathrooms (attached and powder rooms). | Count | User input | Can occasionally exceed bedroom counts in luxury properties; zero values in residential units require sanity check. |
| `age_years` | Integer (`int64`) | Building construction age since completion (0 = brand new/under construction). | Years | Seller disclosure | Non-linear depreciation; 0-year-old properties command developer premiums, whereas >20-year properties are valued mostly for land value. |
| `floors` | Integer (`int64`) | Number of architectural storeys (1 = Single storey, 2 = Double storey, etc.). | Count | Building plan | Portions represent 1 floor of a multi-unit property; houses can be 2-3 floors. |
| `is_corner` | Integer (`int64`) | Binary flag indicating if property is situated at a street corner (1 = Yes, 0 = No). | Binary flag (0/1) | Listing attributes | Pakistani buyers historically pay a 5% to 15% location premium for corner plots due to dual access and ventilation. |
| `is_park_facing` | Integer (`int64`) | Binary flag indicating unobstructed park view / frontage (1 = Yes, 0 = No). | Binary flag (0/1) | Listing attributes | High visual demand feature commanding 5-10% valuation premium. |
| `is_main_boulevard`| Integer (`int64`) | Binary flag indicating frontage on a wide primary commercial/arterial road. | Binary flag (0/1) | Listing attributes | Commercial upside vs residential noise tradeoff. |
| `amenities` | String (`object`) | Semicolon-delimited list of infrastructural amenities (e.g., Gated Community; 24/7 Security; Solar; Elevator). | Text list | Portal checkboxes | High-value unstructured feature; must be parsed into count and weighted amenity indices. |
| `amenities_count` | Integer (`int64`) | Simple tally of recognized amenities. | Count | Feature extraction | May overweight basic amenities equally with premium amenities (e.g., swimming pool vs water tank). |
| `dist_to_main_road_km`| Float (`float64`) | Orthodromic/road distance to nearest primary transport corridor. | Kilometers (km) | Geospatial engine | Skewed distribution; distance decay exhibits non-linear penalties beyond 3 km. |
| `dist_to_school_km` | Float (`float64`) | Distance to nearest recognized academic institution. | Kilometers (km) | Geospatial engine | Proximity under 1.5 km highly prioritized by family home buyers. |
| `dist_to_hospital_km`| Float (`float64`) | Distance to nearest tertiary or secondary hospital. | Kilometers (km) | Geospatial engine | Outliers in suburban fringe developments (e.g., Bahria Karachi, Adiala Road). |
| `dist_to_commercial_km`| Float (`float64`)| Distance to nearest commercial hub/civic center/bazaar. | Kilometers (km) | Geospatial engine | Properties within walking distance (<1 km) command convenience premiums. |
| `listing_date` | String (`object`) | Date listing was posted on the exchange (`YYYY-MM-DD`). | Date | System timestamp | Temporal feature; must not be used directly as a regression variable to avoid temporal overfitting. |
| `price_pkr` | Integer (`int64`) | Listed asking price in Pakistani Rupees (PKR). **(Target)** | Pakistani Rupees (PKR) | Seller asking price | Heavy right-tail skew; contains luxury estates reaching 1+ Billion PKR. Requires log-transformation ($log(1+p)$) for regression modeling. |

---

## 2. Lead Scoring Dataset (`leads_scoring.csv`)

- **Total Records:** 4,500
- **Total Attributes:** 17
- **Primary Source:** Real estate brokerage omnichannel CRM (Meta Ads, Google Search, Zameen Portal, WhatsApp, Direct Walk-ins)
- **Target Variable (Classification Model):** `converted` (Binary: 1 = Closed Deal, 0 = Lost/Inactive)

| Column Name | Data Type | Description | Unit | Source | Known Issues & Data Quality Nuances |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `lead_id` | String (`object`) | Unique CRM lead tracking ID (e.g., `LEAD-10001`). | Categorical ID | CRM internal key | Non-predictive; must be excluded from feature set. |
| `lead_source` | String (`object`) | Marketing attribution channel (Zameen, Facebook Ads, Google Ads, WhatsApp, Referral, Direct). | Marketing Channel | UTM / Lead ingest form | High variance in intent: Referrals and Portals convert at significantly higher rates than cold Facebook ads. |
| `budget_pkr` | Integer (`int64`) | Maximum stated purchase or investment budget in PKR. | Pakistani Rupees (PKR) | Lead qualification | Budget-market mismatch: Leads often state unrealistic budgets for their desired city/property type. |
| `preferred_city` | String (`object`) | Target city of interest for the lead. | City name | Customer inquiry | Must align with property valuation dataset to enable cross-dataset price-ratio features. |
| `purpose` | String (`object`) | Intent of acquisition (`Buy (Own Use)`, `Investment`, `Rent`). | Purpose classification | Customer intake | Investment buyers are price/yield sensitive; own-use buyers are amenity and location sensitive. |
| `property_type_preferred`| String (`object`)| Desired structural type (House, Flat, Plot / Plot File, Commercial, Farmhouse). | Housing category | Customer inquiry | Includes "Plot / Plot File" and "Commercial" which require custom market benchmark matching. |
| `num_calls` | Integer (`int64`) | Total number of recorded phone interactions with sales agents. | Call count | Telephony PBX system | Diminishing returns: high call counts with low duration indicate persistent unanswered attempts. |
| `avg_call_duration_mins` | Float (`float64`) | Mean conversation duration per call. | Minutes | Telephony PBX system | Strong positive signal of genuine lead qualification and rapport building. |
| `response_time_hours` | Float (`float64`) | Elapsed hours between initial inquiry and agent's first response. | Hours | Inbound SLA log | Fast response (<1 hour) dramatically increases odds of conversion; long lag degrades lead viability. |
| `visit_booked` | String (`object`) | Whether a physical property site visit was scheduled (`Yes`, `No`). | Categorical boolean | CRM stage | Funnel milestone indicator. |
| `visit_completed` | String (`object`) | Whether the client actually attended the site inspection (`Yes`, `No`). | Categorical boolean | Agent field report | Extremely strong conversion correlate; beware of potential operational leakage if recorded post-deal. |
| `days_since_first_contact` | Integer (`int64`) | Elapsed calendar days from initial lead capture to current status audit. | Days | CRM timeline | Stale leads (>90 days) require re-engagement workflows; conversion velocity drops over time. |
| `objection_raised` | String (`object`) | Primary roadblock voiced by client (Price Gap, Location Far, Financing, Legal Title, Family Consensus, Timing). | Objection category | Agent CRM note | **Contains 1,438 Missing Values (31.9%)**. A null value indicates that no explicit objection was recorded ("No Objection Raised"). Must be imputed with "No Objection Raised". |
| `followup_count` | Integer (`int64`) | Total CRM touchpoints (emails, WhatsApp messages, reminders, check-ins). | Touchpoint count | CRM activity log | Captures sales effort and lead responsiveness. |
| `lead_stage` | String (`object`) | Sales pipeline classification (`Cold`, `Warm`, `Hot`). | Pipeline status | Sales agent subjective tag | **CRITICAL DATA LEAKAGE RISK**: `lead_stage` reflects human assessment of deal probability downstream. Using it to predict `converted` creates severe target leakage. **Must be removed during training.** |
| `inquiry_date` | String (`object`) | Timestamp when lead entered the system (`YYYY-MM-DD`). | Date string | System timestamp | Non-stationary seasonality; exclude raw string to avoid temporal memorization. |
| `converted` | Integer (`int64`) | Deal outcome flag (**1 = Closed Sale, 0 = Not Converted**). **(Target)** | Binary flag (0/1) | Accounting / Escrow | Severe class imbalance: **~20.6% Positive (Converted) vs 79.4% Negative (Unconverted)**. Requires Stratified Splitting and PR-AUC/F1 monitoring. |

---

## 3. Metric and Unit Standardization Rules

| Metric Dimension | Pakistani Vernacular Term | Normalized Canonical Unit | Conversion Standard |
| :--- | :--- | :--- | :--- |
| **Currency** | `Lac` / `Lakh` | PKR | $1\text{ Lac} = 100,000\text{ PKR} = 10^5\text{ PKR}$ |
| **Currency** | `Crore` / `Cr` | PKR | $1\text{ Crore} = 100\text{ Lac} = 10,000,000\text{ PKR} = 10^7\text{ PKR}$ |
| **Currency** | `Arab` | PKR | $1\text{ Arab} = 100\text{ Crore} = 1,000,000,000\text{ PKR} = 10^9\text{ PKR}$ |
| **Land Area** | `Marla` | Marla | Standardized baseline (225 sq ft modern scheme standard) |
| **Land Area** | `Kanal` | Marla | $1\text{ Kanal} = 20\text{ Marla} = 4,500\text{ sq ft}$ |
| **Covered Area** | `Square Feet (sq ft)`| sq ft | Standard floor surface area |
| **Land Area** | `Square Yards (Gaz)` | Marla | $1\text{ Sq Yard} = 9\text{ sq ft} \approx 0.04\text{ Marla}$ (25 sq yards = 1 Marla) |
