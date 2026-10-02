"""
ml_models_service.py
====================
Property Valuation Bridge for Week 7 Voice Agent & Live REST Endpoints.

Features:
1. Loads Champion LightGBM Regressor and 80% Confidence Interval Quantile Engine.
2. Validates physical inputs with Out-of-Distribution (OOD) checks.
3. Automatically attaches mandatory bilingual legal disclaimers.
4. Logs every prediction to SQLite `model_prediction_logs`.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from guardrails import check_property_ood, log_model_prediction, DISCLAIMER_TEXT_EN, DISCLAIMER_TEXT_UR
from src.valuation_models import format_crore_lakh
from src.feature_engineering import calculate_amenity_score

VALID_CITIES = ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad"]


class MLModelsService:
    _instance = None

    def __init__(self):
        models_dir = os.path.join(BASE_DIR, "saved_models")
        meta_path = os.path.join(models_dir, "models_metadata.json")

        if not os.path.exists(meta_path):
            alt_dir = os.path.join(BASE_DIR, "..", "AI_property_valuation_lead_scoring", "saved_models")
            if os.path.exists(os.path.join(alt_dir, "models_metadata.json")):
                models_dir = alt_dir
                meta_path = os.path.join(alt_dir, "models_metadata.json")

        with open(meta_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        self.val_meta = self.metadata["property_valuation"]
        print("[MLModelsService] Loading valuation and lead scoring models into memory...")
        self.val_pipeline = joblib.load(os.path.join(models_dir, "valuation_pipeline.joblib"))
        self.val_model = joblib.load(os.path.join(models_dir, "valuation_champion_model.joblib"))
        self.val_engine = joblib.load(os.path.join(models_dir, "valuation_quantile_engine.joblib"))
        self.model_version = self.val_meta.get("version", "1.0.0")
        print("[MLModelsService] All models successfully loaded!")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = MLModelsService()
        return cls._instance

    def prepare_property_dataframe(self, prop_data: Dict[str, Any]) -> pd.DataFrame:
        """Prepares and feature-engineers property specifications matching LightGBM training."""
        plot_size = float(prop_data.get("plot_size_marla") or 10.0)
        covered_area = float(prop_data.get("covered_area_sqft") or (plot_size * 225.0 * 1.05))
        bedrooms = int(prop_data.get("bedrooms") or 4)
        bathrooms = int(prop_data.get("bathrooms") or (bedrooms + 1))
        age_years = float(prop_data.get("age_years") if prop_data.get("age_years") is not None else 3.0)
        floors = int(prop_data.get("floors") or 2)

        raw_city = str(prop_data.get("city") or "Lahore").strip().title()
        city = raw_city if raw_city in VALID_CITIES else "Lahore"

        location = str(prop_data.get("location") or prop_data.get("area") or "DHA Phase 6").strip()
        prop_type = str(prop_data.get("property_type") or "House").strip().title()

        is_corner = int(prop_data.get("is_corner", 0))
        is_park = int(prop_data.get("is_park_facing", 0))
        is_boulevard = int(prop_data.get("is_main_boulevard", 0))
        amenities = str(prop_data.get("amenities") or "24/7 security;gated community")

        dist_road = float(prop_data.get("dist_to_main_road_km") or 1.0)
        dist_comm = float(prop_data.get("dist_to_commercial_km") or 1.5)
        dist_hosp = float(prop_data.get("dist_to_hospital_km") or 2.5)
        dist_school = float(prop_data.get("dist_to_school_km") or 1.2)

        amenities_count = len([a for a in amenities.split(";") if a.strip()]) if amenities else 2

        df = pd.DataFrame([{
            "plot_size_marla": plot_size,
            "covered_area_sqft": covered_area,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "age_years": age_years,
            "floors": floors,
            "is_corner": is_corner,
            "is_park_facing": is_park,
            "is_main_boulevard": is_boulevard,
            "amenities_count": amenities_count,
            "dist_to_main_road_km": dist_road,
            "dist_to_school_km": dist_school,
            "dist_to_hospital_km": dist_hosp,
            "dist_to_commercial_km": dist_comm,
            "city": city,
            "location": location,
            "property_type": prop_type
        }])

        # Engineered features
        # 1. Covered area ratio
        df["covered_area_ratio"] = covered_area / ((plot_size * 225.0) + 1e-5)

        # 2. Age bucket
        if age_years <= 1:
            age_bucket = "Brand New (0-1y)"
        elif age_years <= 5:
            age_bucket = "Modern (2-5y)"
        elif age_years <= 15:
            age_bucket = "Established (6-15y)"
        else:
            age_bucket = "Vintage (>15y)"
        df["property_age_bucket"] = age_bucket

        # 3. Society Tier
        loc_lower = location.lower()
        if any(w in loc_lower for w in ["dha", "bahria", "emaar", "gulberg", "f-6", "f-7", "f-8", "e-7"]):
            tier = "Tier 1 (Luxury)"
        elif any(w in loc_lower for w in ["askari", "cantt", "clifton", "defence", "i-8", "g-11"]):
            tier = "Tier 2 (Prime)"
        else:
            tier = "Tier 3 (Standard)"
        df["society_tier"] = tier

        # 4. Amenities score
        df["weighted_amenity_score"] = calculate_amenity_score(amenities)

        # 5. Accessibility index
        access_denom = 1.0 + (dist_road * 0.4 + dist_comm * 0.3 + dist_school * 0.15 + dist_hosp * 0.15)
        df["composite_accessibility_index"] = 1.0 / access_denom

        # 6. Bed bath ratio & Total rooms
        df["bed_bath_ratio"] = float(bedrooms) / (float(bathrooms) + 1e-5)
        df["total_rooms"] = bedrooms + bathrooms

        # 7. Prime orientation score
        df["prime_orientation_score"] = float(is_corner * 1.5 + is_park * 1.2 + is_boulevard * 1.8)

        # 8. Covered area per bedroom
        df["covered_area_per_bed"] = covered_area / max(float(bedrooms), 1.0)

        return df

    def predict_price(self, property_data: Dict[str, Any], client_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes property valuation, calculates 80% confidence interval,
        enforces Out-of-Distribution checks, and appends mandatory legal disclaimers.
        """
        email = client_email or property_data.get("client_email")

        # 1. Check OOD Guardrail
        is_ood, ood_reason = check_property_ood(property_data)
        if is_ood:
            res = {
                "status": "refused",
                "is_ood": True,
                "reason": ood_reason,
                "fair_market_price_pkr": None,
                "disclaimer": DISCLAIMER_TEXT_EN
            }
            log_model_prediction(
                prediction_type="PRICE_VALUATION",
                model_name=self.val_meta.get("model_name", "LGBMRegressor"),
                model_version=self.model_version,
                input_payload=property_data,
                output_payload=res,
                is_ood=True,
                ood_reason=ood_reason,
                client_email=email
            )
            return res

        # 2. Transform & Quantile Inference
        df_feat = self.prepare_property_dataframe(property_data)
        X_proc = self.val_pipeline.transform(df_feat)
        pred_mid_pkr, pred_low_pkr, pred_high_pkr = self.val_engine.predict_range(X_proc)

        p_mid = float(pred_mid_pkr[0])
        p_low = float(pred_low_pkr[0])
        p_high = float(pred_high_pkr[0])

        loc = property_data.get("location") or property_data.get("area") or "DHA Phase 6"
        city = property_data.get("city") or "Lahore"
        ptype = property_data.get("property_type") or "House"
        psize = float(property_data.get("plot_size_marla") or 10.0)

        res = {
            "status": "success",
            "is_ood": False,
            "property_summary": f"{psize:.1f} Marla {ptype} in {loc}, {city}",
            "fair_market_price_pkr": round(p_mid, 0),
            "fair_market_price_formatted": format_crore_lakh(p_mid),
            "confidence_interval_80": {
                "lower_bound_pkr": round(p_low, 0),
                "lower_bound_formatted": format_crore_lakh(p_low),
                "upper_bound_pkr": round(p_high, 0),
                "upper_bound_formatted": format_crore_lakh(p_high),
                "confidence_level": "80%"
            },
            "disclaimer": DISCLAIMER_TEXT_EN,
            "disclaimer_urdulish": DISCLAIMER_TEXT_UR,
            "model_version": self.model_version
        }

        # 3. Investment verdict if asking price provided
        listed_price = property_data.get("listed_price_pkr")
        if listed_price is not None and float(listed_price) > 0:
            p_listed = float(listed_price)
            if p_listed < p_low:
                verdict = "Underpriced"
                narrative = f"Asking price is below fair market median. Excellent investor bargain or motivated seller."
            elif p_listed > p_high:
                verdict = "Overpriced"
                narrative = f"Asking price is above fair market median. Seller is demanding an aggressive premium."
            else:
                verdict = "Fair Market Price"
                narrative = "Asking price is well-aligned within normal market trading range."

            res["investment_verdict"] = {
                "verdict": verdict,
                "listed_price_pkr": p_listed,
                "listed_price_formatted": format_crore_lakh(p_listed),
                "client_narrative": narrative
            }

        # 4. Log to SQLite
        log_model_prediction(
            prediction_type="PRICE_VALUATION",
            model_name=self.val_meta.get("model_name", "LGBMRegressor"),
            model_version=self.model_version,
            input_payload=property_data,
            output_payload=res,
            is_ood=False,
            client_email=email
        )

        return res


def predict_property_price(property_data: Dict[str, Any], client_email: Optional[str] = None) -> Dict[str, Any]:
    """Convenience helper used across voice agent and API endpoints."""
    service = MLModelsService.get_instance()
    return service.predict_price(property_data, client_email=client_email)
