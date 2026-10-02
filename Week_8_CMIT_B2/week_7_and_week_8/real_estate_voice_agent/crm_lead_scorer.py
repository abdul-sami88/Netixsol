"""
crm_lead_scorer.py
==================
Inbound Lead Scoring, Asymmetric Cost Optimization, and Priority Tiering.

Integrates with Week 7 CRM:
- Loads champion Lead Classifier model and preprocessing pipeline.
- Scores incoming call leads into 🔥 Hot, 🌤 Warm, or ❄️ Cold tiers.
- Performs Out-of-Distribution checks and logs all inferences to SQLite.
"""

import os
import sys
import json
from typing import Dict, Any, Optional
import joblib
import numpy as np
import pandas as pd

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from guardrails import check_lead_ood, log_model_prediction

VALID_CITIES = ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad"]
VALID_SOURCES = [
    "Facebook Ads", "Google Search Ads", "Inbound Call / Walk-in",
    "Referral / Network", "Website Direct", "WhatsApp Campaign", "Zameen / Graana Portal"
]


class CRMLeadScorer:
    _instance = None

    def __init__(self):
        models_dir = os.path.join(BASE_DIR, "saved_models")
        meta_path = os.path.join(models_dir, "models_metadata.json")

        if not os.path.exists(meta_path):
            # Fallback to AI_property_valuation_lead_scoring if needed
            alt_dir = os.path.join(BASE_DIR, "..", "AI_property_valuation_lead_scoring", "saved_models")
            if os.path.exists(os.path.join(alt_dir, "models_metadata.json")):
                models_dir = alt_dir
                meta_path = os.path.join(alt_dir, "models_metadata.json")

        with open(meta_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        self.lead_meta = self.metadata["lead_scoring"]
        self.pipeline = joblib.load(os.path.join(models_dir, "leads_pipeline.joblib"))
        self.model = joblib.load(os.path.join(models_dir, "leads_champion_model.joblib"))
        self.model_version = self.lead_meta.get("version", "1.0.0")
        self.hot_thresh = float(self.lead_meta.get("hot_threshold", 0.50))
        self.warm_thresh = float(self.lead_meta.get("warm_threshold", 0.35))
        self.optimal_p = float(self.lead_meta.get("optimal_cost_threshold", 0.38))
        print("[CRMLeadScorer] Champion Lead Scoring Model successfully loaded.")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = CRMLeadScorer()
        return cls._instance

    def prepare_lead_dataframe(self, lead_data: Dict[str, Any]) -> pd.DataFrame:
        """Prepares and feature engineers raw lead data matching training pipeline."""
        budget = float(lead_data.get("budget_pkr") or lead_data.get("max_budget_pkr") or 35000000.0)
        num_calls = int(lead_data.get("num_calls") or 1)
        avg_duration = float(lead_data.get("avg_call_duration_mins") or 5.0)
        resp_time = float(lead_data.get("response_time_hours") or 2.0)
        days_contact = float(lead_data.get("days_since_first_contact") or 2.0)
        followups = int(lead_data.get("followup_count") or 1)

        raw_city = str(lead_data.get("preferred_city") or lead_data.get("city") or "Lahore").strip().title()
        preferred_city = raw_city if raw_city in VALID_CITIES else "Lahore"

        raw_source = str(lead_data.get("lead_source") or "Inbound Call / Walk-in").strip()
        matched_source = next((s for s in VALID_SOURCES if s.lower() == raw_source.lower()), "Inbound Call / Walk-in")

        purpose = str(lead_data.get("purpose") or "Buy").strip().title()
        if purpose not in ["Buy", "Rent", "Investment"]:
            purpose = "Buy"

        prop_type = str(lead_data.get("property_type_preferred") or lead_data.get("property_type") or "House").strip().title()
        if prop_type not in ["House", "Flat", "Plot / Plot File", "Commercial", "Farmhouse"]:
            prop_type = "House"

        visit_booked = str(lead_data.get("visit_booked") or "No").strip().title()
        if visit_booked not in ["Yes", "No"]:
            visit_booked = "Yes" if lead_data.get("appointment_booked") else "No"

        visit_completed = str(lead_data.get("visit_completed") or "No").strip().title()
        if visit_completed not in ["Yes", "No"]:
            visit_completed = "No"

        raw_objection = str(lead_data.get("objection_raised") or "None").strip()
        objection_map = {
            "No Objection Raised": 0, "None": 0, "no": 0,
            "Family Consensus Pending": 1, "family": 1,
            "Location Too Far": 2, "location": 2,
            "Timing / Delayed Decision": 2, "timing": 2,
            "Payment Plan / Financing Needed": 3, "financing": 3,
            "Price / Budget Gap": 3, "price": 3,
            "Legal / Title Verification": 4, "legal": 4
        }
        obj_friction = 0
        for k, v in objection_map.items():
            if k.lower() in raw_objection.lower():
                obj_friction = v
                break

        # 1. Lead engagement score
        lead_engagement = float(num_calls * avg_duration)

        # 2. Response speed category
        if resp_time <= 1.0:
            speed_cat = "Instant (<1h)"
        elif resp_time <= 4.0:
            speed_cat = "Prompt (1-4h)"
        elif resp_time <= 12.0:
            speed_cat = "Moderate (4-12h)"
        else:
            speed_cat = "Delayed (>12h)"

        # 3. Interaction intensity
        interaction_intensity = float(followups / (days_contact + 1.0))

        # 4. Visit funnel status
        if visit_completed == "Yes":
            funnel_status = "Visit Completed"
        elif visit_booked == "Yes":
            funnel_status = "Visit Booked Only"
        else:
            funnel_status = "No Visit"

        # 5. Budget to market ratio & realism tier
        city_medians = {
            "Lahore": 35000000.0, "Karachi": 38000000.0,
            "Islamabad": 45000000.0, "Rawalpindi": 22000000.0,
            "Faisalabad": 20000000.0
        }
        med_price = city_medians.get(preferred_city, 35000000.0)
        budget_ratio = float(budget / (med_price + 1e-5))

        if budget_ratio < 0.7:
            b_tier = "Under-Budgeted (<0.7x)"
        elif budget_ratio <= 1.3:
            b_tier = "Market-Aligned (0.7-1.3x)"
        else:
            b_tier = "High-Budgeted (>1.3x)"

        df = pd.DataFrame([{
            "budget_pkr": budget,
            "num_calls": num_calls,
            "avg_call_duration_mins": avg_duration,
            "response_time_hours": resp_time,
            "days_since_first_contact": days_contact,
            "followup_count": followups,
            "lead_engagement_score": lead_engagement,
            "interaction_intensity": interaction_intensity,
            "objection_friction_score": obj_friction,
            "budget_to_market_ratio": budget_ratio,
            "lead_source": matched_source,
            "preferred_city": preferred_city,
            "purpose": purpose,
            "property_type_preferred": prop_type,
            "visit_booked": visit_booked,
            "visit_completed": visit_completed,
            "response_speed_category": speed_cat,
            "visit_funnel_status": funnel_status,
            "budget_realism_tier": b_tier
        }])

        return df

    def predict_score(self, lead_data: Dict[str, Any], client_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculates conversion probability and priority tier for a sales lead.
        Enforces OOD check and logs inference to SQLite.
        """
        email = client_email or lead_data.get("client_email")

        # 1. Check OOD
        is_ood, ood_reason = check_lead_ood(lead_data)
        if is_ood:
            res = {
                "status": "refused",
                "is_ood": True,
                "reason": ood_reason,
                "priority_tier": "❄️ Cold (OOD)",
                "conversion_probability_pct": 0.0,
                "recommended_action": "Manual review required: Lead parameters fall outside normal operational boundaries."
            }
            log_model_prediction(
                prediction_type="LEAD_SCORING",
                model_name=self.lead_meta.get("model_name", "LGBMClassifier"),
                model_version=self.model_version,
                input_payload=lead_data,
                output_payload=res,
                is_ood=True,
                ood_reason=ood_reason,
                client_email=email
            )
            return res

        # 2. Transform & Predict
        df_feat = self.prepare_lead_dataframe(lead_data)
        X_proc = self.pipeline.transform(df_feat)
        prob = float(self.model.predict_proba(X_proc)[0, 1])

        # Priority tier
        if prob >= self.hot_thresh:
            tier = "🔥 Hot"
            action = "Call immediately within 1 hour! Highly engaged prospect ready to convert."
        elif prob >= self.warm_thresh:
            tier = "🌤 Warm"
            action = "Follow up within 24 hours. Address stated friction and schedule on-site visit."
        else:
            tier = "❄️ Cold"
            action = "Enroll into automated WhatsApp newsletter & long-term drip marketing."

        result = {
            "status": "success",
            "is_ood": False,
            "conversion_probability_pct": round(prob * 100, 2),
            "priority_tier": tier,
            "recommended_action": action,
            "optimal_cost_threshold": self.optimal_p,
            "model_version": self.model_version
        }

        # 3. Log to audit database
        log_model_prediction(
            prediction_type="LEAD_SCORING",
            model_name=self.lead_meta.get("model_name", "LGBMClassifier"),
            model_version=self.model_version,
            input_payload=lead_data,
            output_payload=result,
            is_ood=False,
            client_email=email
        )

        return result

    def get_historical_scored_leads(self, limit: int = 100, city: Optional[str] = None, tier: Optional[str] = None, sort_by: str = "score") -> Dict[str, Any]:
        """Scores historical leads from leads_scoring_cleaned.csv and returns prioritized list."""
        csv_path = os.path.join(BASE_DIR, "data_cleaned", "leads_scoring_cleaned.csv")
        if not os.path.exists(csv_path):
            csv_path = os.path.join(BASE_DIR, "..", "AI_property_valuation_lead_scoring", "data_cleaned", "leads_scoring_cleaned.csv")
        if not os.path.exists(csv_path):
            return {"count": 0, "leads": []}

        df = pd.read_csv(csv_path)
        sample_df = df.head(limit).copy()
        X_proc = self.pipeline.transform(sample_df)
        probs = self.model.predict_proba(X_proc)[:, 1]
        sample_df["conversion_score_pct"] = np.round(probs * 100, 1)

        def get_tier(p):
            if p >= self.hot_thresh * 100:
                return "🔥 Hot"
            elif p >= self.warm_thresh * 100:
                return "🌤 Warm"
            else:
                return "❄️ Cold"

        sample_df["priority_tier"] = sample_df["conversion_score_pct"].apply(get_tier)

        def get_action(tier):
            if "Hot" in tier:
                return "Call immediately within 1 hour! High conversion propensity."
            elif "Warm" in tier:
                return "Follow up within 24 hours to schedule property inspection."
            return "Enroll in automated WhatsApp marketing drip."

        sample_df["recommended_action"] = sample_df["priority_tier"].apply(get_action)

        if city and city != "All":
            sample_df = sample_df[sample_df["preferred_city"].str.lower() == city.lower()]
        if tier and tier != "All":
            sample_df = sample_df[sample_df["priority_tier"].str.contains(tier, case=False, na=False)]

        if sort_by == "budget":
            sample_df = sample_df.sort_values(by="budget_pkr", ascending=False)
        else:
            sample_df = sample_df.sort_values(by="conversion_score_pct", ascending=False)

        leads = []
        for _, row in sample_df.iterrows():
            b = row.get("budget_pkr", 0)
            if b >= 10000000:
                b_fmt = f"{b / 10000000:.2f} Crore"
            elif b >= 100000:
                b_fmt = f"{b / 100000:.1f} Lakh"
            else:
                b_fmt = f"{int(b):,} PKR"

            leads.append({
                "lead_id": str(row.get("lead_id", "")),
                "client_email": f"{str(row.get('lead_id', 'lead')).lower()}@investor.pk",
                "lead_source": str(row.get("lead_source", "Portal")),
                "preferred_city": str(row.get("preferred_city", "Lahore")),
                "property_type": str(row.get("property_type_preferred", "House")),
                "budget_pkr": float(b),
                "budget_formatted": b_fmt,
                "num_calls": int(row.get("num_calls", 1)),
                "visit_booked": str(row.get("visit_booked", "No")),
                "visit_completed": str(row.get("visit_completed", "No")),
                "objection_raised": str(row.get("objection_raised", "None")),
                "conversion_score_pct": float(row.get("conversion_score_pct", 0.0)),
                "priority_tier": str(row.get("priority_tier", "❄️ Cold")),
                "recommended_action": str(row.get("recommended_action", ""))
            })

        return {
            "count": len(leads),
            "leads": leads
        }


crm_lead_scorer = CRMLeadScorer.get_instance()


def score_lead(lead_data: Dict[str, Any], client_email: Optional[str] = None) -> Dict[str, Any]:
    return crm_lead_scorer.predict_score(lead_data, client_email=client_email)
