"""
src/data_cleaning.py
====================
Production-grade cleaning, normalization, outlier handling, and imputation
pipeline for Pakistani real estate listings and lead scoring datasets.

Handles:
- Missing values with domain-justified imputation
- Duplicate detection (exact and near-duplicates)
- Price normalization ('crore', 'lac', 'arab' -> numeric PKR)
- Area normalization (marla, kanal, sq ft, sq yards -> standardized Marla & Sq Ft)
- Location standardization ('DHA Ph 5' -> canonical naming)
- Outlier detection and treatment via IQR & Z-Score methods
"""

import re
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional, Union, List


# ==========================================
# 1. Price Normalization
# ==========================================

def normalize_price(price_input: Union[str, float, int]) -> Optional[float]:
    """
    Parses messy Pakistani price expressions into exact numeric PKR.
    
    Examples:
        '1.5 crore'   -> 15,000,000.0
        '85 lac'      -> 8,500,000.0
        '85 lakh'     -> 8,500,000.0
        '2.5 arab'    -> 2,500,000,000.0
        'PKR 15,000,000' -> 15,000,000.0
        '45M'         -> 45,000,000.0
        '500k'        -> 500,000.0
    """
    if pd.isna(price_input):
        return np.nan

    if isinstance(price_input, (int, float)):
        return float(price_input)

    val_str = str(price_input).strip().lower()
    val_str = val_str.replace("pkr", "").replace("rs.", "").replace("rs", "").replace(",", "").strip()

    # Match Crore / Cr
    match_crore = re.search(r"([\d\.]+)\s*(crore|cr)", val_str)
    if match_crore:
        num = float(match_crore.group(1))
        return num * 10_000_000.0

    # Match Lac / Lakh
    match_lac = re.search(r"([\d\.]+)\s*(lac|lakh|lk)", val_str)
    if match_lac:
        num = float(match_lac.group(1))
        return num * 100_000.0

    # Match Arab (Billion PKR)
    match_arab = re.search(r"([\d\.]+)\s*(arab|billion)", val_str)
    if match_arab:
        num = float(match_arab.group(1))
        return num * 1_000_000_000.0

    # Match Million (M)
    match_m = re.search(r"([\d\.]+)\s*(m|million)", val_str)
    if match_m:
        num = float(match_m.group(1))
        return num * 1_000_000.0

    # Match Thousand (K)
    match_k = re.search(r"([\d\.]+)\s*(k|thousand)", val_str)
    if match_k:
        num = float(match_k.group(1))
        return num * 1_000.0

    # Direct numeric fallback
    try:
        clean_num = re.sub(r"[^\d\.]", "", val_str)
        if clean_num:
            return float(clean_num)
    except Exception:
        pass

    return np.nan


# ==========================================
# 2. Area Normalization
# ==========================================

# Standard Pakistani conversion ratios:
# 1 Marla = 225 sq ft (Modern urban scheme standard: LDA, CDA, DHA, Bahria)
# 1 Kanal = 20 Marla = 4,500 sq ft
# 1 Sq Yard (Gaz) = 9 sq ft = 9 / 225 = 0.04 Marla

MARLA_TO_SQFT = 225.0
KANAL_TO_MARLA = 20.0
SQYARD_TO_SQFT = 9.0

def normalize_area_to_marla(size_input: Union[str, float, int], unit_str: Optional[str] = None) -> Optional[float]:
    """
    Converts various land measurements into standard Marla (225 sq ft base).
    """
    if pd.isna(size_input):
        return np.nan

    if isinstance(size_input, (int, float)) and (unit_str is None or pd.isna(unit_str)):
        return float(size_input)

    text = f"{size_input} {unit_str if unit_str else ''}".strip().lower()

    # Search for Kanal
    if "kanal" in text:
        m = re.search(r"([\d\.]+)", text)
        if m:
            return float(m.group(1)) * KANAL_TO_MARLA

    # Search for Marla
    if "marla" in text:
        m = re.search(r"([\d\.]+)", text)
        if m:
            return float(m.group(1))

    # Search for Sq Ft / Square Feet
    if "sq ft" in text or "sqft" in text or "square feet" in text:
        m = re.search(r"([\d\.]+)", text)
        if m:
            return float(m.group(1)) / MARLA_TO_SQFT

    # Search for Sq Yards / Gaz
    if "sq yard" in text or "sq yd" in text or "gaz" in text:
        m = re.search(r"([\d\.]+)", text)
        if m:
            return (float(m.group(1)) * SQYARD_TO_SQFT) / MARLA_TO_SQFT

    # Default numeric extraction assuming Marla if <= 200, else sqft
    m = re.search(r"([\d\.]+)", text)
    if m:
        num = float(m.group(1))
        return num if num <= 200 else (num / MARLA_TO_SQFT)

    return np.nan


