"""
Time-Series Analysis Module for ShopKaro Demand Forecasting
Implements Task 1:
1. Category and Product Sales Extraction & Aggregation
2. Trend, Seasonality, and Residual Decomposition (STL / Seasonal Decompose)
3. Weekly, Monthly, and Moving Islamic Festival Effects (Lunar Calendar Shift)
4. Stationarity Testing (Augmented Dickey-Fuller / ADF) & Differencing Analysis
5. Intermittent Demand Analysis: ADI & CV^2 Classification (Syntetos-Boylan Grid) & Croston's Method
"""

import os
import duckdb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
from typing import Dict, List, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "processed", "shopkaro.duckdb")
FIG_DIR = os.path.join(BASE_DIR, "reports", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"


def load_daily_category_sales(con=None) -> pd.DataFrame:
    """Extracts continuous daily sales volume and revenue by category across 2 years."""
    should_close = False
    if con is None:
        con = duckdb.connect(DB_PATH, read_only=True)
        should_close = True
        
    query = """
        WITH date_spine AS (
            SELECT CAST(date AS DATE) as date_val, is_weekend, is_festival, festival_name, demand_multiplier
            FROM calendar
        ),
        cat_spine AS (
            SELECT DISTINCT category FROM products
        ),
        grid AS (
            SELECT d.date_val, c.category, d.is_weekend, d.is_festival, d.festival_name, d.demand_multiplier
            FROM date_spine d
            CROSS JOIN cat_spine c
        ),
        sales AS (
            SELECT 
                e.timestamp::DATE as date_val,
                p.category,
                COUNT(*) as units_sold,
                SUM(p.price_pkr) as revenue_pkr
            FROM events e
            JOIN products p ON e.product_id = p.product_id
            WHERE e.event_type = 'purchase'
            GROUP BY 1, 2
        )
        SELECT 
            g.date_val as date,
            g.category,
            COALESCE(s.units_sold, 0) as units_sold,
            COALESCE(s.revenue_pkr, 0) as revenue_pkr,
            g.is_weekend,
            g.is_festival,
            COALESCE(g.festival_name, 'Normal Day') as festival_name,
            g.demand_multiplier
        FROM grid g
        LEFT JOIN sales s ON g.date_val = s.date_val AND g.category = s.category
        ORDER BY g.date_val, g.category
    """
    df = con.execute(query).df()
    df["date"] = pd.to_datetime(df["date"])
    if should_close:
        con.close()
    return df


def load_daily_product_sales(product_ids: List[str] = None, con=None) -> pd.DataFrame:
    """Extracts continuous daily sales for specified or top products."""
    should_close = False
    if con is None:
        con = duckdb.connect(DB_PATH, read_only=True)
        should_close = True
        
    if product_ids is None:
        # Default to top 5 fast movers + 5 intermittent movers
        top_fast = con.execute("""
            SELECT p.product_id
            FROM products p
            JOIN events e ON p.product_id = e.product_id AND e.event_type = 'purchase'
            GROUP BY p.product_id
            ORDER BY COUNT(*) DESC
            LIMIT 5
        """).df()["product_id"].tolist()
        
        intermittent = con.execute("""
            SELECT p.product_id
            FROM products p
            JOIN events e ON p.product_id = e.product_id AND e.event_type = 'purchase'
            GROUP BY p.product_id
            HAVING COUNT(*) BETWEEN 4 AND 12
            LIMIT 5
        """).df()["product_id"].tolist()
        product_ids = top_fast + intermittent
        
    pids_str = ", ".join([f"'{p}'" for p in product_ids])
    query = f"""
        WITH date_spine AS (
            SELECT CAST(date AS DATE) as date_val, is_weekend, is_festival, festival_name
            FROM calendar
        ),
        target_prods AS (
            SELECT product_id, title, category, price_pkr, stock_quantity
            FROM products
            WHERE product_id IN ({pids_str})
        ),
        grid AS (
            SELECT d.date_val, p.product_id, p.title, p.category, p.price_pkr, p.stock_quantity,
                   d.is_weekend, d.is_festival, d.festival_name
            FROM date_spine d
            CROSS JOIN target_prods p
        ),
        sales AS (
            SELECT 
                timestamp::DATE as date_val,
                product_id,
                COUNT(*) as units_sold
            FROM events
            WHERE event_type = 'purchase' AND product_id IN ({pids_str})
            GROUP BY 1, 2
        )
        SELECT 
            g.date_val as date,
            g.product_id,
            g.title,
            g.category,
            g.price_pkr,
            g.stock_quantity,
            COALESCE(s.units_sold, 0) as units_sold,
            g.is_weekend,
            g.is_festival,
            COALESCE(g.festival_name, 'Normal Day') as festival_name
        FROM grid g
        LEFT JOIN sales s ON g.date_val = s.date_val AND g.product_id = s.product_id
        ORDER BY g.product_id, g.date_val
    """
    df = con.execute(query).df()
    df["date"] = pd.to_datetime(df["date"])
    if should_close:
        con.close()
    return df


def perform_decomposition(cat_df: pd.DataFrame, category: str = "Fashion") -> Dict:
    """Performs additive time-series decomposition into trend, seasonality, and residual."""
    subset = cat_df[cat_df["category"] == category].sort_values("date").set_index("date")
    ts = subset["units_sold"].asfreq("D").fillna(0)
    
    # 7-day weekly decomposition
    decomp_7 = seasonal_decompose(ts, model="additive", period=7)
    
    # Yearly decomposition (period=365)
    decomp_365 = seasonal_decompose(ts, model="additive", period=365)
    
    # Plot decomposition
    fig, axes = plt.subplots(4, 1, figsize=(14, 9), sharex=True)
    fig.suptitle(f"Time-Series Decomposition for {category} (Weekly Seasonality Period = 7 Days)", 
                 fontsize=14, fontweight="bold", y=0.98)
    
    decomp_7.observed.plot(ax=axes[0], color="#1f77b4", lw=1.2)
    axes[0].set_ylabel("Observed Units", fontsize=10, fontweight="bold")
    axes[0].grid(True, alpha=0.3)
    
    decomp_7.trend.plot(ax=axes[1], color="#ff7f0e", lw=2)
    axes[1].set_ylabel("Trend Component", fontsize=10, fontweight="bold")
    axes[1].grid(True, alpha=0.3)
    
    decomp_7.seasonal.plot(ax=axes[2], color="#2ca02c", lw=1.2)
    axes[2].set_ylabel("Weekly Seasonality", fontsize=10, fontweight="bold")
    axes[2].grid(True, alpha=0.3)
    
    decomp_7.resid.plot(ax=axes[3], color="#d62728", lw=0.8, alpha=0.8)
    axes[3].axhline(0, color="black", linestyle="--", alpha=0.5)
    axes[3].set_ylabel("Residuals", fontsize=10, fontweight="bold")
    axes[3].set_xlabel("Date", fontsize=11, fontweight="bold")
    axes[3].grid(True, alpha=0.3)
    
    plt.tight_layout()
    decomp_fig_path = os.path.join(FIG_DIR, "time_series_decomposition.png")
    fig.savefig(decomp_fig_path, dpi=200)
    plt.close(fig)
    
    return {
        "category": category,
        "mean_observed": float(ts.mean()),
        "trend_min": float(decomp_7.trend.dropna().min()),
        "trend_max": float(decomp_7.trend.dropna().max()),
        "seasonal_amplitude": float(decomp_7.seasonal.max() - decomp_7.seasonal.min()),
        "residual_std": float(decomp_7.resid.dropna().std())
    }


def analyze_weekly_and_festival_effects(cat_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Analyzes day-of-week patterns and festival impact across categories."""
    df = cat_df.copy()
    df["day_name"] = df["date"].dt.day_name()
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Weekly seasonality
    weekly_agg = df.groupby(["day_name", "category"])["units_sold"].mean().reset_index()
    weekly_agg["day_name"] = pd.Categorical(weekly_agg["day_name"], categories=day_order, ordered=True)
    weekly_pivot = weekly_agg.pivot(index="day_name", columns="category", values="units_sold")
    
    # Festival effects
    festival_agg = df[df["is_festival"]].groupby(["festival_name", "category"])["units_sold"].mean().reset_index()
    normal_agg = df[~df["is_festival"]].groupby("category")["units_sold"].mean().to_dict()
    
    festival_agg["normal_baseline"] = festival_agg["category"].map(normal_agg)
    festival_agg["uplift_pct"] = ((festival_agg["units_sold"] - festival_agg["normal_baseline"]) / festival_agg["normal_baseline"]) * 100
    
    # Plot weekly seasonality & festival uplift
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    sns.lineplot(data=weekly_agg.sort_values("day_name"), x="day_name", y="units_sold", 
                 hue="category", marker="o", ax=ax1, lw=2)
    ax1.set_title("Weekly Demand Pattern (Weekend & Friday Night Surge)", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Day of Week", fontsize=10, fontweight="bold")
    ax1.set_ylabel("Average Daily Units Sold", fontsize=10, fontweight="bold")
    ax1.tick_params(axis="x", rotation=30)
    ax1.grid(True, alpha=0.3)
    
    # Top festival uplifts for Fashion & Electronics
    fest_sub = festival_agg[festival_agg["category"].isin(["Fashion", "Electronics"])].sort_values("uplift_pct", ascending=False)
    sns.barplot(data=fest_sub, x="uplift_pct", y="festival_name", hue="category", ax=ax2, palette="viridis")
    ax2.set_title("Retail Festival Demand Uplift (% Increase vs. Non-Festival Baseline)", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Demand Uplift (%)", fontsize=10, fontweight="bold")
    ax2.set_ylabel("Festival Retail Event", fontsize=10, fontweight="bold")
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    fest_fig_path = os.path.join(FIG_DIR, "weekly_festival_seasonality.png")
    fig.savefig(fest_fig_path, dpi=200)
    plt.close(fig)
    
    return weekly_pivot, festival_agg


def perform_adf_stationarity_tests(cat_df: pd.DataFrame) -> pd.DataFrame:
    """
    Executes Augmented Dickey-Fuller (ADF) tests on raw series and first-order / seasonal differences.
    H0 (Null Hypothesis): The series has a unit root (is non-stationary).
    p-value < 0.05 rejects H0, confirming stationarity.
    """
    results = []
    categories = cat_df["category"].unique()
    
    for cat in sorted(categories):
        sub = cat_df[cat_df["category"] == cat].sort_values("date")
        y_raw = sub["units_sold"].values
        y_diff1 = np.diff(y_raw)
        y_diff7 = y_raw[7:] - y_raw[:-7]
        
        # Raw series ADF
        adf_raw = adfuller(y_raw, autolag="AIC")
        # First difference ADF
        adf_diff1 = adfuller(y_diff1, autolag="AIC")
        # Seasonal (7-day) difference ADF
        adf_diff7 = adfuller(y_diff7, autolag="AIC")
        
        results.append({
            "Category": cat,
            "Raw ADF Stat": round(adf_raw[0], 4),
            "Raw p-value": round(adf_raw[1], 4),
            "Raw Stationary": "Stationary" if adf_raw[1] < 0.05 else "Non-Stationary",
            "Diff(1) ADF Stat": round(adf_diff1[0], 4),
            "Diff(1) p-value": round(adf_diff1[1], 4),
            "Diff(1) Stationary": "Stationary" if adf_diff1[1] < 0.05 else "Non-Stationary",
            "Diff(7) ADF Stat": round(adf_diff7[0], 4),
            "Diff(7) p-value": round(adf_diff7[1], 4)
        })
        
    df_adf = pd.DataFrame(results)
    return df_adf


def analyze_intermittent_demand(prod_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Classifies products according to the Syntetos-Boylan-Croston (SBC) grid:
    - Average Demand Interval (ADI): Average number of periods between non-zero demand.
      Threshold: ADI = 1.32
    - Squared Coefficient of Variation (CV^2): Var(non_zero_demand) / Mean(non_zero_demand)^2
      Threshold: CV^2 = 0.49
    
    Categories:
    1. Smooth: ADI < 1.32 & CV^2 < 0.49 (Regular timing, consistent volume)
    2. Intermittent: ADI >= 1.32 & CV^2 < 0.49 (Sporadic timing, consistent volume)
    3. Erratic: ADI < 1.32 & CV^2 >= 0.49 (Regular timing, volatile volume)
    4. Lumpy: ADI >= 1.32 & CV^2 >= 0.49 (Sporadic timing, volatile volume)
    """
    metrics = []
    
    for pid, group in prod_df.groupby("product_id"):
        title = group["title"].iloc[0]
        category = group["category"].iloc[0]
        price = group["price_pkr"].iloc[0]
        y = group.sort_values("date")["units_sold"].values
        
        non_zeros = y[y > 0]
        n_periods = len(y)
        n_non_zero = len(non_zeros)
        
        if n_non_zero < 2:
            adi = float(n_periods)
            cv2 = 1.0
        else:
            # ADI = total periods / number of non-zero demand events
            adi = n_periods / n_non_zero
            mean_nz = np.mean(non_zeros)
            std_nz = np.std(non_zeros)
            cv2 = (std_nz / mean_nz) ** 2 if mean_nz > 0 else 0.0
            
        # SBC Classification
        if adi < 1.32 and cv2 < 0.49:
            pattern = "Smooth"
            recommended_model = "ARIMA / ETS / LightGBM"
        elif adi >= 1.32 and cv2 < 0.49:
            pattern = "Intermittent"
            recommended_model = "Croston's Method"
        elif adi < 1.32 and cv2 >= 0.49:
            pattern = "Erratic"
            recommended_model = "Quantile Reg / Neural"
        else:
            pattern = "Lumpy"
            recommended_model = "Syntetos-Boylan (SBA) / Bootstrap"
            
        metrics.append({
            "product_id": pid,
            "title": title[:30] + "...",
            "category": category,
            "price_pkr": price,
            "total_sales": int(np.sum(y)),
            "active_days": int(n_non_zero),
            "ADI": round(float(adi), 2),
            "CV2": round(float(cv2), 3),
            "Pattern": pattern,
            "Recommended_Model": recommended_model
        })
        
    df_sbc = pd.DataFrame(metrics)
    
    # Plot SBC Intermittent Demand Classification
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Color palette
    colors = {"Smooth": "#2ca02c", "Intermittent": "#1f77b4", "Erratic": "#ff7f0e", "Lumpy": "#d62728"}
    
    for pat, color in colors.items():
        sub = df_sbc[df_sbc["Pattern"] == pat]
        if not sub.empty:
            ax.scatter(sub["ADI"], sub["CV2"], c=color, label=f"{pat} ({len(sub)} SKUs)", s=80, alpha=0.85, edgecolors="#333333")
            
    # Draw SBC cutoff boundary lines
    ax.axvline(1.32, color="gray", linestyle="--", lw=1.5, alpha=0.8)
    ax.axhline(0.49, color="gray", linestyle="--", lw=1.5, alpha=0.8)
    
    ax.text(0.5, 0.15, "SMOOTH\n(ARIMA/ETS)", fontsize=11, fontweight="bold", color="#2ca02c", alpha=0.7)
    ax.text(2.5, 0.15, "INTERMITTENT\n(Croston)", fontsize=11, fontweight="bold", color="#1f77b4", alpha=0.7)
    ax.text(0.5, 1.2, "ERRATIC\n(Quantile)", fontsize=11, fontweight="bold", color="#ff7f0e", alpha=0.7)
    ax.text(2.5, 1.2, "LUMPY\n(SBA)", fontsize=11, fontweight="bold", color="#d62728", alpha=0.7)
    
    ax.set_title("Syntetos-Boylan-Croston (SBC) Demand Categorization Grid", fontsize=13, fontweight="bold")
    ax.set_xlabel("Average Demand Interval (ADI) — Threshold = 1.32", fontsize=11, fontweight="bold")
    ax.set_ylabel("Squared Coefficient of Variation (CV²) — Threshold = 0.49", fontsize=11, fontweight="bold")
    ax.legend(frameon=True, facecolor="white", loc="upper right")
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    sbc_fig_path = os.path.join(FIG_DIR, "intermittent_demand_matrix.png")
    fig.savefig(sbc_fig_path, dpi=200)
    plt.close(fig)
    
    # Calculate Croston & SBA forecasts for intermittent products
    croston_results = []
    for pid, group in prod_df.groupby("product_id"):
        y = group.sort_values("date")["units_sold"].values
        fc_croston, fc_sba = croston_forecast(y, alpha=0.1)
        croston_results.append({
            "product_id": pid,
            "Last_Croston_Forecast": round(fc_croston, 3),
            "Last_SBA_Forecast": round(fc_sba, 3)
        })
    df_croston = pd.DataFrame(croston_results)
    
    return df_sbc, df_croston


def croston_forecast(y: np.ndarray, alpha: float = 0.1) -> Tuple[float, float]:
    """
    Croston's Method and Syntetos-Boylan Approximation (SBA) for intermittent demand:
    Decomposes intermittent series into demand size (z_t) and inter-arrival time (p_t).
    
    Updates when demand occurs (y_t > 0):
      z_t = alpha * y_t + (1 - alpha) * z_{t-1}
      p_t = alpha * q + (1 - alpha) * p_{t-1}
    where q is elapsed time since last non-zero demand.
    
    Forecast:
      Croston = z_t / p_t
      SBA = (1 - alpha / 2) * (z_t / p_t)
    """
    non_zeros = y[y > 0]
    if len(non_zeros) == 0:
        return 0.0, 0.0
        
    z = float(non_zeros[0]) # initial demand size
    p = 1.0                # initial inter-arrival interval
    q = 1                  # periods since last non-zero demand
    
    for t in range(1, len(y)):
        if y[t] > 0:
            z = alpha * y[t] + (1 - alpha) * z
            p = alpha * q + (1 - alpha) * p
            q = 1
        else:
            q += 1
            
    croston_fc = z / p if p > 0 else 0.0
    sba_fc = (1.0 - alpha / 2.0) * croston_fc
    return float(croston_fc), float(sba_fc)


def run_time_series_analysis():
    print("="*75)
    print("   TASK 1: SHOPKARO TIME-SERIES & INTERMITTENT DEMAND ANALYSIS")
    print("="*75)
    
    con = duckdb.connect(DB_PATH, read_only=True)
    cat_df = load_daily_category_sales(con)
    prod_df = load_daily_product_sales(con=con)
    con.close()
    
    print(f"Extracted {len(cat_df):,} daily category records across 5 retail categories.")
    print(f"Extracted continuous 731-day sales history for sample products across volume tiers.")
    
    # 1. Decomposition
    print("\n[1/4] Performing Time-Series Decomposition (Fashion Category)...")
    decomp_stats = perform_decomposition(cat_df, category="Fashion")
    print(f" - Mean Daily Volume: {decomp_stats['mean_observed']:.2f} units")
    print(f" - Weekly Seasonality Amplitude: {decomp_stats['seasonal_amplitude']:.2f} units")
    print(f" - Trend Range: {decomp_stats['trend_min']:.2f} to {decomp_stats['trend_max']:.2f} units")
    print(" -> Saved decomposition visualization to 'reports/figures/time_series_decomposition.png'")
    
    # 2. Seasonality & Festivals
    print("\n[2/4] Analyzing Weekly & Moving Islamic Festival Seasonality...")
    weekly_pivot, festival_agg = analyze_weekly_and_festival_effects(cat_df)
    print("Weekly Average Sales by Category:")
    print(weekly_pivot.round(2))
    print("\nKey Festival Uplifts:")
    for _, r in festival_agg[festival_agg["category"].isin(["Fashion", "Electronics"])].head(6).iterrows():
        print(f" - [{r['category']}] {r['festival_name']:30s}: {r['units_sold']:.1f} units/day ({r['uplift_pct']:+.1f}% vs baseline)")
    print(" -> Saved weekly & festival dynamics to 'reports/figures/weekly_festival_seasonality.png'")
    
    # 3. Stationarity Tests
    print("\n[3/4] Running Augmented Dickey-Fuller (ADF) Stationarity Tests...")
    df_adf = perform_adf_stationarity_tests(cat_df)
    print(df_adf.to_string(index=False))
    
    # 4. Intermittent Demand Analysis
    print("\n[4/4] Conducting Intermittent Demand SBC Classification & Croston Modeling...")
    df_sbc, df_croston = analyze_intermittent_demand(prod_df)
    merged_sbc = pd.merge(df_sbc, df_croston, on="product_id")
    print(merged_sbc[["product_id", "title", "total_sales", "ADI", "CV2", "Pattern", "Last_Croston_Forecast"]].to_string(index=False))
    print(" -> Saved SBC categorization grid to 'reports/figures/intermittent_demand_matrix.png'")
    
    print("\n[SUCCESS] Task 1 completed.")
    return cat_df, prod_df, df_adf, merged_sbc


if __name__ == "__main__":
    run_time_series_analysis()

