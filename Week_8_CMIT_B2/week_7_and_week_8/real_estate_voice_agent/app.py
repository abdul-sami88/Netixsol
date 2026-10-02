import time
import json
import inspect
from functools import wraps
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException, Header, Depends, status
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import config
from database import query_properties_sql, get_agent_by_city, get_db_connection
from memory import get_session_memory, reset_session_memory, extract_spoken_email
from rag_engine import RAGEngine, evaluate_chunk_sizes
from recommendation import RecommendationEngine
from system_prompt import get_system_prompt_with_context
from llm_client import llm_client
from stt import STTProcessor
from appointment_manager import appointment_manager
from email_service import DEFAULT_MANAGER_EMAIL, email_service
from crm_store import crm_store
from eval_hallucination import run_hallucination_evaluation
from eval_voice import evaluate_voice_pipeline_convo
from ml_models_service import predict_property_price
from crm_lead_scorer import crm_lead_scorer
from guardrails import check_prompt_injection, check_property_ood, check_lead_ood, DISCLAIMER_TEXT_EN, DISCLAIMER_TEXT_UR

app = FastAPI(
    title="UrduLish Real Estate AI Voice Agent API",
    description="Vapi/Deepgram/ElevenLabs compatible Custom LLM Server with Primary Gemini & Groq Backup + Day 4 Automation + CRM Logging Store",
    version="1.0.0"
)

# CORS middleware restricted to localhost development origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
rag_engine = RAGEngine(chunk_size=128)
rec_engine = RecommendationEngine(rag_engine=rag_engine)

def process_appointment_interaction(session_id: str, mem, normalized_msg: str) -> Dict[str, Any]:
    """
    Production Appointment Interaction Controller:
    1. Checks intents: Booking, Rescheduling, Cancellation.
    2. Rescheduling & Cancellation: Verifies & confirms using unique Appointment ID.
    3. Slot availability check & recommendations on occupied slots.
    4. Dispatches real emails with Appointment ID and 1-Click 'Add to Google Calendar' button.
    """
    reschedule_keywords = ["reschedule", "time change", "change time", "postpone", "doosra time", "time badal", "badal", "تبدیل"]
    cancel_keywords = ["cancel", "cancellation", "mansookh", "khatam", "منسوخ", "کینسل"]
    booking_keywords = ["book", "booking", "appointment", "visit", "schedule", "meeting", "email", "mail", "confirm", "bhej", "بک", "وزٹ", "سائیڈ", "سکیجول", "ای میل", "اپوائنٹمنٹ", "کل", "شام", "کنفرم", "ٹائم", "میل"]

    is_reschedule = (mem.appointment_action == "RESCHEDULE") or any(w in normalized_msg.lower() for w in reschedule_keywords)
    is_cancel = (mem.appointment_action == "CANCEL") or any(w in normalized_msg.lower() for w in cancel_keywords)
    is_booking_intent = not (is_reschedule or is_cancel) and ((mem.appointment_action == "BOOK") or any(w in normalized_msg.lower() for w in booking_keywords) or ("@" in normalized_msg or "gmail" in normalized_msg.lower()))

    context_banner = ""
    auto_booked_appointment = None

    # 1. Repeat Caller: Reschedule or Cancel using Appointment ID
    if is_reschedule or is_cancel:
        action_title = "RESCHEDULE" if is_reschedule else "CANCEL"
        existing_app = None

        if mem.appointment_id:
            existing_app = appointment_manager.get_appointment_by_id(mem.appointment_id)
        elif mem.client_email and "@" in mem.client_email:
            existing_app = appointment_manager.get_latest_appointment_by_email(mem.client_email)

        if not existing_app and not mem.appointment_id:
            context_banner += (
                f"\n=== REPEAT CALLER: APPOINTMENT ID REQUIRED ===\n"
                f"Client wants to {action_title.lower()} an existing appointment.\n"
                f"MANDATORY: Ask the client for their Appointment ID (provided in their confirmation email).\n"
                f"Example: 'Ji bilkul sir! Appointment trace karne ke liye please apna Appointment Reference ID batayein?'\n"
            )
        elif mem.appointment_id and not existing_app:
            context_banner += (
                f"\n=== APPOINTMENT ID #{mem.appointment_id} NOT FOUND ===\n"
                f"No appointment was found in the database under Appointment ID #{mem.appointment_id}.\n"
                f"MANDATORY: Inform the client politely that Appointment ID #{mem.appointment_id} was not found. Ask them to verify the ID or provide their registered email address.\n"
            )
        elif existing_app:
            app_id = existing_app["id"]
            prop_title = existing_app["property_title"]
            client_mail = existing_app["client_email"]
            curr_date = existing_app["appointment_date"]
            curr_time = existing_app["appointment_time"]

            if is_cancel:
                appointment_manager.cancel_appointment(app_id)
                mem.appointment_action = None
                context_banner += (
                    f"\n=== APPOINTMENT CANCELLED (ID #{app_id}) ===\n"
                    f"Appointment ID #{app_id} for {prop_title} ({curr_date} at {curr_time}) has been CANCELLED as per client request.\n"
                    f"Cancellation confirmation email dispatched to {client_mail}.\n"
                    f"MANDATORY: Confirm clearly to the client that Appointment ID #{app_id} for {prop_title} has been cancelled and confirmation email sent to {client_mail}.\n"
                )
            elif is_reschedule:
                if mem.appointment_date and mem.appointment_time:
                    avail = appointment_manager.check_availability(mem.appointment_date, mem.appointment_time)
                    if avail["is_available"] or avail.get("conflict_appointment_id") == app_id:
                        appointment_manager.reschedule_appointment(app_id, mem.appointment_date, mem.appointment_time)
                        mem.appointment_action = None
                        context_banner += (
                            f"\n=== APPOINTMENT RESCHEDULED (ID #{app_id}) ===\n"
                            f"Appointment ID #{app_id} for {prop_title} has been successfully RESCHEDULED to {mem.appointment_date} at {mem.appointment_time}.\n"
                            f"Confirmation email with updated 1-click 'Add to Google Calendar' button dispatched to {client_mail}.\n"
                            f"MANDATORY: Confirm to the client that Appointment ID #{app_id} is rescheduled to {mem.appointment_date} at {mem.appointment_time}, and updated confirmation sent to {client_mail}.\n"
                        )
                    else:
                        alt_slots = appointment_manager.get_available_slots(mem.appointment_date)
                        alt_slots = [s for s in alt_slots if s.lower() != mem.appointment_time.lower()]
                        alt_str = ", ".join(alt_slots[:3])
                        context_banner += (
                            f"\n=== RESCHEDULE SLOT OCCUPIED (ID #{app_id}) ===\n"
                            f"For Appointment ID #{app_id} ({prop_title}), requested slot {mem.appointment_time} on {mem.appointment_date} is already occupied.\n"
                            f"Available alternative slots on {mem.appointment_date}: {alt_str}.\n"
                            f"MANDATORY: Inform client that {mem.appointment_time} is busy and recommend {alt_str} on {mem.appointment_date}.\n"
                        )
                else:
                    context_banner += (
                        f"\n=== APPOINTMENT FOUND (ID #{app_id}) - REQUEST NEW SLOT ===\n"
                        f"Existing Booking Verified: Appointment ID #{app_id} for {prop_title} on {curr_date} at {curr_time}.\n"
                        f"MANDATORY: Confirm the existing booking to client: 'Ji sir! Aap ki appointment ID #{app_id} ({prop_title}) hamare paas mojood hai. Kis nayi date aur time par reschedule karna chahte hain?'\n"
                    )

    # 2. Booking Intent: Email, Date, Time & Calendar Availability
    elif is_booking_intent:
        if not mem.client_email:
            context_banner += (
                "\n=== APPOINTMENT BOOKING: EMAIL & TIME REQUIRED ===\n"
                "Client wants to book an appointment/visit.\n"
                "MANDATORY: Ask the client for their Name, Email address, and Preferred Date & Time.\n"
            )
        elif not mem.appointment_date or not mem.appointment_time:
            context_banner += (
                f"\n=== APPOINTMENT BOOKING: DATE & TIME REQUIRED ===\n"
                f"Client Email provided: {mem.client_email}\n"
                f"MANDATORY: Confirm the email address with client ('Aap ka email {mem.client_email} sahi hai sir?') and ask for their preferred Date and Time slot.\n"
            )
        elif not mem.appointment_booked:
            avail = appointment_manager.check_availability(mem.appointment_date, mem.appointment_time)
            if not avail["is_available"]:
                alt_slots = appointment_manager.get_available_slots(mem.appointment_date)
                alt_slots = [s for s in alt_slots if s.lower() != mem.appointment_time.lower()]
                alt_str = ", ".join(alt_slots[:3])
                context_banner += (
                    f"\n=== CALENDAR SLOT UNAVAILABLE (CONFLICT DETECTED) ===\n"
                    f"Requested slot: {mem.appointment_date} at {mem.appointment_time} is ALREADY OCCUPIED.\n"
                    f"Available alternative slots on SAME DATE ({mem.appointment_date}): {alt_str}\n"
                    f"MANDATORY: Inform the client that {mem.appointment_time} is busy, and proactively suggest {alt_str} on the same date.\n"
                )
            else:
                last_prop_title = mem.last_recommended_properties[0]["title"] if mem.last_recommended_properties else "Real Estate Consultation"
                auto_booked_appointment = appointment_manager.book_appointment(
                    session_id=session_id,
                    client_name=mem.client_name or "Valued Client",
                    client_email=mem.client_email,
                    city=mem.city or "Lahore",
                    property_title=last_prop_title,
                    appointment_date=mem.appointment_date,
                    appointment_time=mem.appointment_time
                )
                if auto_booked_appointment.get("success"):
                    mem.appointment_booked = True
                    mem.appointment_action = None
                    booked_id = auto_booked_appointment.get("appointment_id")
                    mem.appointment_id = booked_id
                    context_banner += (
                        f"\n=== APPOINTMENT BOOKED SUCCESSFULLY ===\n"
                        f"Appointment ID: #{booked_id} (Reference: APT-{booked_id}).\n"
                        f"Slot: {mem.appointment_date} at {mem.appointment_time} is confirmed.\n"
                        f"Confirmation email with 1-click 'Add to Google Calendar' button dispatched to {mem.client_email}.\n"
                        f"MANDATORY: Confirm booking clearly, state their Appointment ID #{booked_id}, and confirm email sent to {mem.client_email}.\n"
                        f"Tell client: 'Aap ka Appointment ID #{booked_id} hai. Main ne confirmation email aur calendar link {mem.client_email} par bhej di hai. Reschedule ya cancel karne ke liye yeh ID zaroor batayein.'\n"
                    )

    return {
        "context_banner": context_banner,
        "auto_booked_appointment": auto_booked_appointment
    }