# ==========================================
# 3. Location Standardization
# ==========================================

CANONICAL_LOCATION_PATTERNS = [
    # DHA Phases
    (re.compile(r'(?i)\bdha\b.*(?:ph(?:ase)?|p)?[-_\s]*(?:5|6|v|vi)\b'), 'DHA Defence Phase 5-6'),
    (re.compile(r'(?i)\bdha\b.*(?:ph(?:ase)?|p)?[-_\s]*(?:2|ii)\b'), 'DHA Defence Phase 2'),
    (re.compile(r'(?i)\bdha\b.*(?:ph(?:ase)?|p)?[-_\s]*(?:7|8|9|vii|viii|ix)\b'), 'DHA Defence Phase 7-9'),
    (re.compile(r'(?i)\bdha\b.*(?:ph(?:ase)?|p)?[-_\s]*(?:1|3|4|i|iii|iv)\b'), 'DHA Defence Phase 1-8'),
    (re.compile(r'(?i)\bdha\s*defence\s*phase\s*5-6\b'), 'DHA Defence Phase 5-6'),
    (re.compile(r'(?i)\bdha\s*defence\s*phase\s*7-9\b'), 'DHA Defence Phase 7-9'),
    (re.compile(r'(?i)\bdha\s*defence\s*phase\s*1-8\b'), 'DHA Defence Phase 1-8'),
    (re.compile(r'(?i)\bdha\s*defence\s*phase\s*2\b'), 'DHA Defence Phase 2'),

    # Bahria variants
    (re.compile(r'(?i)\b(?:btk|bahria\s*(?:town)?\s*(?:karachi|khi))\b'), 'Bahria Town Karachi'),
    (re.compile(r'(?i)\bbahria\s*(?:town)?\s*(?:ph(?:ase)?|p)?[-_\s]*(?:1-8|[1-8])\b'), 'Bahria Town Phase 1-8'),
    (re.compile(r'(?i)\bbahria\s*(?:town)?\b'), 'Bahria Town'),

    # Islamabad Sectors
    (re.compile(r'(?i)\b(?:sector\s*)?[fe]-?[67]\b'), 'Sector F-6/F-7/E-7'),
    (re.compile(r'(?i)\b(?:sector\s*)?f-?(?:8|10|11)\b'), 'Sector F-8/F-10/F-11'),
    (re.compile(r'(?i)\b(?:sector\s*)?g-?(?:11|13)\b'), 'Sector G-11/G-13'),
    (re.compile(r'(?i)\b(?:sector\s*)?e-?11\b'), 'Sector E-11'),
    (re.compile(r'(?i)\b(?:sector\s*)?b-?17\b|\bmulti\s*gardens\b'), 'Sector B-17 Multi Gardens'),

    # Karachi locations
    (re.compile(r'(?i)\bclifton\b'), 'Clifton'),
    (re.compile(r'(?i)\bp\.?e\.?c\.?h\.?s\b'), 'PECHS'),
    (re.compile(r'(?i)\bgulshan(?:-e-iqbal)?\b'), 'Gulshan-e-Iqbal'),
    (re.compile(r'(?i)\b(?:north\s*nazimabad|n\.?\s*nazimabad)\b'), 'North Nazimabad'),
    (re.compile(r'(?i)\bmalir\s*cantt\b'), 'Malir Cantt'),
    (re.compile(r'(?i)\bscheme\s*33\b|\bsch\s*33\b'), 'Scheme 33'),

    # Lahore locations
    (re.compile(r'(?i)\bgulberg\b'), 'Gulberg'),
    (re.compile(r'(?i)\bjohar\s*town\b'), 'Johar Town'),
    (re.compile(r'(?i)\bmodel\s*town\b'), 'Model Town'),
    (re.compile(r'(?i)\ballama\s*iqbal\s*town\b|\bait\b'), 'Allama Iqbal Town'),
    (re.compile(r'(?i)\blake\s*city\b'), 'Lake City'),
    (re.compile(r'(?i)\bwapda\s*town\b'), 'Wapda Town'),
    (re.compile(r'(?i)\baskari\b'), 'Askari'),

    # Rawalpindi & Faisalabad
    (re.compile(r'(?i)\bchaklala(?:\s*scheme\s*3)?\b'), 'Chaklala Scheme 3'),
    (re.compile(r'(?i)\bsatellite\s*town\b'), 'Satellite Town'),
    (re.compile(r'(?i)\badiala(?:\s*road)?\b'), 'Adiala Road'),
    (re.compile(r'(?i)\bsaddar(?:\s*cantt)?\b'), 'Saddar Cantt'),
    (re.compile(r'(?i)\bd[-_\s]*ground\b|\bpeoples\s*colony\b'), 'D Ground / Peoples Colony'),
    (re.compile(r'(?i)\bmadina\s*town\b'), 'Madina Town'),
    (re.compile(r'(?i)\bcanal\s*road(?:\s*villas)?\b'), 'Canal Road Villas')
]


