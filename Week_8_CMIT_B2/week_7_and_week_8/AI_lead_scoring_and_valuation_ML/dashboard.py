"""
dashboard.py
============
Day 4 - Task 3: Streamlit Interactive Web Application for Pakistan Real Estate AI.

Tabs:
1. 🏡 Property Valuation & Investment Verdict Engine
2. 🎯 Inbound Lead Prioritization & Scoring Inbox
3. 🔍 SHAP Explainability Studio & Agent Talking Points
4. 📊 Pakistan Real Estate Market Analytics (Day 1 Insights)
5. 💬 AI Real Estate Advisor Chat (LangGraph UrduLish Assistant)
"""

import os
import sys
import json
import time
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configure page layout and title
st.set_page_config(
    page_title="Pakistan Real Estate AI & Valuation Platform",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from serving_api import ModelArtifacts, PropertyInput, LeadInput, prepare_property_df, prepare_lead_df
from src.feature_engineering import OBJECTION_SEVERITY_MAP
from src.valuation_models import format_crore_lakh
from ai_assistant import chat_with_assistant, comparable_properties, market_stats


# ========================================================
# Custom CSS for Modern, Premium Dark-Mode Aesthetics
# ========================================================
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    /* Header Gradient */
    .hero-banner {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 24px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    
    /* Cards and Glassmorphism */
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        backdrop-filter: blur(10px);
        margin-bottom: 15px;
    }
    
    .verdict-box {
        padding: 18px 24px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 1.25rem;
        text-align: center;
        margin: 15px 0;
        letter-spacing: 0.5px;
    }
    .verdict-underpriced {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid #10b981;
        color: #34d399;
    }
    .verdict-fair {
        background: rgba(59, 130, 246, 0.15);
        border: 1px solid #3b82f6;
        color: #60a5fa;
    }
    .verdict-overpriced {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid #ef4444;
        color: #f87171;
    }
    
    /* Badges */
    .badge-hot {
        background-color: #ef4444;
        color: white;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .badge-warm {
        background-color: #f59e0b;
        color: white;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .badge-cold {
        background-color: #3b82f6;
        color: white;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(30, 41, 59, 0.5);
        border-radius: 8px 8px 0 0;
        border: 1px solid rgba(255, 255, 255, 0.05);
        color: #94a3b8;
        font-weight: 600;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e293b !important;
        color: #38bdf8 !important;
        border-bottom: 2px solid #38bdf8 !important;
    }
</style>
""", unsafe_allow_html=True)


# ========================================================
# Cached Data & Model Loaders
# ========================================================
@st.cache_resource
def get_artifacts():
    return ModelArtifacts.get_instance()

@st.cache_data
def load_datasets():
    prop_path = os.path.join(BASE_DIR, "data_cleaned", "property_listings_cleaned.csv")
    lead_path = os.path.join(BASE_DIR, "data_cleaned", "leads_scoring_cleaned.csv")
    df_p = pd.read_csv(prop_path) if os.path.exists(prop_path) else pd.DataFrame()
    df_l = pd.read_csv(lead_path) if os.path.exists(lead_path) else pd.DataFrame()
    return df_p, df_l

def load_crm_leads():
    """Connects directly to the Voice Agent SQLite database to fetch live caller leads."""
    db_candidates = [
        os.path.join(BASE_DIR, "real_estate.db"),
        os.path.abspath(os.path.join(BASE_DIR, "..", "real_estate_voice_agent", "real_estate.db"))
    ]
    db_path = next((p for p in db_candidates if os.path.exists(p)), None)
    if db_path and os.path.exists(db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        try:
            df = pd.read_sql_query("SELECT * FROM crm_client_preferences ORDER BY lead_score_pct DESC", conn)
            return df
        except Exception as e:
            st.error(f"Error querying Voice Agent DB: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

artifacts = get_artifacts()
df_prop, df_leads = load_datasets()


# ========================================================
# Sidebar Overview
# ========================================================
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/real-estate.png", width=70)
    st.title("EstateAI Pakistan")
    st.caption("Week 8 • Enterprise AI & ML Serving Engine")
    st.markdown("---")
    
    st.subheader("Model Status")
    st.success("🟢 Valuation Engine: Active (80% CI)")
    st.success("🟢 Lead Scorer: Active (Optimal p*=0.35)")
    st.info(f"Test MAE: {artifacts.metadata['property_valuation']['metrics']['MAE_formatted']}")
    st.info(f"Lead ROC-AUC: {artifacts.metadata['lead_scoring']['metrics']['ROC_AUC']}")

    st.markdown("---")
    st.subheader("Coverage")
    st.write(f"• Cities: {', '.join(artifacts.supported_cities[:4])}")
    st.write(f"• Active Comps: {len(df_prop):,} listings")
    st.write(f"• Lead Records: {len(df_leads):,} profiles")


# ========================================================
# Hero Header
# ========================================================
st.markdown("""
<div class="hero-banner">
    <h1 style="margin:0; font-size:2.2rem; font-weight:800; background:linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Pakistan Real Estate AI Valuation & Lead Scoring Platform
    </h1>
    <p style="margin:8px 0 0 0; color:#94a3b8; font-size:1.05rem;">
        Enterprise Machine Learning serving for property appraisals, quantile risk intervals, conversion scoring, and UrduLish voice agent intelligence.
    </p>
</div>
""", unsafe_allow_html=True)


# ========================================================
# Main Tabs
# ========================================================
tab_val, tab_leads, tab_shap, tab_analytics, tab_chat, tab_mlops = st.tabs([
    "🏡 Property Valuation",
    "🎯 Lead Scoring & Inbox",
    "🔍 SHAP Explainability",
    "📊 Market Insights",
    "💬 AI Assistant (UrduLish)",
    "📡 MLOps & Drift Lifecycle"
])


# ========================================================
# TAB 1: Property Valuation Engine
# ========================================================
with tab_val:
    st.subheader("Automated Property Valuation & Quantile Range Engine")
    st.caption("Accurately values residential and commercial assets with 80% confidence interval and automated investment verdicts.")

    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        with st.form("valuation_form"):
            st.markdown("#### Property Specifications")
            col1, col2 = st.columns(2)
            with col1:
                city = st.selectbox("Metropolitan City", artifacts.supported_cities, index=0)
                plot_size_marla = st.number_input("Plot Size (Marla)", min_value=1.0, max_value=200.0, value=20.0, step=0.5)
                bedrooms = st.slider("Bedrooms", 1, 10, 5)
                bathrooms = st.slider("Bathrooms", 1, 10, 6)
            with col2:
                # Filter locations by city if available
                city_locs = df_prop[df_prop["city"] == city]["location"].dropna().unique().tolist() if not df_prop.empty else artifacts.supported_locations
                loc_list = sorted(city_locs) if city_locs else ["DHA Phase 6", "Bahria Town", "Gulshan-e-Iqbal", "F-7"]
                location = st.selectbox("Society / Location", loc_list, index=0)
                property_type = st.selectbox("Property Type", ["House", "Flat", "Upper Portion", "Lower Portion", "Farm House"], index=0)
                age_years = st.number_input("Age of Structure (Years)", min_value=0.0, max_value=60.0, value=3.0, step=0.5)
                covered_area_sqft = st.number_input("Covered Area (Sq Ft)", min_value=200.0, max_value=25000.0, value=float(plot_size_marla * 225 * 1.05), step=100.0)

            st.markdown("#### Prime Orientation & Features")
            col3, col4, col5 = st.columns(3)
            with col3:
                is_corner = st.checkbox("Corner Plot", value=True)
            with col4:
                is_park = st.checkbox("Park Facing", value=False)
            with col5:
                is_boulevard = st.checkbox("Main Boulevard", value=False)

            amenities = st.text_input("Amenities List", value="24/7 security;gated community;backup generator / solar;servant quarter")

            st.markdown("#### Investment Verdict (Optional)")
            listed_price_crore = st.number_input("Seller Asking Price (Crore PKR, optional)", min_value=0.0, max_value=100.0, value=8.2, step=0.1)

            submit_val = st.form_submit_button("🚀 Compute Real Estate Valuation", width="stretch")

    with col_out:
        if submit_val or "val_result" not in st.session_state:
            # Construct PropertyInput
            ask_pkr = listed_price_crore * 1e7 if listed_price_crore > 0 else None
            prop_req = PropertyInput(
                plot_size_marla=plot_size_marla,
                covered_area_sqft=covered_area_sqft,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                age_years=age_years,
                city=city,
                location=location,
                property_type=property_type,
                is_corner=1 if is_corner else 0,
                is_park_facing=1 if is_park else 0,
                is_main_boulevard=1 if is_boulevard else 0,
                amenities=amenities,
                listed_price_pkr=ask_pkr
            )
            df_feat = prepare_property_df(prop_req)
            X_proc = artifacts.val_pipeline.transform(df_feat)
            p_mid, p_low, p_high = artifacts.val_engine.predict_range(X_proc)

            st.session_state["val_result"] = {
                "mid": float(p_mid[0]),
                "low": float(p_low[0]),
                "high": float(p_high[0]),
                "ask": ask_pkr,
                "prop_req": prop_req,
                "df_feat": df_feat,
                "X_proc": X_proc
            }

        res = st.session_state["val_result"]
        p_mid, p_low, p_high, ask = res["mid"], res["low"], res["high"], res["ask"]

        st.markdown(f"### Appraisal Result: {location}, {city}")
        
        # Display Metrics
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Fair Market Value", format_crore_lakh(p_mid))
        with m2:
            st.metric("80% Lower Bound (P10)", format_crore_lakh(p_low))
        with m3:
            st.metric("80% Upper Bound (P90)", format_crore_lakh(p_high))

        # Verdict Badge
        if ask:
            if ask < p_low:
                v_class = "verdict-underpriced"
                v_text = "🟢 UNDERPRICED (EXCELLENT BARGAIN)"
                narrative = f"Asking price is {((p_mid - ask)/p_mid)*100:.1f}% below fair market median. Motivated seller or prime investment deal."
            elif ask > p_high:
                v_class = "verdict-overpriced"
                v_text = "🔴 OVERPRICED (AGGRESSIVE PREMIUM)"
                narrative = f"Asking price is {((ask - p_mid)/p_mid)*100:.1f}% above fair market median. Recommend aggressive counter-offer."
            else:
                v_class = "verdict-fair"
                v_text = "🟡 FAIR MARKET TRADING PRICE"
                narrative = "Asking price is well-calibrated within normal 80% trading boundaries."

            st.markdown(f"""
            <div class="verdict-box {v_class}">
                {v_text}<br>
                <span style="font-size:0.95rem; font-weight:400;">{narrative}</span>
            </div>
            """, unsafe_allow_html=True)

        # Plotly Range Gauge Visualizer
        fig_range = go.Figure()
        fig_range.add_trace(go.Bar(
            y=["Valuation Range"],
            x=[(p_high - p_low)/1e7],
            base=[p_low/1e7],
            orientation="h",
            marker=dict(color="rgba(56, 189, 248, 0.4)", line=dict(color="#38bdf8", width=2)),
            name="80% Trading Range"
        ))
        fig_range.add_trace(go.Scatter(
            y=["Valuation Range"],
            x=[p_mid/1e7],
            mode="markers+text",
            marker=dict(color="#38bdf8", size=18, symbol="diamond"),
            text=[f"Fair: {format_crore_lakh(p_mid)}"],
            textposition="top center",
            name="Fair Valuation (Median)"
        ))
        if ask:
            fig_range.add_trace(go.Scatter(
                y=["Valuation Range"],
                x=[ask/1e7],
                mode="markers+text",
                marker=dict(color="#f43f5e" if ask > p_high else "#10b981", size=18, symbol="circle"),
                text=[f"Ask: {format_crore_lakh(ask)}"],
                textposition="bottom center",
                name="Asking Price"
            ))

        fig_range.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=200,
            margin=dict(l=10, r=10, t=30, b=30),
            xaxis_title="Property Price (Crore PKR)",
            showlegend=True
        )
        st.plotly_chart(fig_range, width="stretch")


# ========================================================
# TAB 2: Lead Scoring & Priority Inbox
# ========================================================
with tab_leads:
    st.subheader("Inbound Sales Lead Prioritization & Scoring Inbox")
    st.caption("Prioritizes buyers by predicted closing probability. Top 20% leads capture >60% of all closed transactions.")

    sub_crm, sub_t1, sub_t2 = st.tabs(["📞 Voice Agent CRM Live Leads", "📥 Portal Historical Leads", "⚡ Single Lead Scorer Form"])

    with sub_crm:
        st.markdown("#### Live Calls & Inquiries from Voice Agent (`real_estate.db`)")
        df_crm = load_crm_leads()

        if not df_crm.empty:
            hot_count = int((df_crm["priority_tier"].str.contains("Hot", na=False)).sum())
            warm_count = int((df_crm["priority_tier"].str.contains("Warm", na=False)).sum())
            cold_count = int((df_crm["priority_tier"].str.contains("Cold", na=False)).sum())

            # Top KPI metrics
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            with kpi1:
                st.metric("Total CRM Prospects", len(df_crm))
            with kpi2:
                st.metric("🔥 Hot (Action Now)", hot_count)
            with kpi3:
                st.metric("🌤 Warm (Nurture)", warm_count)
            with kpi4:
                st.metric("❄️ Cold (Drip)", cold_count)

            # Format Budget
            df_crm["Budget_Formatted"] = df_crm["max_budget_pkr"].apply(lambda v: format_crore_lakh(v) if pd.notnull(v) and v > 0 else "Flexible")

            # Filters
            cf1, cf2 = st.columns(2)
            with cf1:
                cities_opt = ["All"] + sorted([c for c in df_crm["preferred_city"].dropna().unique() if c])
                chosen_city = st.selectbox("Filter City", cities_opt, index=0)
            with cf2:
                tiers_opt = ["All", "Hot", "Warm", "Cold"]
                chosen_tier = st.selectbox("Filter Priority Tier", tiers_opt, index=0)

            filtered_crm = df_crm.copy()
            if chosen_city != "All":
                filtered_crm = filtered_crm[filtered_crm["preferred_city"] == chosen_city]
            if chosen_tier != "All":
                filtered_crm = filtered_crm[filtered_crm["priority_tier"].str.contains(chosen_tier, na=False)]

            display_cols = [
                "client_email", "preferred_city", "Budget_Formatted", "property_type",
                "lead_source", "num_calls", "objection_raised", "visit_booked",
                "lead_score_pct", "priority_tier", "recommended_action"
            ]
            valid_cols = [c for c in display_cols if c in filtered_crm.columns]

            st.dataframe(
                filtered_crm[valid_cols],
                column_config={
                    "lead_score_pct": st.column_config.ProgressColumn("Conversion Likelihood", format="%.1f%%", min_value=0, max_value=100),
                    "Budget_Formatted": "Budget (PKR)",
                    "priority_tier": "Priority Status",
                    "client_email": "Prospect Email",
                    "recommended_action": "Prescribed Sales Action"
                },
                width="stretch",
                height=420
            )

            if st.button("🔄 Refresh Live Voice Agent CRM Data"):
                st.rerun()
        else:
            st.info("No CRM leads found in `real_estate.db`. Make a call via Voice Agent or run seeding script.")

    with sub_t1:
        if not df_leads.empty:
            # Score sample of leads for interactive table
            df_disp = df_leads.head(100).copy()
            
            # Predict probabilities
            X_leads_proc = artifacts.lead_pipeline.transform(df_disp)
            probs = artifacts.lead_model.predict_proba(X_leads_proc)[:, 1]
            df_disp["Conversion_Score"] = np.round(probs * 100, 1)

            hot_thresh = artifacts.metadata["lead_scoring"]["hot_threshold"]
            warm_thresh = artifacts.metadata["lead_scoring"]["warm_threshold"]

            def get_tier(p):
                if p >= hot_thresh * 100:
                    return "🔥 Hot"
                elif p >= warm_thresh * 100:
                    return "🌤 Warm"
                else:
                    return "❄️ Cold"

            df_disp["Priority_Tier"] = df_disp["Conversion_Score"].apply(get_tier)
            df_disp["Budget_Formatted"] = df_disp["budget_pkr"].apply(format_crore_lakh)

            # Filters
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                sel_city = st.multiselect("Filter by City", options=df_disp["preferred_city"].unique().tolist(), default=df_disp["preferred_city"].unique().tolist())
            with f_col2:
                sel_tier = st.multiselect("Filter by Priority Tier", options=["🔥 Hot", "🌤 Warm", "❄️ Cold"], default=["🔥 Hot", "🌤 Warm", "❄️ Cold"])
            with f_col3:
                sort_order = st.selectbox("Sort By", ["Highest Conversion Score", "Highest Budget"], index=0)

            filtered = df_disp[(df_disp["preferred_city"].isin(sel_city)) & (df_disp["Priority_Tier"].isin(sel_tier))]
            if sort_order == "Highest Conversion Score":
                filtered = filtered.sort_values(by="Conversion_Score", ascending=False)
            else:
                filtered = filtered.sort_values(by="budget_pkr", ascending=False)

            st.write(f"Showing **{len(filtered)}** prioritized leads matching filters:")
            
            # Display Clean Table
            show_cols = ["lead_id", "preferred_city", "Budget_Formatted", "num_calls", "lead_source", "visit_booked", "visit_completed", "Conversion_Score", "Priority_Tier"]
            st.dataframe(
                filtered[show_cols],
                column_config={
                    "Conversion_Score": st.column_config.ProgressColumn("Conversion Likelihood", format="%f%%", min_value=0, max_value=100),
                    "Budget_Formatted": "Budget (PKR)",
                    "Priority_Tier": "Priority Status"
                },
                width="stretch",
                height=400
            )

    with sub_t2:
        with st.form("single_lead_form"):
            st.markdown("#### Evaluate Inbound Lead Profile")
            c1, c2, c3 = st.columns(3)
            with c1:
                lead_budget_cr = st.number_input("Client Budget (Crore PKR)", min_value=0.2, max_value=80.0, value=5.5, step=0.1)
                l_city = st.selectbox("Target City", artifacts.supported_cities, index=0)
                l_source = st.selectbox("Lead Source", ["Zameen.com", "Facebook Ads", "Instagram Ads", "Referral", "Walk-in"], index=0)
            with c2:
                num_calls = st.slider("Phone Calls Conducted", 0, 15, 4)
                call_dur = st.slider("Avg Call Duration (Mins)", 1.0, 30.0, 8.5)
                days_contact = st.number_input("Days Since Inquiry", 1.0, 180.0, 10.0)
            with c3:
                v_booked = st.selectbox("Site Visit Booked?", ["Yes", "No"], index=0)
                v_completed = st.selectbox("Site Visit Completed?", ["Yes", "No"], index=0)
                objection = st.selectbox("Primary Client Objection", list(OBJECTION_SEVERITY_MAP.keys()), index=0)

            score_btn = st.form_submit_button("⚡ Score Inbound Lead", width="stretch")

        if score_btn:
            lead_in = LeadInput(
                budget_pkr=lead_budget_cr * 1e7,
                num_calls=num_calls,
                avg_call_duration_mins=call_dur,
                response_time_hours=1.5,
                days_since_first_contact=days_contact,
                followup_count=num_calls,
                lead_source=l_source,
                preferred_city=l_city,
                purpose="Buy",
                property_type_preferred="House",
                visit_booked=v_booked,
                visit_completed=v_completed,
                objection_raised=objection
            )
            df_lead_proc = prepare_lead_df(lead_in)
            X_lead_v = artifacts.lead_pipeline.transform(df_lead_proc)
            prob_v = float(artifacts.lead_model.predict_proba(X_lead_v)[0, 1])

            hot_t = artifacts.metadata["lead_scoring"]["hot_threshold"]
            warm_t = artifacts.metadata["lead_scoring"]["warm_threshold"]
            tier_v = "🔥 Hot" if prob_v >= hot_t else ("🌤 Warm" if prob_v >= warm_t else "❄️ Cold")
            action_v = "Call immediately within 1 hour! Highly engaged prospect." if tier_v == "🔥 Hot" else ("Follow up within 24h. Address concerns and schedule viewing." if tier_v == "🌤 Warm" else "Enroll in automated WhatsApp marketing drip.")

            st.markdown(f"### Lead Score: **{tier_v}** ({prob_v*100:.1f}%)")
            st.info(f"👉 **Sales Team Directive:** {action_v}")


# ========================================================
# TAB 3: SHAP Explainability Studio
# ========================================================
with tab_shap:
    st.subheader("SHAP (SHapley Additive exPlanations) Local & Global Studio")
    st.caption("Unboxes black-box tree ensembles into transparent, human-auditable dollar impact drivers and UrduLish agent talking points.")

    if "val_result" in st.session_state:
        res = st.session_state["val_result"]
        X_proc = res["X_proc"]
        prop_req = res["prop_req"]

        # Local SHAP for current listing
        shap_vals = artifacts.val_explainer.shap_values(X_proc)[0]
        feature_names = artifacts.val_pipeline.get_feature_names_out().tolist()
        clean_fnames = [f.replace("num__", "").replace("cat__", "").replace("low_card_cat__", "").replace("high_card_loc__", "") for f in feature_names]

        # Get top 8 absolute features
        top_idx = np.argsort(np.abs(shap_vals))[::-1][:8]
        top_names = [clean_fnames[i] for i in top_idx]
        top_vals = [float(shap_vals[i]) for i in top_idx]

        # Horizontal Bar Chart of Impacts
        col_c1, col_c2 = st.columns([1, 1], gap="large")

        with col_c1:
            st.markdown(f"#### Top Value Drivers for {prop_req.location}")
            colors = ["#10b981" if v > 0 else "#ef4444" for v in top_vals[::-1]]
            fig_shap = go.Figure(go.Bar(
                x=top_vals[::-1],
                y=top_names[::-1],
                orientation="h",
                marker=dict(color=colors)
            ))
            fig_shap.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="SHAP Value (Impact on Log Price)",
                margin=dict(l=10, r=10, t=10, b=10),
                height=380
            )
            st.plotly_chart(fig_shap, width="stretch")

        with col_c2:
            st.markdown("#### Bilingual Sales Agent Talking Points (UrduLish)")
            pos_reasons = [top_names[i] for i in range(len(top_names)) if top_vals[i] > 0][:3]
            neg_reasons = [top_names[i] for i in range(len(top_names)) if top_vals[i] < 0][:2]

            st.markdown(f"""
            <div class="metric-card">
                <h4 style="color:#38bdf8; margin-top:0;">Client Negotiation Script:</h4>
                <p><b>Valuation Context:</b> "Model ke mutabiq is property ki fair market price <b>{format_crore_lakh(res['mid'])}</b> calculate hui hai."</p>
                <p><b>Strong Positive Factors (+):</b> {', '.join(pos_reasons) if pos_reasons else 'Prime location & size'} ki wajah se property premium command kar rahi hai.</p>
                <p><b>Drag / Value Restraints (-):</b> {', '.join(neg_reasons) if neg_reasons else 'Structure age'} buyer ke liye negotiation room create karta hai.</p>
                <p><b>Closing Strategy:</b> 80% range ke mutabiq buyer ko <b>{format_crore_lakh(res['low'])}</b> se start karne ka mashwara dein.</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Please compute a property valuation on Tab 1 first to view local SHAP attributions.")


# ========================================================
# TAB 4: Market Analytics (Day 1 Insights)
# ========================================================
with tab_analytics:
    st.subheader("Pakistan Real Estate Market Intelligence")
    st.caption("Macroeconomic price distributions, price-per-marla density, and construction economics across Pakistani cities.")

    if not df_prop.empty:
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            # Price Per Marla by City
            city_avg = df_prop.groupby("city")["price_per_marla"].mean().reset_index()
            city_avg["Price_per_Marla_Lakh"] = city_avg["price_per_marla"] / 1e5
            fig_ppm = px.bar(
                city_avg.sort_values(by="Price_per_Marla_Lakh", ascending=False),
                x="city",
                y="Price_per_Marla_Lakh",
                color="city",
                title="Average Price per Marla by City (Lakh PKR)",
                template="plotly_dark"
            )
            fig_ppm.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig_ppm, width="stretch")

        with col_m2:
            # Society Tier Distribution
            tier_dist = df_prop["society_tier"].value_counts().reset_index()
            tier_dist.columns = ["Society Tier", "Listing Count"]
            fig_tier = px.pie(
                tier_dist,
                names="Society Tier",
                values="Listing Count",
                title="Inventory by Society Economic Tier",
                template="plotly_dark",
                hole=0.4
            )
            fig_tier.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_tier, width="stretch")

        # Covered Area vs Price
        df_scatter = df_prop.sample(min(800, len(df_prop))).copy()
        df_scatter["Price_Crore"] = df_scatter["price_pkr"] / 1e7
        fig_scatter = px.scatter(
            df_scatter,
            x="covered_area_sqft",
            y="Price_Crore",
            color="city",
            size="plot_size_marla",
            hover_data=["location", "property_type", "bedrooms"],
            title="Covered Area (Sq Ft) vs Property Price (Crore PKR)",
            template="plotly_dark"
        )
        fig_scatter.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_scatter, width="stretch")