def process_valuation_interaction(mem, normalized_msg: str) -> Optional[Dict[str, Any]]:
    """
    Handles Caller Valuation Queries like 'Mera ghar kitne ka bikega?':
    - Extracts property specs (Marla/Kanal, City, Area, Bedrooms)
    - Validates against Out-Of-Distribution (OOD) boundaries
    - Invokes LightGBM Quantile Price Valuation Regressor
    - Injects fair market value, 80% CI range, and UrduLish legal disclaimer
    """
    import re
    norm_lower = normalized_msg.lower()

    val_regex = re.compile(
        r'(?:'
        r'kitn[ea]\s*(?:ka|mein|me|par)?\s*(?:bik|sell|sale|khar|bikay|hoga)'
        r'|price\s*of\s*(?:my\s*)?(?:house|home|property|ghar|plot)'
        r'|how\s*much\s*(?:is|can|for|would)'
        r'|predict\s*(?:the\s*)?(?:property\s*|house\s*)?price'
        r'|price\s*predict'
        r'|price\s*score'
        r'|lead\s*score'
        r'|valuation'
        r'|value\s*(?:kya|kitni|estimate|check|of)'
        r'|qeemat\s*(?:kya|kitni|batao|check)'
        r'|qimat'
        r'|rate\s*(?:kya|kitna|batao|check)'
        r'|market\s*(?:rate|value|price)'
        r'|property\s*price'
        r'|house\s*price'
        r'|ghar\s*price'
        r'|bazar\s*bhav'
        r'|bhav\s*kya'
        r'|worth'
        r'|estimate'
        r'|appraisal'
        r'|bechn[aei]'
        r'|farokht'
        r'|sell\s*karna'
        r'|sell\s*my\s*house'
        r'|sell\s*house'
        r'|sale\s*karna'
        r')',
        re.IGNORECASE
    )
    has_size = bool(re.search(r'\b(?:\d+(?:\.\d+)?)\s*(?:marla|marle|kanal|kanals|مرلہ|کنال)\b', norm_lower))
    has_pricing_term = bool(re.search(r'\b(?:price|rate|value|qeemat|worth|cost|bikega|bikay|sell|sale|bhav|khar)\b', norm_lower))
    is_awaiting = getattr(mem, "awaiting_valuation_specs", False)

    if not (val_regex.search(norm_lower) or (has_size and has_pricing_term) or is_awaiting):
        return None

    # Check for prompt injection
    is_inj, inj_reason = check_prompt_injection(normalized_msg)
    if is_inj:
        mem.awaiting_valuation_specs = False
        return {
            "status": "refused",
            "reply": "Mujhe afsos hai, main safety policies ke mutabiq aisi instructions follow nahi kar sakti. Main sirf real estate khareed o farokht, valuation aur appointments mein aapki madad kar sakti hoon."
        }

    # Check if caller specifically asked for their Lead Score / CRM Priority Tier
    lead_score_query = bool(re.search(r'\b(?:lead\s*score|lead\s*quality|caller\s*score|priority\s*tier)\b', norm_lower))
    prop_val_query = bool(re.search(r'\b(?:ghar|house|property|plot|marla|kanal|price|qeemat|rate|bikega|bikay|worth|cost|valuation)\b', norm_lower))
    if lead_score_query and not (prop_val_query or has_size):
        from crm_lead_scorer import CRMLeadScorer
        scorer = CRMLeadScorer.get_instance()
        lead_input = {
            "budget_pkr": mem.budget_pkr or 35000000.0,
            "num_calls": max(1, len(mem.history) // 2),
            "avg_call_duration_mins": 4.5,
            "response_time_hours": 1.5,
            "days_since_first_contact": 1.0,
            "followup_count": 1,
            "preferred_city": mem.city or "Lahore",
            "purpose": mem.purpose or "Buy",
            "property_type_preferred": mem.property_type or "House",
            "visit_booked": "Yes" if mem.appointment_booked else "No",
            "client_email": mem.client_email
        }
        res = scorer.predict_score(lead_input, client_email=mem.client_email)
        score_pct = int(res["conversion_probability"] * 100)
        tier = res["priority_tier"]
        tier_text = "Hot Lead" if tier == "Hot" else ("Warm Lead" if tier == "Warm" else "Cold Lead")
        sla = res["action_sla"]
        lead_reply = (
            f"Aap ka current CRM lead score {score_pct} percent calculate hua hai aur aapka status '{tier_text}' hai. "
            f"Hamari sales team ka action time {sla} hai. Main aapki real estate mein mazeed kis tarah madad kar sakti hoon?"
        )
        return {
            "status": "lead_score",
            "reply": lead_reply
        }

    # Extract size: e.g. "10 marla", "5 marla", "1 kanal", "2 kanal"
    marla_val = None
    kanal_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kanal|kanals|کنال)', norm_lower)
    if kanal_match:
        marla_val = float(kanal_match.group(1)) * 20.0
    else:
        marla_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:marla|marle|مرلہ|مرلے)', norm_lower)
        if marla_match:
            marla_val = float(marla_match.group(1))

    # Check city
    city = None
    for c in ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad"]:
        if c.lower() in norm_lower:
            city = c
            break
    if not city:
        city = mem.city or "Lahore"

    # Check area
    area = None
    common_areas = ["DHA Phase 6", "DHA Phase 5", "Bahria Town", "Gulberg", "F-7", "F-10", "E-11", "Clifton", "Johar Town", "Model Town", "G-11", "I-8", "Cantt"]
    for a in common_areas:
        if a.lower() in norm_lower:
            area = a
            break
    if not area:
        area = mem.area or "DHA Phase 6"

    # Check bedrooms
    bed_match = re.search(r'(\d+)\s*(?:bed|bedroom|kamray|kamre)', norm_lower)
    bedrooms = int(bed_match.group(1)) if bed_match else (5 if (marla_val or 10) >= 20 else 4 if (marla_val or 10) >= 10 else 3)
    bathrooms = bedrooms

    # If caller hasn't given size yet
    if marla_val is None:
        mem.awaiting_valuation_specs = True
        return {
            "status": "prompt_more",
            "reply": "Ji bilkul! Main aapke ghar ki exact market valuation calculate kar sakti hoon. Barah-e-karam mujhe batayein ke aap ka ghar kitne marla ka hai, kis shehar aur society mein waqia hai, aur kitne bedrooms hain?"
        }

    mem.awaiting_valuation_specs = False

    prop_payload = {
        "city": city,
        "location": area,
        "plot_size_marla": marla_val,
        "property_type": "House",
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "covered_area_sqft": marla_val * 225.0 * 0.75,
        "year_built": 2021,
        "amenities": ["24/7 security", "gated community"]
    }

    # OOD Check
    is_ood, ood_reason = check_property_ood(prop_payload)
    if is_ood:
        return {
            "status": "refused_ood",
            "reply": f"Hum maazrat chahte hain! Hamara statistical valuation model sirf operational boundaries (1 se 100 Marla aur supported cities: Lahore, Karachi, Islamabad, Rawalpindi, Faisalabad) ke liye trained hai. {ood_reason}"
        }

    # Model inference
    val_res = predict_property_price(prop_payload, client_email=mem.client_email)
    mid_fmt = val_res["fair_market_price_formatted"]
    low_fmt = val_res["confidence_interval_80"]["lower_bound_formatted"]
    high_fmt = val_res["confidence_interval_80"]["upper_bound_formatted"]

    reply = (
        f"Aap ke {marla_val:.0f} Marla ghar {area} {city} ki fair market value taqreeban {mid_fmt} banti hai. "
        f"Hamare statistical 80 percent confidence interval model ke mutabiq yeh {low_fmt} se {high_fmt} ke darmiyan sell ho sakta hai. "
        f"Qanooni wazahat: {DISCLAIMER_TEXT_UR}"
    )

    return {
        "status": "success",
        "val_res": val_res,
        "reply": reply
    }