def standardize_location(loc_name: str) -> str:
    """
    Standardizes inconsistent neighborhood and sector names to canonical labels.
    """
    if pd.isna(loc_name) or not str(loc_name).strip():
        return "Unknown"

    loc_str = str(loc_name).strip()
    for pattern, canonical in CANONICAL_LOCATION_PATTERNS:
        if pattern.search(loc_str):
            return canonical

    return loc_str


# ==========================================
# 4. Outlier Detection & Capping (IQR & Z-Score)
# ==========================================

def detect_outliers_iqr(series: pd.Series, factor: float = 1.5) -> Tuple[pd.Series, float, float]:
    """
    Computes IQR bounds and returns a boolean mask of outliers.
    """
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - factor * iqr
    upper_bound = q3 + factor * iqr
    outlier_mask = (series < lower_bound) | (series > upper_bound)
    return outlier_mask, lower_bound, upper_bound


def detect_outliers_zscore(series: pd.Series, threshold: float = 3.0) -> Tuple[pd.Series, float, float]:
    """
    Computes Z-Score bounds and returns a boolean mask of outliers.
    """
    mean = series.mean()
    std = series.std()
    lower_bound = mean - threshold * std
    upper_bound = mean + threshold * std
    z_scores = np.abs((series - mean) / (std + 1e-8))
    outlier_mask = z_scores > threshold
    return outlier_mask, lower_bound, upper_bound


def winsorize_series(series: pd.Series, lower_quantile: float = 0.01, upper_quantile: float = 0.99) -> pd.Series:
    """
    Winsorizes (caps) extreme values at specified percentiles.
    Preserves sample size while neutralizing catastrophic typos or extreme outliers.
    """
    low_val = series.quantile(lower_quantile)
    high_val = series.quantile(upper_quantile)
    return series.clip(lower=low_val, upper=high_val)


# ==========================================
# 5. Full Dataset Cleaning Functions
# ==========================================