# ========================================================
# TAB 5: AI Assistant (UrduLish Chat)
# ========================================================
with tab_chat:
    st.subheader("AI Real Estate Sales Assistant (UrduLish)")
    st.caption("Autonomous conversational agent grounded in machine learning models and database comps. LLM never invents a number.")

    # Initialize chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Assalam-o-Alaikum! Main Pakistan Real Estate AI Assistant hoon. Aap mujh se kisi bhi society ki property valuation, fair price range, market statistics, ya sales leads ke baray mein UrduLish mein pooch sakte hain."}
        ]

    # Pre-populated prompt chips
    st.markdown("##### Quick Inquiries:")
    c_btn1, c_btn2, c_btn3 = st.columns(3)
    preset_query = None
    if c_btn1.button("🏡 DHA Phase 6 1-Kanal Price"):
        preset_query = "DHA Phase 6 mein 1 kanal, 5 saal purana ghar, kitne ka jana chahiye?"
    if c_btn2.button("🎯 Score 5-Crore Lead"):
        preset_query = "Hamari ek lead hai jiska budget 5 crore hai, 4 dafa call ho chuki hai aur visit bhi book hai, iska kya score hai?"
    if c_btn3.button("📈 DHA Lahore Market Stats"):
        preset_query = "DHA Lahore mein average price per marla kya chal rahi hai?"

    # Display chat messages
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User input
    user_input = st.chat_input("Ask in Roman Urdu / UrduLish or English...") or preset_query

    if user_input:
        # Add to state and render
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("AI Agent models aur comps tools query kar raha hai..."):
                t0 = time.time()
                res = chat_with_assistant(user_input, chat_history=st.session_state.chat_messages[:-1])
                elapsed = round(time.time() - t0, 2)
                st.markdown(res["reply"])
                st.caption(f"⏱️ Model Grounded Response Generated in {elapsed}s")

        st.session_state.chat_messages.append({"role": "assistant", "content": res["reply"]})