# Pydantic Schemas
class DirectLeadScoreRequest(BaseModel):
    budget_pkr: Optional[float] = 35000000.0
    num_calls: Optional[int] = 2
    avg_call_duration_mins: Optional[float] = 5.0
    response_time_hours: Optional[float] = 2.0
    days_since_first_contact: Optional[float] = 2.0
    followup_count: Optional[int] = 1
    lead_source: Optional[str] = "Inbound Call / Walk-in"
    preferred_city: Optional[str] = "Lahore"
    purpose: Optional[str] = "Buy"
    property_type_preferred: Optional[str] = "House"
    visit_booked: Optional[str] = "No"
    visit_completed: Optional[str] = "No"
    objection_raised: Optional[str] = "None"
    client_email: Optional[str] = None


class DirectValuationRequest(BaseModel):
    city: str = "Lahore"
    location: Optional[str] = "DHA Phase 6"
    plot_size_marla: float = 10.0
    property_type: Optional[str] = "House"
    bedrooms: Optional[int] = 4
    bathrooms: Optional[int] = 4
    covered_area_sqft: Optional[float] = 2500.0
    year_built: Optional[int] = 2021
    is_corner: Optional[int] = 0
    is_park_facing: Optional[int] = 0
    is_main_boulevard: Optional[int] = 0
    amenities: Optional[List[str]] = []
    listed_price_pkr: Optional[float] = None
    client_email: Optional[str] = None


class CallEndedRequest(BaseModel):
    session_id: str
    client_email: Optional[str] = None
    client_name: Optional[str] = None
    city: Optional[str] = None
    budget_pkr: Optional[float] = None
    call_duration_seconds: Optional[float] = None
    num_calls: Optional[int] = None
    followup_count: Optional[int] = None
    days_since_first_contact: Optional[float] = None
    response_time_hours: Optional[float] = None
    visit_booked: Optional[str] = None
    visit_completed: Optional[str] = None
    objection_raised: Optional[str] = None
    purpose: Optional[str] = None
    property_type: Optional[str] = None


class ChatRequest(BaseModel):
    session_id: Optional[str] = "default_session"
    message: str
    stream: bool = False

class BookAppointmentRequest(BaseModel):
    session_id: Optional[str] = "api_session"
    client_name: Optional[str] = "Valued Client"
    client_email: str
    client_phone: Optional[str] = "Email Priority Client"
    city: Optional[str] = "Lahore"
    property_title: Optional[str] = "General Real Estate Consultation"
    appointment_date: Optional[str] = "Tomorrow"
    appointment_time: Optional[str] = "11:00 AM"
    notes: Optional[str] = "Site visit & consultation."

class RescheduleAppointmentRequest(BaseModel):
    appointment_id: int
    new_date: str
    new_time: str

class CancelAppointmentRequest(BaseModel):
    appointment_id: int

class CreateFollowupRequest(BaseModel):
    client_email: Optional[str] = "client@realestatehub.pk"
    client_name: Optional[str] = "Valued Client"
    reminder_type: str = "Pre-Visit Call Reminder"
    reminder_date: str = "Tomorrow"
    notes: Optional[str] = "Follow-up consultation call."

class CompleteFollowupRequest(BaseModel):
    reminder_id: int

class OpenAICompletionMessage(BaseModel):
    role: str
    content: str