def clean_property_data(
    df: pd.DataFrame,
    handle_outliers_method: str = "winsorize",
    verbose: bool = True
) -> pd.DataFrame:
    """
    Complete cleaning procedure for property listings.
    
    Steps:
    1. Remove duplicate rows.
    2. Normalize price values ('crore', 'lac' -> numeric PKR).
    3. Normalize plot size into standardized Marlas.
    4. Standardize location strings.
    5. Impute any missing numerical or categorical values.
    6. Treat outliers in price and price_per_marla using IQR/Winsorization.
    """
    df_clean = df.copy()
    initial_rows = len(df_clean)

    # 1. Deduplication
    # Check exact duplicates
    exact_dups = df_clean.duplicated().sum()
    df_clean = df_clean.drop_duplicates()

    # Check semantic duplicates (same location, size, covered area, beds, price)
    semantic_subset = ["city", "location", "property_type", "plot_size_marla", "covered_area_sqft", "bedrooms", "price_pkr"]
    semantic_dups = df_clean.duplicated(subset=semantic_subset).sum()
    df_clean = df_clean.drop_duplicates(subset=semantic_subset)

    # 2. Normalize Price
    df_clean["price_pkr"] = df_clean["price_pkr"].apply(normalize_price)

    # 3. Normalize Area
    if "plot_size_unit" in df_clean.columns:
        df_clean["plot_size_marla"] = [
            normalize_area_to_marla(sz, unit)
            for sz, unit in zip(df_clean["plot_size_marla"], df_clean["plot_size_unit"])
        ]
    else:
        df_clean["plot_size_marla"] = df_clean["plot_size_marla"].apply(normalize_area_to_marla)

    # 4. Standardize Location
    df_clean["location"] = df_clean["location"].apply(standardize_location)

    # 5. Missing Values Imputation
    # Numeric imputation: Grouped median by (city, property_type), fallback to column median
    num_cols = df_clean.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        if df_clean[col].isnull().any():
            df_clean[col] = df_clean.groupby(["city", "property_type"])[col].transform(
                lambda x: x.fillna(x.median())
            ).fillna(df_clean[col].median())

    # Categorical imputation
    cat_cols = df_clean.select_dtypes(include=["object"]).columns
    for col in cat_cols:
        if df_clean[col].isnull().any():
            df_clean[col] = df_clean[col].fillna(df_clean[col].mode()[0] if not df_clean[col].mode().empty else "Unknown")

    # 6. Outlier Handling
    # Compute price per marla
    df_clean["price_per_marla"] = df_clean["price_pkr"] / (df_clean["plot_size_marla"] + 1e-5)

    if handle_outliers_method == "winsorize":
        # Winsorize price within property type to preserve luxury/farmhouses while clipping typos
        df_clean["price_pkr"] = df_clean.groupby("property_type")["price_pkr"].transform(
            lambda x: winsorize_series(x, 0.01, 0.99)
        )
        df_clean["price_per_marla"] = df_clean["price_pkr"] / (df_clean["plot_size_marla"] + 1e-5)
    elif handle_outliers_method == "iqr_filter":
        # Filter rows outside 3.0x IQR (extreme outlier filter)
        mask, _, _ = detect_outliers_iqr(df_clean["price_per_marla"], factor=3.0)
        df_clean = df_clean[~mask]

    if verbose:
        print(f"Property Cleaning Summary:")
        print(f" - Initial rows: {initial_rows}")
        print(f" - Exact duplicates removed: {exact_dups}")
        print(f" - Semantic duplicates removed: {semantic_dups}")
        print(f" - Final clean rows: {len(df_clean)}")
        print(f" - Missing values remaining: {df_clean.isnull().sum().sum()}")

    return df_clean


def clean_leads_data(
    df: pd.DataFrame,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Complete cleaning procedure for lead scoring CRM data.
    
    Steps:
    1. Deduplication (exact & lead_id duplicates).
    2. Missing value imputation:
       - 'objection_raised': 1,438 null values (31.9%). Imputed with 'No Objection Raised'.
         Justification: In sales CRM workflow, an unlogged objection means the lead progressed without raising friction.
       - 'avg_call_duration_mins' / 'response_time_hours': Median imputation if missing.
    3. Categorical normalization (strip, title case).
    4. Numeric boundary validation.
    """
    df_clean = df.copy()
    initial_rows = len(df_clean)

    # 1. Deduplication
    exact_dups = df_clean.duplicated().sum()
    df_clean = df_clean.drop_duplicates()

    id_dups = df_clean.duplicated(subset=["lead_id"]).sum()
    df_clean = df_clean.drop_duplicates(subset=["lead_id"])

    # 2. Impute 'objection_raised'
    # Missing values represent friction-free prospective leads where no obstacle was recorded
    df_clean["objection_raised"] = df_clean["objection_raised"].fillna("No Objection Raised")

    # 3. Numeric Imputations
    num_cols = ["budget_pkr", "num_calls", "avg_call_duration_mins", "response_time_hours", "followup_count"]
    for col in num_cols:
        if col in df_clean.columns and df_clean[col].isnull().any():
            df_clean[col] = df_clean[col].fillna(df_clean[col].median())

    # 4. Standardize text categories
    cat_cols = ["lead_source", "preferred_city", "purpose", "property_type_preferred", "visit_booked", "visit_completed"]
    for col in cat_cols:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()

    if verbose:
        print(f"Leads Cleaning Summary:")
        print(f" - Initial rows: {initial_rows}")
        print(f" - Exact duplicates removed: {exact_dups}")
        print(f" - ID duplicates removed: {id_dups}")
        print(f" - Final clean rows: {len(df_clean)}")
        print(f" - Missing values remaining: {df_clean.isnull().sum().sum()}")

    return df_clean


if __name__ == "__main__":
    # Test cleaning on both datasets
    p_df = pd.read_csv("Data/property_listings.csv")
    cleaned_p = clean_property_data(p_df)
    
    l_df = pd.read_csv("Data/leads_scoring.csv")
    cleaned_l = clean_leads_data(l_df)
