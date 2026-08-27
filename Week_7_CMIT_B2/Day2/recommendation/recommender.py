"""
recommender.py — Task 4: Property Recommendation Engine

Recommends properties using ONLY verified SQL data (structured filters +
a transparent, weighted scoring function) plus amenity match pulled from
the `amenities` table. "Investment goal" is handled as a scoring strategy,
not a fabricated prediction — everything is computed from real columns
(price, price_bin, locality popularity, purpose) already in the DB, so
there's nothing to hallucinate.
"""
from __future__ import annotations
import sqlite3
import os
from dataclasses import dataclass

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "..", "db", "real_estate.db")


@dataclass
class RecommendationRequest:
    city: str | None = None
    max_budget: float | None = None
    min_budget: float | None = None
    min_area_marla: float | None = None
    bedrooms: int | None = None
    purpose: str | None = None            # "For Sale" / "For Rent"
    desired_amenities: list[str] | None = None
    investment_goal: str | None = None    # "capital_growth" | "rental_yield" | "affordability" | None
    top_n: int = 5


class Recommender:
    def __init__(self, db_path: str = DB):
        self.db_path = db_path

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def recommend(self, req: RecommendationRequest) -> list[dict]:
        conn = self._conn()
        clauses, params = [], []
        if req.city:
            clauses.append("p.city = ?"); params.append(req.city)
        if req.purpose:
            clauses.append("p.purpose = ?"); params.append(req.purpose)
        if req.max_budget:
            clauses.append("p.price <= ?"); params.append(req.max_budget)
        if req.min_budget:
            clauses.append("p.price >= ?"); params.append(req.min_budget)
        if req.bedrooms:
            clauses.append("p.bedrooms >= ?"); params.append(req.bedrooms)
        if req.min_area_marla:
            clauses.append("p.area_marla >= ?"); params.append(req.min_area_marla)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        sql = f"""
            SELECT p.*, l.popularity_score, l.avg_price_per_marla
            FROM properties p LEFT JOIN locations l ON p.location_id = l.location_id
            {where}
        """
        rows = [dict(r) for r in conn.execute(sql, tuple(params)).fetchall()]

        # amenity match count (real data from `amenities` table, not guessed)
        amenity_map = {}
        if req.desired_amenities:
            q = conn.execute("SELECT property_id, amenity_name FROM amenities").fetchall()
            for r in q:
                amenity_map.setdefault(r["property_id"], set()).add(r["amenity_name"])
        conn.close()

        scored = []
        for r in rows:
            score = 0.0
            reasons = []

            # budget fit — closer to (but under) budget without being far under it
            if req.max_budget:
                fit = 1 - abs(req.max_budget - r["price"]) / req.max_budget
                score += max(fit, 0) * 30
                if r["price"] <= req.max_budget:
                    reasons.append("within budget")

            # bedroom match
            if req.bedrooms:
                if r["bedrooms"] == req.bedrooms:
                    score += 15; reasons.append("exact bedroom match")
                elif r["bedrooms"] > req.bedrooms:
                    score += 7

            # amenity overlap
            if req.desired_amenities:
                have = amenity_map.get(r["property_id"], set())
                overlap = have.intersection(set(req.desired_amenities))
                score += 8 * len(overlap)
                if overlap:
                    reasons.append(f"matches amenities: {', '.join(sorted(overlap))}")

            # investment-goal weighting, using only real columns
            pop = r.get("popularity_score") or 0
            avg_ppm = r.get("avg_price_per_marla") or 0
            if req.investment_goal == "capital_growth":
                score += pop * 10  # high-popularity localities = stronger appreciation proxy
                if r["area_marla"] and avg_ppm and r["price"] / r["area_marla"] < avg_ppm:
                    score += 12
                    reasons.append("priced below area's average PKR/marla (upside potential)")
            elif req.investment_goal == "rental_yield" and r["purpose"] == "For Rent":
                score += (r["price"] / max(r["area_marla"], 1)) * 0.0005
            elif req.investment_goal == "affordability":
                score += max(0, 40 - (r["price"] / 1_000_000))

            scored.append({**r, "match_score": round(score, 2), "match_reasons": reasons})

        scored.sort(key=lambda x: x["match_score"], reverse=True)
        return scored[:req.top_n]


def format_recommendation(r: dict) -> str:
    reasons = "; ".join(r["match_reasons"]) if r["match_reasons"] else "matches your filters"
    return (f"#{r['property_id']} — {r['bedrooms']}-bed {r['property_type']} in "
            f"{r['locality']}, {r['city']} — PKR {r['price']:,.0f} ({r['area']}). "
            f"Score {r['match_score']} — {reasons}.")


if __name__ == "__main__":
    rec = Recommender()
    req = RecommendationRequest(city="Lahore", max_budget=15_000_000, bedrooms=3,
                                 purpose="For Sale", desired_amenities=["Community Park", "24/7 Security"],
                                 investment_goal="capital_growth", top_n=5)
    for r in rec.recommend(req):
        print(format_recommendation(r))
