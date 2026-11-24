"""
Prescriptive Intervention Policy
Maps student dropout risk scores into actionable, risk-tiered pedagogical interventions.
"""

from typing import Dict, Any, List

class InterventionPolicy:
    """
    Translates predictive dropout probabilities into concrete educational remediation actions.
    """

    TIERS = {
        "LOW": {"min": 0.0, "max": 0.25, "color": "GREEN", "label": "On Track / Thriving"},
        "MEDIUM": {"min": 0.25, "max": 0.60, "color": "AMBER", "label": "Moderate Friction / At-Risk"},
        "HIGH": {"min": 0.60, "max": 1.0, "color": "RED", "label": "Critical Churn Imminent"}
    }

    @classmethod
    def evaluate_student(
        cls,
        student_id: str,
        risk_probability: float,
        top_struggling_concept: str = "loops_or_conditionals"
    ) -> Dict[str, Any]:
        """
        Determines the risk tier and prescribes customized immediate actions.
        """
        p = risk_probability

        if p < cls.TIERS["LOW"]["max"]:
            tier = "LOW"
            color = "GREEN"
            label = "Low Risk (Normal Flow)"
            actions = [
                "Proceed with standard adaptive learning path targeting 70% ZPD.",
                "Offer optional high-challenge coding puzzles to maintain high engagement.",
                "Deliver UrduLish praise nudge celebrating progress."
            ]
            mentor_alert = False
            video_remedy = False

        elif p < cls.TIERS["MEDIUM"]["max"]:
            tier = "MEDIUM"
            color = "AMBER"
            label = "Medium Risk (Early Warning Triggered)"
            actions = [
                f"Shift ZPD target from 0.70 to 0.80 (easier success probability) on '{top_struggling_concept}' to rebuild confidence.",
                "Activate interactive micro-hints ladder and provide structured starter code.",
                f"Dispatch Vector DB video jump link: review 60-second lecture clip explaining '{top_struggling_concept}'.",
                "Reduce daily assessment workload from 6 questions to 3 bite-sized practice problems."
            ]
            mentor_alert = False
            video_remedy = True

        else:
            tier = "HIGH"
            color = "RED"
            label = "High Risk (Critical Churn Imminent)"
            actions = [
                "IMMEDIATE FREEZE: Halt progression to new modules; enforce prerequisite remediation on fundamental concepts.",
                "Dispatch high-priority alert to Ilm Academy TA/Mentor for proactive 1-on-1 outreach.",
                f"Deliver empathetic UrduLish reset message acknowledging struggle and removing penalty stress.",
                "Replace formal quizzes with guided interactive code-along walkthroughs with instant feedback."
            ]
            mentor_alert = True
            video_remedy = True

        return {
            "student_id": student_id,
            "risk_score": round(p, 3),
            "risk_tier": tier,
            "tier_label": label,
            "alert_color": color,
            "human_mentor_alert_dispatched": mentor_alert,
            "video_timestamp_remedy_suggested": video_remedy,
            "prescribed_actions": actions
        }

    @classmethod
    def generate_policy_report(cls) -> List[Dict[str, Any]]:
        """Returns the full policy matrix for client documentation."""
        report = []
        for tier_key in ["LOW", "MEDIUM", "HIGH"]:
            meta = cls.TIERS[tier_key]
            dummy = cls.evaluate_student("SAMPLE_STU", (meta["min"] + meta["max"]) / 2.0)
            report.append({
                "risk_tier": tier_key,
                "probability_range": f"{int(meta['min']*100)}% - {int(meta['max']*100)}%",
                "status_label": dummy["tier_label"],
                "prescribed_actions": dummy["prescribed_actions"]
            })
        return report