# ========================================================
# TAB 6: MLOps Control Tower & Drift Lifecycle
# ========================================================
with tab_mlops:
    st.subheader("📡 MLOps Control Tower: Drift Detection & Automated Lifecycle")
    st.caption("Continuous production monitoring, statistical population stability audit (PSI/KS), automated gated retraining, and rollback safeguarding.")

    # 1. Load latest drift report if available
    drift_json_path = os.path.join(BASE_DIR, "reports", "drift_report.json")
    drift_report = None
    if os.path.exists(drift_json_path):
        try:
            with open(drift_json_path, "r", encoding="utf-8") as f:
                drift_report = json.load(f)
        except Exception:
            drift_report = None

    # Status Cards
    if drift_report:
        status_val = drift_report.get("overall_status", "UNKNOWN")
        perf = drift_report.get("performance_drift", {})
        pred = drift_report.get("prediction_drift", {})
        feat = drift_report.get("feature_drift", {})

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            status_color = "🔴" if status_val == "RETRAIN_TRIGGERED" else ("🟡" if status_val == "WARNING" else "🟢")
            st.metric(
                label="System Health SLA",
                value=f"{status_color} {status_val}",
                delta="Retrain Mandated" if drift_report.get("retrain_recommended") else "Nominal SLA",
                delta_color="inverse" if drift_report.get("retrain_recommended") else "normal"
            )
        with m2:
            mape_val = perf.get("current_mape_pct", 0.0)
            st.metric(
                label="Production MAPE",
                value=f"{mape_val:.2f}%",
                delta=f"Alert Threshold: {drift_report.get('alert_mape_threshold_pct', 15.0)}%",
                delta_color="inverse" if mape_val > 15.0 else "normal"
            )
        with m3:
            psi_val = pred.get("psi", 0.0)
            st.metric(
                label="Prediction PSI",
                value=f"{psi_val:.4f}",
                delta=f"Threshold: 0.25 ({pred.get('status', 'STABLE')})",
                delta_color="inverse" if psi_val >= 0.25 else "normal"
            )
        with m4:
            drifted_cnt = feat.get("drifted_features_count", 0)
            tot_cnt = feat.get("total_features_evaluated", 0)
            st.metric(
                label="Drifted Features",
                value=f"{drifted_cnt} / {tot_cnt}",
                delta=f"Warnings: {feat.get('warning_features_count', 0)}"
            )

        st.markdown("---")

    # Action Controls
    st.markdown("##### ⚙️ MLOps Operational Actions")
    col_act1, col_act2, col_act3 = st.columns(3)

    with col_act1:
        if st.button("🧪 Simulate +15% Inflation & Run Audit", use_container_width=True):
            with st.spinner("Simulating production data batch & running KS/PSI tests..."):
                from drift_monitoring import run_drift_detection_flow
                summary = run_drift_detection_flow(simulate_drift=True, price_inflation_pct=0.15)
                st.success("✅ Drift Audit completed! Reloading metrics...")
                st.rerun()

    with col_act2:
        if st.button("⚡ Trigger Retraining Pipeline", use_container_width=True):
            with st.spinner("Retraining challenger model, evaluating holdout set & testing promotion gate..."):
                from retraining_pipeline import RetrainingPipeline
                pipeline = RetrainingPipeline()
                res = pipeline.run_retraining(
                    new_data_path=os.path.join(BASE_DIR, "data_cleaned", "property_listings_drifted_simulated.csv")
                )
                if res["promoted"]:
                    st.success(f"🎉 Challenger PROMOTED as Champion! (MAPE: {res['challenger_metrics']['MAPE_pct']}%)")
                else:
                    st.warning(f"❌ Challenger did not beat Champion SLA (Challenger: {res['challenger_metrics']['MAPE_pct']}%, Champ: {res['champion_metrics']['MAPE_pct']}%)")
                st.rerun()

    with col_act3:
        if st.button("⏪ Rollback to Previous Champion", use_container_width=True):
            with st.spinner("Restoring previous champion model snapshot from saved_models/rollback/..."):
                from retraining_pipeline import ModelVersionManager
                success = ModelVersionManager.execute_rollback()
                if success:
                    st.success("✅ Rollback successful! Previous champion model reinstated.")
                else:
                    st.error("Rollback failed: No backup snapshot found.")
                st.rerun()

    st.markdown("---")

    # Feature drift breakdown table
    if drift_report and "feature_drift" in drift_report:
        st.markdown("##### 🔬 Monitored Feature Drift Breakdown (KS & PSI Tests)")
        feat_data = []
        for feat_name, f_info in drift_report["feature_drift"].get("feature_reports", {}).items():
            if f_info.get("type") == "numerical":
                psi_val = f_info.get("psi")
                b_mean = f_info.get("mean_baseline")
                p_mean = f_info.get("mean_current")
                feat_data.append({
                    "Feature": feat_name,
                    "Type": "Numerical",
                    "Status": str(f_info.get("status", "")),
                    "PSI": f"{psi_val:.4f}" if isinstance(psi_val, (int, float)) else "N/A",
                    "KS p-value": f"{f_info.get('ks_pvalue', 1.0):.4e}",
                    "Mean Shift": f"{f_info.get('mean_shift_pct', 0.0):+.1f}%",
                    "Baseline Mean": f"{b_mean:,.2f}" if isinstance(b_mean, (int, float)) else "N/A",
                    "Production Mean": f"{p_mean:,.2f}" if isinstance(p_mean, (int, float)) else "N/A"
                })
            else:
                feat_data.append({
                    "Feature": feat_name,
                    "Type": "Categorical",
                    "Status": str(f_info.get("status", "")),
                    "PSI": "N/A",
                    "KS p-value": "N/A",
                    "Mean Shift": f"Max delta: {f_info.get('max_category_shift_pct', 0.0):.1f}%",
                    "Baseline Mean": "N/A",
                    "Production Mean": "N/A"
                })
        if feat_data:
            st.dataframe(pd.DataFrame(feat_data), use_container_width=True)

    # Retraining history log
    audit_log_path = os.path.join(BASE_DIR, "reports", "retraining_audit_log.json")
    if os.path.exists(audit_log_path):
        st.markdown("##### 📜 Model Retraining & Promotion Audit Trail")
        try:
            with open(audit_log_path, "r", encoding="utf-8") as f:
                retrain_history = json.load(f)
            df_retrain = pd.DataFrame([
                {
                    "Timestamp": h.get("timestamp"),
                    "Promoted": "✅ Yes" if h.get("promoted") else "❌ No",
                    "Champion MAPE": f"{h['champion_metrics']['MAPE_pct']}%",
                    "Challenger MAPE": f"{h['challenger_metrics']['MAPE_pct']}%",
                    "MAPE Delta": f"{h['deltas']['mape_improvement_pct']:+.2f}%",
                    "Deployed Version": h.get("deployed_version", "N/A")
                }
                for h in reversed(retrain_history[-5:])
            ])
            st.dataframe(df_retrain, use_container_width=True)
        except Exception:
            pass

    # Recent Database Inferences
    st.markdown("##### 🗄️ Recent Live Inference Audit Logs (SQLite)")
    try:
        import database as db
        recent_inferences = db.get_recent_inference_logs(limit=10)
        if recent_inferences:
            df_inf = pd.DataFrame([
                {
                    "Timestamp": r["timestamp"],
                    "Endpoint": r["endpoint"],
                    "Latency (ms)": r["latency_ms"],
                    "Status": r["status_code"]
                }
                for r in recent_inferences
            ])
            st.dataframe(df_inf, use_container_width=True)
        else:
            st.info("No inference logs recorded yet. Send a prediction in Tab 1 or Tab 2 to see live logging.")
    except Exception as e:
        st.caption(f"Audit log status: {e}")