class OpenAICompletionRequest(BaseModel):
    model: Optional[str] = "urdu-real-estate-llm"
    messages: List[OpenAICompletionMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.6
    max_tokens: Optional[int] = 300
    call: Optional[Dict[str, Any]] = None
    tools: Optional[List[Any]] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class AddPropertyRequest(BaseModel):
    title: str
    city: str
    area: str
    price_pkr: float
    size_val: float
    size_unit: str = "Marla"
    bedrooms: int = 0
    bathrooms: int = 0
    purpose: str = "Sale"
    property_type: str = "House"
    developer: str = "Private Developer"
    description: Optional[str] = ""
    amenities: Optional[List[str]] = []
    nearby_schools: Optional[str] = ""
    nearby_hospitals: Optional[str] = ""
    has_payment_plan: Optional[bool] = False
    down_payment_pkr: Optional[float] = None
    monthly_installment_pkr: Optional[float] = None
    duration_months: Optional[int] = 36
    possession_months: Optional[int] = 18

# Serve static directory if available
from pathlib import Path
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ==========================================
# AUTHENTICATION & SECURITY DEPENDENCIES
# ==========================================
def verify_admin_token(authorization: Optional[str] = Header(None)) -> bool:
    """
    Verifies Bearer token for protected administrative and CRM endpoints.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required. Please log in."
        )
    token = authorization.replace("Bearer ", "").strip()
    if token != config.ADMIN_SESSION_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token."
        )
    return True

@app.post("/api/v1/auth/login")
async def login_endpoint(req: LoginRequest):
    """Simple, secure authentication for dashboard administration."""
    if req.username == config.ADMIN_USERNAME and req.password == config.ADMIN_PASSWORD:
        return {
            "success": True,
            "message": "Login successful",
            "token": config.ADMIN_SESSION_TOKEN,
            "user": {
                "username": config.ADMIN_USERNAME,
                "role": "admin"
            }
        }
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password"
    )

@app.get("/api/v1/auth/verify")
async def verify_auth_endpoint(authorization: Optional[str] = Header(None)):
    """Validates whether client session token is active."""
    if not authorization:
        return {"valid": False, "error": "No token provided"}
    token = authorization.replace("Bearer ", "").strip()
    return {"valid": token == config.ADMIN_SESSION_TOKEN}

@app.post("/api/v1/auth/logout")
async def logout_endpoint():
    return {"success": True, "message": "Logged out successfully"}

# ==========================================
# PAGE ROUTING (Dashboard, Login, Website)
# ==========================================
@app.get("/")
def read_root():
    index_file = static_dir / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return {"message": "UrduLish Real Estate Voice Agent API Server is running."}

@app.get("/login")
def read_login():
    login_file = static_dir / "login.html"
    if login_file.exists():
        with open(login_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return JSONResponse(status_code=404, content={"detail": "Login page not found."})

@app.get("/website")
def read_website():
    web_file = static_dir / "website.html"
    if web_file.exists():
        with open(web_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return JSONResponse(status_code=404, content={"detail": "Website page not found."})

@app.get("/ml-dashboard")
def read_ml_dashboard():
    ml_file = static_dir / "ml_dashboard.html"
    if ml_file.exists():
        with open(ml_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return JSONResponse(status_code=404, content={"detail": "ML Dashboard page not found."})

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    fav = static_dir / "favicon.ico"
    if fav.exists():
        return FileResponse(fav)
    return JSONResponse(status_code=404, content={"detail": "Favicon not found"})

# ==========================================
# VAPI SECURITY CHECKPOINT DECORATOR
# ==========================================
def check_if_it_is_vapi(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        # 1. Look for the password in the request header
        request: Request = kwargs.get("request")
        if not request:
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

        auth_header = request.headers.get("Authorization") if request else None
        
        # Vapi sends it like: "Bearer <SUPER_SECRET>"
        expected_format = f"Bearer {config.SUPER_SECRET}"
        
        # 2. If it's missing or wrong, kick them out!
        if not auth_header or auth_header != expected_format:
            return JSONResponse({"error": "Go away, you are not Vapi!"}, status_code=401)
            
        # 3. If it matches, let them in
        if inspect.iscoroutinefunction(f):
            return await f(*args, **kwargs)
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# VAPI & OPENAI STREAMING HELPERS
# ==========================================
def create_openai_sse_stream(text: str, model: str):
    """
    Yields chunks formatted for OpenAI SSE streaming protocol compatible with Vapi.
    Streams word-by-word with finish_reason: None, followed by terminal stop delta.
    """
    created_ts = int(time.time())
    words = text.split(" ")
    for w in words:
        if not w:
            continue
        chunk = {
            "id": f"chatcmpl-{created_ts}",
            "object": "chat.completion.chunk",
            "created": created_ts,
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {"content": w + " "},
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(chunk)}\n\n"
    
    end_chunk = {
        "id": f"chatcmpl-{created_ts}",
        "object": "chat.completion.chunk",
        "created": created_ts,
        "model": model,
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "stop"
        }]
    }
    yield f"data: {json.dumps(end_chunk)}\n\n"
    yield "data: [DONE]\n\n"

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
    "Content-Type": "text/event-stream"
}

# This is the path the AI agent calls mid-phone call for Tool Calling
@app.post("/vapi-voice-tool")
async def voice_agent_helper(request: Request):
    """
    Vapi Mid-Call Tool Calling webhook for Property Valuation & Lead Scoring.
    Handles Vapi function calls (e.g., predict_price, get_property_valuation).
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    tool_calls = []
    if isinstance(body, dict):
        if "message" in body and isinstance(body["message"], dict):
            tool_calls = body["message"].get("toolCalls") or body["message"].get("toolCallList") or []
        elif "toolCalls" in body:
            tool_calls = body.get("toolCalls") or []

    if tool_calls:
        results = []
        for tc in tool_calls:
            call_id = tc.get("id") or tc.get("toolCallId") or "call_default"
            func = tc.get("function", {})
            args = func.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}

            plot_size = float(args.get("plot_size_marla") or args.get("marla") or 10.0)
            city = str(args.get("city") or "Lahore")
            loc = str(args.get("location") or args.get("area") or "DHA Phase 6")
            beds = int(args.get("bedrooms") or 4)

            prop_data = {
                "city": city,
                "location": loc,
                "plot_size_marla": plot_size,
                "bedrooms": beds,
                "bathrooms": beds,
                "covered_area_sqft": plot_size * 225.0 * 0.75,
                "year_built": 2021
            }
            val_res = predict_property_price(prop_data)
            reply = (
                f"Aap ke {plot_size:.0f} Marla ghar {loc} {city} ki fair market value taqreeban {val_res['fair_market_price_formatted']} banti hai. "
                f"Hamare 80 percent confidence interval model ke mutabiq yeh {val_res['confidence_interval_80']['lower_bound_formatted']} se {val_res['confidence_interval_80']['upper_bound_formatted']} ke darmiyan sell ho sakta hai. "
                f"Qanooni wazahat: {DISCLAIMER_TEXT_UR}"
            )
            results.append({"toolCallId": call_id, "result": reply})

        return JSONResponse({"results": results})

    # Direct fallback if called with raw JSON arguments
    plot_size = float(body.get("plot_size_marla") or body.get("marla") or 10.0)
    city = str(body.get("city") or "Lahore")
    loc = str(body.get("location") or body.get("area") or "DHA Phase 6")
    val_res = predict_property_price({
        "city": city,
        "location": loc,
        "plot_size_marla": plot_size,
        "bedrooms": int(body.get("bedrooms") or 4),
        "bathrooms": int(body.get("bedrooms") or 4),
        "covered_area_sqft": plot_size * 225.0 * 0.75,
        "year_built": 2021
    })
    reply = (
        f"Aap ke {plot_size:.0f} Marla ghar {loc} {city} ki fair market value taqreeban {val_res['fair_market_price_formatted']} banti hai. "
        f"Hamare 80 percent confidence interval model ke mutabiq yeh {val_res['confidence_interval_80']['lower_bound_formatted']} se {val_res['confidence_interval_80']['upper_bound_formatted']} ke darmiyan sell ho sakta hai. "
        f"Qanooni wazahat: {DISCLAIMER_TEXT_UR}"
    )
    return JSONResponse({"result": reply, "results": [{"toolCallId": "default", "result": reply}]})

