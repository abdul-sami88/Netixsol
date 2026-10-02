"""
src/feature_engineering.py
==========================
Production-grade domain feature engineering for Pakistani property valuation
and real estate lead scoring datasets.

Includes:
1. Property Features:
   - price_per_marla
   - covered_area_ratio
   - property_age_bucket
   - society_tier (Tier 1 Luxury, Tier 2 Premium, Tier 3 Affordable)
   - amenity_score (weighted infrastructure index)
   - composite_accessibility_index (inverted distance decay)
   - bed_bath_ratio
   - prime_location_features (corner + park + boulevard)

2. Lead Scoring Features:
   - lead_engagement_score (calls x call duration)
   - response_speed_category (instant, prompt, moderate, delayed)
   - budget_to_market_price_ratio (lead budget vs actual city/type median price)
   - interaction_intensity (followups per elapsed day)
   - objection_friction_score (graded sales friction)
   - visit_funnel_status (milestone progression)
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional


# ========================================================
# Weighted Amenity Scoring Map
# ========================================================
AMENITY_WEIGHTS = {
    "swimming pool": 3.0,
    "elevator": 2.5,
    "backup generator / solar": 2.0,
    "underground utilities": 1.5,
    "central heating / cooling": 1.5,
    "24/7 security": 1.0,
    "gated community": 1.0,
    "servant quarter": 1.0,
    "lawn / garden": 1.0,
}

OBJECTION_SEVERITY_MAP = {
    "No Objection Raised": 0,
    "None": 0,
    "Family Consensus Pending": 1,
    "Location Too Far": 2,
    "Timing / Delayed Decision": 2,
    "Payment Plan / Financing Needed": 3,
    "Price / Budget Gap": 3,
    "Legal / Title Verification": 4,
}


def calculate_amenity_score(amenities_str: str) -> float:
    """
    Computes a weighted infrastructural luxury score from semicolon-delimited amenities.
    Elevators, power backup/solar, and pools contribute higher value than basic security.
    """
    if pd.isna(amenities_str) or not str(amenities_str).strip() or str(amenities_str).strip().lower() == "basic":
        return 0.0

    score = 0.0
    text_lower = str(amenities_str).lower()
    for amenity, weight in AMENITY_WEIGHTS.items():
        if amenity in text_lower:
            score += weight

    return float(score)


def assign_society_tier(df: pd.DataFrame) -> pd.Series:
    """
    Categorizes housing societies into economic tiers based on median price-per-marla percentiles within each city.
    - Tier 1 (Ultra Luxury / Diplomatic / Prime): Top 25% price per marla
    - Tier 2 (Premium / Established): Middle 50%
    - Tier 3 (Mid-Market / Suburban): Bottom 25%
    """
    # Calculate median price per marla per (city, location)
    loc_medians = df.groupby(["city", "location"])["price_per_marla"].transform("median")
    city_q25 = df.groupby("city")["price_per_marla"].transform(lambda x: x.quantile(0.33))
    city_q75 = df.groupby("city")["price_per_marla"].transform(lambda x: x.quantile(0.67))

    tiers = pd.Series("Tier 2 - Premium", index=df.index)
    tiers[loc_medians >= city_q75] = "Tier 1 - Ultra Luxury"
    tiers[loc_medians < city_q25] = "Tier 3 - Affordable/Suburban"
    return tiers


def engineer_property_features(df_prop: pd.DataFrame) -> pd.DataFrame:
    """
    Applies domain feature engineering to cleaned property listings dataframe.
    """
    df = df_prop.copy()

    # 1. Price Per Marla
    if "price_pkr" in df.columns:
        df["price_per_marla"] = df["price_pkr"] / (df["plot_size_marla"] + 1e-5)
    else:
        # Fallback if price is not present (e.g. test set without target)
        df["price_per_marla"] = np.nan

    # 2. Covered Area Ratio (Construction Density)
    # Standard 1 Marla = 225 sq ft
    df["covered_area_ratio"] = df["covered_area_sqft"] / ((df["plot_size_marla"] * 225.0) + 1e-5)

    # 3. Property Age Bucket
    age_bins = [-1, 1, 5, 15, 100]
    age_labels = ["Brand New (0-1y)", "Modern (2-5y)", "Established (6-15y)", "Vintage (16y+)"]
    df["property_age_bucket"] = pd.cut(df["age_years"], bins=age_bins, labels=age_labels)

    # 4. Society Tier
    df["society_tier"] = assign_society_tier(df)

    # 5. Weighted Amenity Score
    df["weighted_amenity_score"] = df["amenities"].apply(calculate_amenity_score)

    # 6. Composite Accessibility Index
    # Inverted distance metric: closer to amenities -> higher accessibility index
    w_main = 0.35
    w_comm = 0.30
    w_hosp = 0.20
    w_sch = 0.15
    weighted_dist = (
        w_main * df["dist_to_main_road_km"] +
        w_comm * df["dist_to_commercial_km"] +
        w_hosp * df["dist_to_hospital_km"] +
        w_sch * df["dist_to_school_km"]
    )
    df["composite_accessibility_index"] = 1.0 / (1.0 + weighted_dist)

    # 7. Bed to Bath Ratio & Total Functional Rooms
    df["bed_bath_ratio"] = df["bedrooms"] / (df["bathrooms"] + 1e-4)
    df["total_rooms"] = df["bedrooms"] + df["bathrooms"]

    # 8. Luxury Plot Factor (Prime Orientation Combo)
    df["prime_orientation_score"] = df["is_corner"] + df["is_park_facing"] + df["is_main_boulevard"]

    # 9. Space per Bedroom
    df["covered_area_per_bed"] = df["covered_area_sqft"] / (df["bedrooms"] + 1e-4)

    return df


def compute_market_benchmarks(df_prop: pd.DataFrame) -> pd.DataFrame:
    """
    Computes median property prices grouped by (city, property_type).
    Used to calculate budget-to-market-price ratio in the leads dataset.
    """
    benchmarks = df_prop.groupby(["city", "property_type"])["price_pkr"].median().reset_index()
    benchmarks.rename(columns={"city": "preferred_city", "property_type": "property_type_preferred", "price_pkr": "market_median_price_pkr"}, inplace=True)
    return benchmarks


def engineer_leads_features(
    df_leads: pd.DataFrame,
    df_prop_clean: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Applies domain feature engineering to cleaned leads scoring dataframe.
    """
    df = df_leads.copy()

    # 1. Lead Engagement Score (Cumulative Phone Interaction Minutes)
    df["lead_engagement_score"] = df["num_calls"] * df["avg_call_duration_mins"]

    # 2. Response Speed Category
    response_bins = [-1, 1.0, 4.0, 12.0, 1000.0]
    response_labels = ["Instant (<1h)", "Prompt (1-4h)", "Moderate (4-12h)", "Delayed (>12h)"]
    df["response_speed_category"] = pd.cut(df["response_time_hours"], bins=response_bins, labels=response_labels)

    # 3. Interaction Intensity (Touchpoints per Day)
    df["interaction_intensity"] = df["followup_count"] / (df["days_since_first_contact"] + 1.0)

    # 4. Objection Friction Score (Ordinal Scale 0 to 4)
    df["objection_friction_score"] = df["objection_raised"].map(OBJECTION_SEVERITY_MAP).fillna(0).astype(int)

    # 5. Visit Funnel Progression
    def classify_visit(row):
        booked = str(row["visit_booked"]).strip().lower() == "yes"
        completed = str(row["visit_completed"]).strip().lower() == "yes"
        if completed:
            return "Visit Completed"
        elif booked:
            return "Visit Booked Only"
        else:
            return "No Visit"

    df["visit_funnel_status"] = df.apply(classify_visit, axis=1)

    # 6. Budget-to-Market-Price Ratio
    if df_prop_clean is not None:
        benchmarks = compute_market_benchmarks(df_prop_clean)
        df = df.merge(benchmarks, on=["preferred_city", "property_type_preferred"], how="left")

        # For property types not in listings (e.g. 'Plot / Plot File' or 'Commercial'),
        # use the overall city median price
        city_medians = df_prop_clean.groupby("city")["price_pkr"].median().to_dict()
        df["market_median_price_pkr"] = df["market_median_price_pkr"].fillna(df["preferred_city"].map(city_medians))
        df["market_median_price_pkr"] = df["market_median_price_pkr"].fillna(df_prop_clean["price_pkr"].median())

        df["budget_to_market_ratio"] = df["budget_pkr"] / (df["market_median_price_pkr"] + 1e-5)
    else:
        # Fallback if property dataset is not provided
        city_approx = {"Lahore": 35_000_000, "Karachi": 38_000_000, "Islamabad": 45_000_000, "Rawalpindi": 22_000_000, "Faisalabad": 20_000_000}
        approx_median = df["preferred_city"].map(city_approx).fillna(30_000_000)
        df["budget_to_market_ratio"] = df["budget_pkr"] / (approx_median + 1e-5)

    # 7. Budget Realism Category
    # Constrained (<0.7), Realistic (0.7-1.3), Affluent (>1.3)
    ratio_bins = [-1.0, 0.7, 1.3, 1000.0]
    ratio_labels = ["Under-Budgeted (<0.7x)", "Market-Aligned (0.7-1.3x)", "High-Budgeted (>1.3x)"]
    df["budget_realism_tier"] = pd.cut(df["budget_to_market_ratio"], bins=ratio_bins, labels=ratio_labels)

    return df


if __name__ == "__main__":
    from data_cleaning import clean_property_data, clean_leads_data
    df_p = clean_property_data(pd.read_csv("Data/property_listings.csv"), verbose=False)
    df_l = clean_leads_data(pd.read_csv("Data/leads_scoring.csv"), verbose=False)

    df_p_feat = engineer_property_features(df_p)
    df_l_feat = engineer_leads_features(df_l, df_p)

    print("Engineered Property Features Shape:", df_p_feat.shape)
    print("Sample Property New Features:\n", df_p_feat[["price_per_marla", "covered_area_ratio", "society_tier", "weighted_amenity_score", "composite_accessibility_index"]].head(3))

    print("\nEngineered Leads Features Shape:", df_l_feat.shape)
    print("Sample Leads New Features:\n", df_l_feat[["lead_engagement_score", "response_speed_category", "interaction_intensity", "objection_friction_score", "budget_to_market_ratio"]].head(3))
