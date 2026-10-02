"""
database.py
===========
Day 5 - Task 3: Production Database Layer for Inference Auditing, Drift Tracking, and Deployment Lifecycle.

Manages SQLite / PostgreSQL database schemas:
1. InferenceAuditLog: Logs every API request, input payload, output prediction, and latency
2. DriftMonitoringLog: Records continuous drift detection runs, PSI, MAPE, and retrain triggers
3. ModelDeploymentHistory: Tracks model promotions, challenger evaluations, and rollbacks
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, desc
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'production_audit.db')}")

# Fix postgresql:// scheme for SQLAlchemy 2+ if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class InferenceAuditLog(Base):
    __tablename__ = "inference_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    endpoint = Column(String(100), nullable=False)
    inputs_json = Column(Text, nullable=False)
    prediction_result = Column(Text, nullable=False)
    latency_ms = Column(Float, nullable=False)
    client_ip = Column(String(50), nullable=True)
    status_code = Column(Integer, default=200)


class DriftMonitoringLog(Base):
    __tablename__ = "drift_monitoring_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    overall_status = Column(String(50), nullable=False)
    current_mape_pct = Column(Float, nullable=True)
    prediction_psi = Column(Float, nullable=True)
    drifted_features_count = Column(Integer, default=0)
    retrain_triggered = Column(Boolean, default=False)
    details_json = Column(Text, nullable=True)


class ModelDeploymentHistory(Base):
    __tablename__ = "model_deployment_history"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    action = Column(String(50), nullable=False)  # "PROMOTION", "ROLLBACK", "EVALUATION"
    model_name = Column(String(100), default="PropertyValuation")
    version = Column(String(50), nullable=False)
    champion_mape = Column(Float, nullable=True)
    challenger_mape = Column(Float, nullable=True)
    details_json = Column(Text, nullable=True)


def init_db():
    """Initializes tables in database."""
    Base.metadata.create_all(bind=engine)


def log_inference(
    endpoint: str,
    inputs: Dict[str, Any],
    result: Dict[str, Any],
    latency_ms: float,
    client_ip: Optional[str] = "127.0.0.1",
    status_code: int = 200
):
    """Asynchronously or synchronously records inference request to audit database."""
    try:
        session = SessionLocal()
        record = InferenceAuditLog(
            endpoint=endpoint,
            inputs_json=json.dumps(inputs),
            prediction_result=json.dumps(result),
            latency_ms=round(latency_ms, 2),
            client_ip=client_ip,
            status_code=status_code
        )
        session.add(record)
        session.commit()
        session.close()
    except Exception as e:
        print(f"Warning: Failed to log inference audit to database: {e}")


def log_drift_event(drift_summary: Dict[str, Any]):
    """Records drift monitoring evaluation results to database."""
    try:
        session = SessionLocal()
        perf = drift_summary.get("performance_drift", {})
        pred = drift_summary.get("prediction_drift", {})
        feat = drift_summary.get("feature_drift", {})

        record = DriftMonitoringLog(
            overall_status=drift_summary.get("overall_status", "UNKNOWN"),
            current_mape_pct=perf.get("current_mape_pct"),
            prediction_psi=pred.get("psi"),
            drifted_features_count=feat.get("drifted_features_count", 0),
            retrain_triggered=bool(drift_summary.get("retrain_recommended", False)),
            details_json=json.dumps(drift_summary)
        )
        session.add(record)
        session.commit()
        session.close()
    except Exception as e:
        print(f"Warning: Failed to log drift event to database: {e}")


def get_recent_inference_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetches recent inference audit records for dashboard monitoring."""
    session = SessionLocal()
    try:
        records = session.query(InferenceAuditLog).order_by(desc(InferenceAuditLog.timestamp)).limit(limit).all()
        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else "",
                "endpoint": r.endpoint,
                "latency_ms": r.latency_ms,
                "status_code": r.status_code,
                "inputs": json.loads(r.inputs_json) if r.inputs_json else {},
                "prediction": json.loads(r.prediction_result) if r.prediction_result else {}
            }
            for r in records
        ]
    finally:
        session.close()


def get_drift_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Fetches past drift audit events."""
    session = SessionLocal()
    try:
        records = session.query(DriftMonitoringLog).order_by(desc(DriftMonitoringLog.timestamp)).limit(limit).all()
        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else "",
                "overall_status": r.overall_status,
                "current_mape_pct": r.current_mape_pct,
                "prediction_psi": r.prediction_psi,
                "drifted_features_count": r.drifted_features_count,
                "retrain_triggered": r.retrain_triggered
            }
            for r in records
        ]
    finally:
        session.close()


# Initialize database upon import
init_db()