# ==========================================
# 1. VAPI CUSTOM LLM COMPATIBLE ENDPOINT (/v1/chat/completions)
# ==========================================
@app.post("/v1/chat/completions")
# @check_if_it_is_vapi
async def open_ai_chat_completions(req: OpenAICompletionRequest, request: Request):
    """
    Standard OpenAI-compatible completions endpoint designed specifically for
    Vapi Custom LLM Webhook Integration. Handles STT normalization, interruptions, live email automation & CRM logging.
    """
    start_time = time.time()
    
    # Extract unique call ID from Vapi headers or request payload
    vapi_call_id = (
        request.headers.get("x-vapi-call-id")
        or request.headers.get("x-call-id")
        or (req.call.get("id") if req.call else None)
        or "vapi_session_active"
    )
    
    # Extract user messages
    user_msgs = [m.content for m in req.messages if m.role == "user"]
    last_user_msg = user_msgs[-1] if user_msgs else "Assalam-o-Alaikum"
    
    # If this is the start of a call (1 user message or empty), reset memory so it starts 100% fresh!
    if len(user_msgs) <= 1:
        reset_session_memory(vapi_call_id)

    mem = get_session_memory(vapi_call_id)
    
    # STT Pre-processing & Normalization (lahorayy -> Lahore, karor -> crore, etc.)
    stt_info = STTProcessor.normalize_transcript(last_user_msg)
    normalized_msg = stt_info["normalized_transcript"]

    # Interruption handling
    if stt_info["is_interruption"]:
        interruption_reply = "Ji bilkul sir! Main sun rahi hoon, aap bataiye."
        if req.stream:
            return StreamingResponse(
                create_openai_sse_stream(interruption_reply, req.model),
                media_type="text/event-stream",
                headers=SSE_HEADERS
            )
        else:
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": req.model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": interruption_reply}, "finish_reason": "stop"}]
            }

    # 1. Prompt Injection Defense
    is_inj, inj_reason = check_prompt_injection(normalized_msg)
    if is_inj:
        refusal_reply = "Mujhe afsos hai, main safety policies ke mutabiq aisi instructions follow nahi kar sakti. Main sirf real estate khareed o farokht, valuation aur appointments mein aapki madad kar sakti hoon."
        if req.stream:
            return StreamingResponse(
                create_openai_sse_stream(refusal_reply, req.model),
                media_type="text/event-stream",
                headers=SSE_HEADERS
            )
        else:
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": req.model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": refusal_reply}, "finish_reason": "stop"}]
            }

    # 2. Valuation Query Flow ("Mera ghar kitne ka bikega?", "predict price score", etc.)
    val_flow = process_valuation_interaction(mem, normalized_msg)
    if val_flow:
        val_reply = val_flow["reply"]
        mem.add_turn("user", normalized_msg)
        mem.add_turn("assistant", val_reply)
        caller_email = mem.client_email or "guest_caller@realestatehub.pk"
        crm_store.log_transcript(
            session_id=vapi_call_id,
            client_email=caller_email,
            raw_transcript=last_user_msg,
            normalized_transcript=normalized_msg,
            agent_response=val_reply,
            latency_sec=round(time.time() - start_time, 3)
        )
        if req.stream:
            return StreamingResponse(
                create_openai_sse_stream(val_reply, req.model),
                media_type="text/event-stream",
                headers=SSE_HEADERS
            )
        else:
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": req.model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": val_reply}, "finish_reason": "stop"}]
            }

    # Update memory with normalized text
    mem.add_turn("user", normalized_msg)

    # Process Appointment Controller (Intent detection, repeat caller lookup, slot availability check, email confirmation)
    app_flow = process_appointment_interaction(vapi_call_id, mem, normalized_msg)
    auto_booked_appointment = app_flow["auto_booked_appointment"]
    appointment_banner = app_flow["context_banner"]

    # Hybrid Retrieval (SQL + RAG)
    rec_data = rec_engine.get_recommendations(mem, normalized_msg)
    context_combined = rec_data["formatted_context"]
    if appointment_banner:
        context_combined = f"{appointment_banner}\n\n{context_combined}"
    
    # Build System Prompt
    sys_prompt = get_system_prompt_with_context(context_combined, mem.get_summary())
    
    messages_payload = [{"role": m.role, "content": m.content if m.content != last_user_msg else normalized_msg} for m in req.messages if m.role != "system"]

    full_response = llm_client.generate_response(messages_payload, sys_prompt, temperature=req.temperature, stream=False)
    
    # Synchronize email from LLM response if memory didn't catch it
    if not mem.client_email:
        extracted_from_llm = extract_spoken_email(full_response)
        if extracted_from_llm:
            mem.client_email = extracted_from_llm

    # Layer 2 Guarantee Fail-Safe: Ensure dispatches trigger if confirmed in LLM text!
    confirm_phrases = ["confirmation mail", "confirmation email", "bhej di hai", "bhej diya hai", "schedule kar di", "calendar invite", "appointment book"]
    if any(phrase in full_response.lower() for phrase in confirm_phrases) and not mem.appointment_booked:
        target_email = mem.client_email or "samiworkspace11@gmail.com"
        mem.client_email = target_email
        last_prop_title = mem.last_recommended_properties[0]["title"] if mem.last_recommended_properties else "Real Estate Consultation"
        auto_booked_appointment = appointment_manager.book_appointment(
            session_id=vapi_call_id,
            client_name=mem.client_name or "Valued Client",
            client_email=target_email,
            city=mem.city or "Lahore",
            property_title=last_prop_title,
            appointment_date=mem.appointment_date or "Tomorrow",
            appointment_time=mem.appointment_time or "11:00 AM"
        )
        if auto_booked_appointment.get("success"):
            mem.appointment_booked = True
            mem.appointment_action = None
            mem.appointment_id = auto_booked_appointment.get("appointment_id")

    latency = round(time.time() - start_time, 3)

    # CRM Store Logging (Transcripts & Client Preferences Profile)
    caller_email = mem.client_email or "guest_caller@realestatehub.pk"
    crm_store.log_transcript(
        session_id=vapi_call_id,
        client_email=caller_email,
        raw_transcript=last_user_msg,
        normalized_transcript=normalized_msg,
        agent_response=full_response,
        latency_sec=latency
    )
    crm_store.update_client_preferences(
        client_email=caller_email,
        memory_summary={
            "city": mem.city,
            "area": mem.area,
            "budget_pkr": mem.budget_pkr,
            "bedrooms": mem.bedrooms,
            "property_type": mem.property_type,
            "purpose": mem.purpose
        }
    )

    if req.stream:
        return StreamingResponse(
            create_openai_sse_stream(full_response, req.model),
            media_type="text/event-stream",
            headers=SSE_HEADERS
        )
    else:
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": req.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": full_response
                },
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            "meta": {
                "latency_sec": latency,
                "retrieved_properties_count": len(rec_data["properties"]),
                "few_shot_guidance": rec_data.get("few_shot_exemplar"),
                "memory_summary": mem.get_summary(),
                "stt_normalized_text": normalized_msg
            }
        }

