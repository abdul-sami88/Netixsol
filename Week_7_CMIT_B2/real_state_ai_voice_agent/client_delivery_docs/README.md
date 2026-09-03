# RealEstate Hub Pakistan — AI Voice Agent Enterprise Handover Index

Welcome to the official Enterprise Handover Documentation for the **UrduLish Real Estate AI Voice Agent System** ('Zara').

This product delivers an end-to-end autonomous Pakistani real estate sales executive capable of natural UrduLish speech, property recommendations, Google Calendar scheduling, automated dual HTML email notifications via SMTP, CRM lead tracking, and LangGraph AI Agent orchestration with 100% security guardrails.

---

## Complete Executive Documentation Suite

The complete product documentation package is organized as follows:

1. [**System Architecture (`SYSTEM_ARCHITECTURE.md`)**](file:///c:/Users/MEE/Anti-Gravity_projects/Real_estate_voice_agent/client_delivery_docs/SYSTEM_ARCHITECTURE.md)
   - High-level architecture, LangGraph state machine flow, Vapi / Deepgram / ElevenLabs integration, hybrid SQL+RAG retrieval pipeline, and security model.

2. [**API Documentation (`API_DOCUMENTATION.md`)**](file:///c:/Users/MEE/Anti-Gravity_projects/Real_estate_voice_agent/client_delivery_docs/API_DOCUMENTATION.md)
   - Comprehensive OpenAPI / REST and Webhook API specifications for Vapi `/v1/chat/completions`, REST chat, LangGraph agent, CRM logs, and Kubernetes health probes.

3. [**User Guide (`USER_GUIDE.md`)**](file:///c:/Users/MEE/Anti-Gravity_projects/Real_estate_voice_agent/client_delivery_docs/USER_GUIDE.md)
   - End-user and agent operator guide on UrduLish conversation etiquette, property search, site visit booking, rescheduling, and cancellation.

4. [**Admin Guide (`ADMIN_GUIDE.md`)**](file:///c:/Users/MEE/Anti-Gravity_projects/Real_estate_voice_agent/client_delivery_docs/ADMIN_GUIDE.md)
   - Administrator guide for environment configuration (`.env`), Vapi Portal setup, Google Service Account calendar integration, Gmail SMTP setup, and Docker deployment.

5. [**Monitoring & Maintenance Plan (`MAINTENANCE_GUIDE.md`)**](file:///c:/Users/MEE/Anti-Gravity_projects/Real_estate_voice_agent/client_delivery_docs/MAINTENANCE_GUIDE.md)
   - Operational SLAs, latency targets, 99.9% uptime targets, weekly STT retraining, vector DB refresh schedule, prompt updates, backup strategy, and monthly security review cadence.

6. [**Troubleshooting Guide (`TROUBLESHOOTING_GUIDE.md`)**](file:///c:/Users/MEE/Anti-Gravity_projects/Real_estate_voice_agent/client_delivery_docs/TROUBLESHOOTING_GUIDE.md)
   - Diagnostic matrix for SMTP authentication drops, DMARC/SPF deliverability, Vapi webhook timeouts, Deepgram STT normalization, and Google Calendar API error resolution.

7. [**Future Enhancements Roadmap (`FUTURE_ENHANCEMENTS.md`)**](file:///c:/Users/MEE/Anti-Gravity_projects/Real_estate_voice_agent/client_delivery_docs/FUTURE_ENHANCEMENTS.md)
   - Strategic roadmap detailing WhatsApp Business integration, SMS confirmations, Salesforce/HubSpot CRM integration, Multilingual support (Urdu, English, Punjabi), and Voice Cloning for brand representatives.

---

## Quick System Status

- **Core Engine**: FastAPI Custom LLM Server with Primary Gemini & Groq Backup
- **Agent Orchestration**: LangGraph StateGraph (`langgraph_agent/`) + **n8n Workflow** ([`n8n_langgraph_workflow.json`](file:///c:/Users/MEE/Anti-Gravity_projects/Real_estate_voice_agent/n8n_langgraph_workflow.json))
- **Speech Stack**: Deepgram `nova-2` STT + ElevenLabs TTS (`21m00Tcm4TlvDq8ikWAM`)
- **Database & Storage**: SQLite (`real_estate.db`) + TF-IDF Vector Index
- **Email Dispatch**: Dual HTML Email Notifications via Live SMTP (`samiworkspace11@gmail.com`)
- **Production Package**: Dockerized with non-root security user, telemetry logging, and `/readyz` probes