# ==========================================
# 2. REST & WEB DASHBOARD ENDPOINTS
# ==========================================
@app.post("/api/v1/chat")
async def chat_endpoint(req: ChatRequest):
    start_time = time.time()
    stt_info = STTProcessor.normalize_transcript(req.message)
    normalized_msg = stt_info["normalized_transcript"]

    mem = get_session_memory(req.session_id)
    
    if stt_info["is_interruption"]:
        interruption_reply = "Ji bilkul sir! Main sun rahi hoon, aap bataiye."
        return {
            "session_id": req.session_id,
            "reply": interruption_reply,
            "memory_summary": mem.get_summary(),
            "matched_properties": [],
            "assigned_agent": get_agent_by_city(mem.city or "Lahore"),
            "retrieved_rag_context": "Interruption signal detected."
        }

    # 1. Prompt Injection Defense
    is_inj, inj_reason = check_prompt_injection(normalized_msg)
    if is_inj:
        refusal_reply = "Mujhe afsos hai, main safety policies ke mutabiq aisi instructions follow nahi kar sakti. Main sirf real estate khareed o farokht, valuation aur appointments mein aapki madad kar sakti hoon."
        return {
            "session_id": req.session_id,
            "reply": refusal_reply,
            "memory_summary": mem.get_summary(),
            "matched_properties": [],
            "assigned_agent": get_agent_by_city(mem.city or "Lahore"),
            "retrieved_rag_context": "Prompt injection detected & refused."
        }

    # 2. Valuation Query Flow ("Mera ghar kitne ka bikega?", etc.)
    val_flow = process_valuation_interaction(mem, normalized_msg)
    if val_flow:
        val_reply = val_flow["reply"]
        mem.add_turn("user", normalized_msg)
        mem.add_turn("assistant", val_reply)
        caller_email = mem.client_email or "guest_caller@realestatehub.pk"
        crm_store.log_transcript(
            session_id=req.session_id,
            client_email=caller_email,
            raw_transcript=req.message,
            normalized_transcript=normalized_msg,
            agent_response=val_reply,
            latency_sec=round(time.time() - start_time, 3)
        )
        return {
            "session_id": req.session_id,
            "reply": val_reply,
            "memory_summary": mem.get_summary(),
            "matched_properties": [],
            "assigned_agent": get_agent_by_city(mem.city or "Lahore"),
            "retrieved_rag_context": "Statistical Property Valuation Engine (Quantile LightGBM)"
        }

    mem.add_turn("user", normalized_msg)

    # Process Appointment Controller (Intent detection, repeat caller lookup, slot availability check, email confirmation)
    app_flow = process_appointment_interaction(req.session_id, mem, normalized_msg)
    auto_booked_appointment = app_flow["auto_booked_appointment"]
    appointment_banner = app_flow["context_banner"]

    rec_data = rec_engine.get_recommendations(mem, normalized_msg)
    context_combined = rec_data["formatted_context"]
    if appointment_banner:
        context_combined = f"{appointment_banner}\n\n{context_combined}"

    sys_prompt = get_system_prompt_with_context(context_combined, mem.get_summary())
    
    response = llm_client.generate_response(mem.history, sys_prompt, stream=False)
    
    # Synchronize email from LLM response if memory didn't catch it
    if not mem.client_email:
        extracted_from_llm = extract_spoken_email(response)
        if extracted_from_llm:
            mem.client_email = extracted_from_llm

    # Layer 2 Guarantee Fail-Safe: Ensure dispatches trigger if confirmed in LLM text!
    confirm_phrases = ["confirmation mail", "confirmation email", "bhej di hai", "bhej diya hai", "schedule kar di", "calendar invite", "appointment book"]
    if any(phrase in response.lower() for phrase in confirm_phrases) and not mem.appointment_booked:
        target_email = mem.client_email or "samiworkspace11@gmail.com"
        mem.client_email = target_email
        last_prop_title = mem.last_recommended_properties[0]["title"] if mem.last_recommended_properties else "Real Estate Consultation"
        auto_booked_appointment = appointment_manager.book_appointment(
            session_id=req.session_id,
            client_name=mem.client_name or "Valued Client",
            client_email=target_email,
            city=mem.city or "Lahore",
            property_title=last_prop_title,
            appointment_date=mem.appointment_date or "Tomorrow",
            appointment_time=mem.appointment_time or "11:00 AM"
        )
        if auto_booked_appointment.get("success"):
            mem.appointment_booked = True
            mem.appointment_action = None
            mem.appointment_id = auto_booked_appointment.get("appointment_id")

    mem.add_turn("assistant", response)

    latency = round(time.time() - start_time, 3)

    # CRM Store Logging (Transcripts & Client Preferences Profile)
    caller_email = mem.client_email or "guest_caller@realestatehub.pk"
    crm_store.log_transcript(
        session_id=req.session_id,
        client_email=caller_email,
        raw_transcript=req.message,
        normalized_transcript=normalized_msg,
        agent_response=response,
        latency_sec=latency
    )
    crm_store.update_client_preferences(
        client_email=caller_email,
        memory_summary={
            "city": mem.city,
            "area": mem.area,
            "budget_pkr": mem.budget_pkr,
            "bedrooms": mem.bedrooms,
            "property_type": mem.property_type,
            "purpose": mem.purpose
        }
    )

    return {
        "session_id": req.session_id,
        "reply": response,
        "memory_summary": mem.get_summary(),
        "matched_properties": rec_data["properties"],
        "assigned_agent": rec_data["agent"],
        "few_shot_guidance": rec_data.get("few_shot_exemplar"),
        "retrieved_rag_context": rec_data["formatted_context"],
        "stt_normalized_text": normalized_msg,
        "booked_appointment": auto_booked_appointment
    }


# ==========================================
# WEEK 8 ML/MLOPS INTEGRATION ENDPOINTS
# ==========================================
@app.post("/predict/price")
async def predict_price_endpoint(request: Request):
    """
    Direct Property Price Valuation Endpoint:
    Accepts both standard DirectValuationRequest JSON and Vapi toolCalls webhooks mid-call.
    Returns Fair Market Price, 80% Confidence Interval, and Mandatory Legal Disclaimer.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    tool_calls = []
    if isinstance(body, dict):
        if "message" in body and isinstance(body["message"], dict):
            tool_calls = body["message"].get("toolCalls") or body["message"].get("toolCallList") or []
        elif "toolCalls" in body:
            tool_calls = body.get("toolCalls") or []

    if tool_calls:
        results = []
        for tc in tool_calls:
            call_id = tc.get("id") or tc.get("toolCallId") or "call_default"
            func = tc.get("function", {})
            args = func.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}
            plot_size = float(args.get("plot_size_marla") or args.get("marla") or 10.0)
            city = str(args.get("city") or "Lahore")
            loc = str(args.get("location") or args.get("area") or "DHA Phase 6")
            beds = int(args.get("bedrooms") or 4)
            prop_data = {
                "city": city,
                "location": loc,
                "plot_size_marla": plot_size,
                "bedrooms": beds,
                "bathrooms": beds,
                "covered_area_sqft": plot_size * 225.0 * 0.75,
                "year_built": 2021
            }
            val_res = predict_property_price(prop_data)
            reply = (
                f"Aap ke {plot_size:.0f} Marla ghar {loc} {city} ki fair market value taqreeban {val_res['fair_market_price_formatted']} banti hai. "
                f"Hamare 80 percent confidence interval model ke mutabiq yeh {val_res['confidence_interval_80']['lower_bound_formatted']} se {val_res['confidence_interval_80']['upper_bound_formatted']} ke darmiyan sell ho sakta hai. "
                f"Qanooni wazahat: {DISCLAIMER_TEXT_UR}"
            )
            results.append({"toolCallId": call_id, "result": reply})
        return {"results": results}

    # Standard direct API call
    res = predict_property_price(body, client_email=body.get("client_email"))
    return res


@app.post("/predict/lead-score")
async def predict_lead_score_endpoint(req: DirectLeadScoreRequest):
    """
    Direct Lead Scoring Endpoint:
    Returns Lead Conversion Probability, Priority Tier (Hot/Warm/Cold), and Action SLA.
    """
    res = crm_lead_scorer.predict_score(req.model_dump(), client_email=req.client_email)
    return res


@app.post("/api/v1/voice/call-ended")
async def call_ended_endpoint(req: CallEndedRequest):
    """
    Task 4 End-of-Call Webhook:
    1. Compiles call data and scores inbound caller using champion LGBM lead model.
    2. Persists ML lead scores into crm_client_preferences.
    3. If Hot Lead (score >= 50% or Hot tier), immediately dispatches urgent email alert to assigned city broker.
    """
    mem = get_session_memory(req.session_id)
    email = (req.client_email or mem.client_email or "guest_caller@realestatehub.pk").strip()
    city = req.city or mem.city or "Lahore"
    budget = float(req.budget_pkr or mem.budget_pkr or 35000000.0)
    dur_mins = float(req.call_duration_seconds / 60.0) if req.call_duration_seconds else 5.0
    num_calls = int(req.num_calls or max(1, len(mem.history) // 2))
    followups = int(req.followup_count or 1)
    days_contact = float(req.days_since_first_contact or 1.0)
    resp_time = float(req.response_time_hours or 1.0)
    v_booked = req.visit_booked or ("Yes" if mem.appointment_booked else "No")
    v_completed = req.visit_completed or "No"
    objection = req.objection_raised or "None"
    purpose = req.purpose or mem.purpose or "Buy"
    prop_type = req.property_type or mem.property_type or "House"

    lead_payload = {
        "budget_pkr": budget,
        "num_calls": num_calls,
        "avg_call_duration_mins": dur_mins,
        "response_time_hours": resp_time,
        "days_since_first_contact": days_contact,
        "followup_count": followups,
        "preferred_city": city,
        "purpose": purpose,
        "property_type_preferred": prop_type,
        "visit_booked": v_booked,
        "visit_completed": v_completed,
        "objection_raised": objection,
        "lead_source": "Inbound Call / Walk-in"
    }

    score_result = crm_lead_scorer.predict_score(lead_payload, client_email=email)
    score_pct = float(score_result.get("conversion_probability_pct", 0.0))
    tier = str(score_result.get("priority_tier", "❄️ Cold"))
    action = str(score_result.get("recommended_action", "Enroll in newsletter"))

    # Update preferences in CRM store
    crm_store.update_client_preferences(
        client_email=email,
        memory_summary={
            "city": city,
            "budget_pkr": budget,
            "property_type": prop_type,
            "purpose": purpose,
            "lead_score_pct": score_pct,
            "priority_tier": tier,
            "recommended_action": action,
            "lead_source": "Inbound Call / Walk-in",
            "objection_raised": objection,
            "avg_call_duration_mins": dur_mins,
            "num_calls": num_calls,
            "response_time_hours": resp_time,
            "days_since_first_contact": days_contact,
            "followup_count": followups,
            "visit_booked": v_booked,
            "visit_completed": v_completed
        }
    )

    # Hot Lead Email Alert
    hot_lead_email_sent = False
    assigned_agent = get_agent_by_city(city)
    is_hot = (score_pct >= 50.0) or ("Hot" in tier)

    if is_hot:
        email_res = email_service.send_hot_lead_alert(
            client_email=email,
            lead_score_pct=score_pct,
            priority_tier=tier,
            recommended_action=action,
            city=city,
            budget_pkr=budget,
            property_type=prop_type,
            assigned_employee_email=assigned_agent.get("email"),
            assigned_employee_name=assigned_agent.get("name")
        )
        hot_lead_email_sent = email_res.get("success", False)

    return {
        "status": "success",
        "session_id": req.session_id,
        "client_email": email,
        "lead_score": score_result,
        "is_hot_lead": is_hot,
        "hot_lead_email_sent": hot_lead_email_sent,
        "assigned_agent": assigned_agent
    }


# --- DAY 4 APPOINTMENT MANAGEMENT ENDPOINTS ---
@app.post("/api/v1/appointments/book")
async def book_appointment_endpoint(req: BookAppointmentRequest):
    res = appointment_manager.book_appointment(
        session_id=req.session_id,
        client_name=req.client_name,
        client_email=req.client_email,
        client_phone=req.client_phone,
        city=req.city,
        property_title=req.property_title,
        appointment_date=req.appointment_date,
        appointment_time=req.appointment_time,
        notes=req.notes
    )
    return res

@app.post("/api/v1/appointments/reschedule")
async def reschedule_appointment_endpoint(req: RescheduleAppointmentRequest):
    res = appointment_manager.reschedule_appointment(
        appointment_id=req.appointment_id,
        new_date=req.new_date,
        new_time=req.new_time
    )
    return res

@app.post("/api/v1/appointments/cancel")
async def cancel_appointment_endpoint(req: CancelAppointmentRequest):
    res = appointment_manager.cancel_appointment(appointment_id=req.appointment_id)
    return res

@app.get("/api/v1/appointments", dependencies=[Depends(verify_admin_token)])
async def list_appointments_endpoint():
    apps = appointment_manager.list_appointments(limit=50)
    return {"count": len(apps), "appointments": apps}

# --- CRM LOGGING STORE REST ENDPOINTS ---
@app.get("/api/v1/crm/transcripts", dependencies=[Depends(verify_admin_token)])
async def get_crm_transcripts():
    logs = crm_store.get_transcripts(limit=50)
    return {"count": len(logs), "transcripts": logs}

@app.get("/api/v1/crm/preferences", dependencies=[Depends(verify_admin_token)])
async def get_crm_preferences():
    prefs = crm_store.get_preferences(limit=50)
    return {"count": len(prefs), "preferences": prefs}

@app.get("/api/v1/crm/history", dependencies=[Depends(verify_admin_token)])
async def get_crm_history():
    history = crm_store.get_appointment_history(limit=50)
    return {"count": len(history), "history": history}

@app.get("/api/v1/crm/followups", dependencies=[Depends(verify_admin_token)])
async def get_crm_followups(status: Optional[str] = None):
    reminders = crm_store.get_followups(status=status, limit=50)
    return {"count": len(reminders), "followups": reminders}

@app.post("/api/v1/crm/followups/create", dependencies=[Depends(verify_admin_token)])
async def create_crm_followup(req: CreateFollowupRequest):
    res = crm_store.create_followup_reminder(
        client_email=req.client_email or "client@realestatehub.pk",
        client_name=req.client_name,
        reminder_type=req.reminder_type,
        reminder_date=req.reminder_date,
        notes=req.notes or ""
    )
    return res


@app.get("/api/v1/ml/audit-logs")
async def get_ml_audit_logs(limit: int = 50, ood_only: bool = False):
    """
    Returns audit trail records from model_prediction_logs for real-time governance,
    inspection of OOD refusals, and accuracy tracking.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM model_prediction_logs"
    params = []
    if ood_only:
        query += " WHERE is_ood = 1"
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    
    cursor.execute("SELECT COUNT(*) as total FROM model_prediction_logs")
    total_preds = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) as ood_cnt FROM model_prediction_logs WHERE is_ood = 1")
    ood_preds = cursor.fetchone()["ood_cnt"]
    conn.close()
    return {
        "count": len(rows),
        "total_predictions": total_preds,
        "ood_predictions": ood_preds,
        "logs": rows
    }


@app.get("/api/v1/ml/leads-inbox")
async def get_ml_leads_inbox(city: Optional[str] = None, tier: Optional[str] = None):
    """
    Returns prioritized sales leads from crm_client_preferences enriched with
    ML conversion probabilities, priority tiers (Hot/Warm/Cold), and prescribed SLAs.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM crm_client_preferences"
    clauses = []
    params = []
    if city and city != "All":
        clauses.append("LOWER(preferred_city) = LOWER(?)")
        params.append(city)
    if tier and tier != "All":
        clauses.append("priority_tier LIKE ?")
        params.append(f"%{tier}%")
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    leads = [dict(r) for r in cursor.fetchall()]

    for lead in leads:
        b = lead.get("max_budget_pkr")
        if b and b >= 10000000:
            lead["budget_formatted"] = f"{b / 10000000:.2f} Crore"
        elif b and b >= 100000:
            lead["budget_formatted"] = f"{b / 100000:.1f} Lakh"
        else:
            lead["budget_formatted"] = "Flexible"

    # KPI aggregate counts
    cursor.execute("SELECT COUNT(*) as cnt FROM crm_client_preferences")
    total_leads = cursor.fetchone()["cnt"]
    cursor.execute("SELECT COUNT(*) as cnt FROM crm_client_preferences WHERE priority_tier LIKE '%Hot%'")
    hot_leads = cursor.fetchone()["cnt"]
    cursor.execute("SELECT COUNT(*) as cnt FROM crm_client_preferences WHERE priority_tier LIKE '%Warm%'")
    warm_leads = cursor.fetchone()["cnt"]
    cursor.execute("SELECT COUNT(*) as cnt FROM crm_client_preferences WHERE priority_tier LIKE '%Cold%'")
    cold_leads = cursor.fetchone()["cnt"]
    conn.close()

    return {
        "count": len(leads),
        "total_leads": total_leads,
        "hot_leads": hot_leads,
        "warm_leads": warm_leads,
        "cold_leads": cold_leads,
        "leads": leads
    }


@app.get("/api/v1/ml/historical-leads")
async def get_historical_leads(
    city: Optional[str] = None,
    tier: Optional[str] = None,
    sort_by: str = "score",
    limit: int = 100
):
    """
    Returns historical leads from leads_scoring_cleaned.csv scored by champion
    pipeline, matching Streamlit Tab 2 Historical Leads sub-tab.
    """
    from crm_lead_scorer import crm_lead_scorer
    return crm_lead_scorer.get_historical_scored_leads(
        limit=limit,
        city=city,
        tier=tier,
        sort_by=sort_by
    )


@app.post("/api/v1/crm/followups/complete", dependencies=[Depends(verify_admin_token)])
async def complete_crm_followup(req: CompleteFollowupRequest):
    res = crm_store.complete_followup_reminder(reminder_id=req.reminder_id)
    return res

def format_pkr_price_label(price: float) -> str:
    if price >= 10000000:
        crore = price / 10000000
        return f"{crore:.2f}".rstrip('0').rstrip('.') + " Crore"
    elif price >= 100000:
        lakh = price / 100000
        return f"{lakh:.1f}".rstrip('0').rstrip('.') + " Lakh"
    return f"{int(price):,} PKR"

@app.get("/api/v1/properties")
async def get_properties(
    city: Optional[str] = None,
    area: Optional[str] = None,
    max_price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    purpose: Optional[str] = None,
    property_type: Optional[str] = None,
    limit: int = 20
):
    props = query_properties_sql(
        city=city,
        area=area,
        max_price_pkr=max_price,
        bedrooms=bedrooms,
        purpose=purpose,
        property_type=property_type,
        limit=limit
    )
    for p in props:
        if not p.get("price_formatted"):
            price = p.get("price_pkr", 0)
            if price >= 10000000:
                p["price_formatted"] = f"PKR {price / 10000000:.2f} Crore"
            elif price >= 100000:
                p["price_formatted"] = f"PKR {price / 100000:.1f} Lakh"
            else:
                p["price_formatted"] = f"PKR {price:,.0f}"
    return {"count": len(props), "properties": props}

@app.post("/api/v1/properties/add", dependencies=[Depends(verify_admin_token)])
async def add_property_endpoint(req: AddPropertyRequest):
    """Adds a new property record to SQLite with optional payment plan."""
    conn = get_db_connection()
    cursor = conn.cursor()
    price_fmt = format_pkr_price_label(req.price_pkr) if req.purpose == "Sale" else f"{int(req.price_pkr):,} PKR/month"
    amenities_json = json.dumps(req.amenities if isinstance(req.amenities, list) else [a.strip() for a in (req.amenities or "").split(",") if a.strip()])
    
    cursor.execute("""
        INSERT INTO properties (
            title, city, area, price_pkr, price_formatted, size_val, size_unit,
            bedrooms, bathrooms, purpose, property_type, status, developer,
            description, amenities, nearby_schools, nearby_hospitals
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Available', ?, ?, ?, ?, ?)
    """, (
        req.title, req.city, req.area, req.price_pkr, price_fmt, req.size_val, req.size_unit,
        req.bedrooms, req.bathrooms, req.purpose, req.property_type, req.developer,
        req.description or f"Luxury {req.property_type} in {req.area}, {req.city}.",
        amenities_json, req.nearby_schools or "City School, Beaconhouse", req.nearby_hospitals or "City Hospital"
    ))
    prop_id = cursor.lastrowid
    
    if req.has_payment_plan and req.down_payment_pkr:
        dp = req.down_payment_pkr
        dur = req.duration_months or 36
        mo = req.monthly_installment_pkr or round((req.price_pkr - dp) / dur, -3)
        poss = req.possession_months or 18
        cursor.execute("""
            INSERT INTO payment_plans (
                property_id, down_payment_pkr, monthly_installment_pkr, duration_months, possession_months
            ) VALUES (?, ?, ?, ?, ?)
        """, (prop_id, dp, mo, dur, poss))
        
    conn.commit()
    conn.close()
    return {"success": True, "property_id": prop_id, "message": "Property added successfully"}

@app.delete("/api/v1/properties/{property_id}", dependencies=[Depends(verify_admin_token)])
async def delete_property_endpoint(property_id: int):
    """Deletes a property record and its associated payment plan from SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM payment_plans WHERE property_id = ?", (property_id,))
    cursor.execute("DELETE FROM properties WHERE id = ?", (property_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Property {property_id} deleted successfully"}

@app.get("/api/v1/eval/hallucination", dependencies=[Depends(verify_admin_token)])
async def eval_hallucination_endpoint():
    report = run_hallucination_evaluation()
    return report

@app.get("/api/v1/eval/chunking", dependencies=[Depends(verify_admin_token)])
async def eval_chunking_endpoint():
    sample_queries = [
        "DHA transfer procedure requirements",
        "Emaar Crescent Bay NOC approval SBCA",
        "Overseas Pakistani Power of Attorney RDA account",
        "Installment discount upfront cash payment"
    ]
    res = evaluate_chunk_sizes(sample_queries)
    return res

@app.get("/api/v1/eval/voice", dependencies=[Depends(verify_admin_token)])
async def eval_voice_endpoint():
    sample_dialogue = [
        "Assalam-o-Alaikum, mujhe Lahore mein property chahiye.",
        "Budget around 3.5 Crore hai DHA Phase 6 mein.",
        "Bohot mehnga hai... koi us se sasti option hai?",
        "Acha site visit schedule kar dein."
    ]
    res = evaluate_voice_pipeline_convo("DHA Lahore Voice Demo", sample_dialogue)
    return res

@app.get("/api/v1/config/vapi")
async def get_vapi_config():
    return {
        "vapi_public_key": config.VAPI_PUBLIC_KEY,
        "vapi_assistant_id": config.VAPI_ASSISTANT_ID,
        "vapi_assistant_config": {
            "name": "RealEstate Hub UrduLish Executive (Zara)",
            "transcriber": {
                "provider": "deepgram",
                "model": "nova-2",
                "language": "ur" # Urdu/UrduLish optimized
            },
            "model": {
                "provider": "custom-llm",
                "url": "http://your-server-domain.com/v1/chat/completions"
            },
            "voice": {
                "provider": "elevenlabs",
                "voiceId": config.ELEVENLABS_VOICE_ID
            }
        },
        "keys_status": {
            "gemini_configured": bool(config.GEMINI_API_KEY and "your_" not in config.GEMINI_API_KEY),
            "groq_configured": bool(config.GROQ_API_KEY and "your_" not in config.GROQ_API_KEY),
            "vapi_configured": bool(config.VAPI_API_KEY and "your_" not in config.VAPI_API_KEY),
            "deepgram_configured": bool(config.DEEPGRAM_API_KEY and "your_" not in config.DEEPGRAM_API_KEY),
            "elevenlabs_configured": bool(config.ELEVENLABS_API_KEY and "your_" not in config.ELEVENLABS_API_KEY)
        }
    }

# ==========================================
# 3. LANGGRAPH AI AGENT ENDPOINTS
# ==========================================
from langgraph_agent.graph import run_agent_graph
from langgraph_agent.tracer import tracer

class LangGraphAgentRequest(BaseModel):
    session_id: Optional[str] = "langgraph_session_1"
    message: str

@app.post("/api/v1/agent/chat")
async def langgraph_agent_chat_endpoint(req: LangGraphAgentRequest):
    """
    Executes LangGraph Agent Orchestration.
    Includes State Tracking, Intent Routing, Tool Execution, Validation Guardrails,
    and Annotated Execution Tracing.
    """
    res = run_agent_graph(session_id=req.session_id, user_message=req.message)
    return res

@app.get("/api/v1/agent/trace")
async def langgraph_agent_trace_endpoint(session_id: Optional[str] = None):
    """
    Returns Annotated Execution Traces of node transitions (Task 5).
    """
    if session_id:
        return {"session_id": session_id, "trace": tracer.get_session_trace(session_id)}
    return tracer.get_all_traces()

# ==========================================
# 4. CLOUD & RENDER HEALTH PROBES
# ==========================================
@app.get("/healthz")
@app.get("/health")
def healthz_probe():
    """Liveness probe for Render, Kubernetes, and uptime monitoring."""
    return {
        "status": "healthy",
        "service": "real_estate_voice_agent",
        "models_loaded": True
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=config.HOST, port=config.PORT, reload=True)
