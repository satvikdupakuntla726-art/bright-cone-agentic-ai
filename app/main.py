import os
import json
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.database import tickets_collection, get_db
from app.agents.ticket_agents import run_full_pipeline
from app.services.rag_service import initialize_chroma_db
from app.auth import get_current_user, router as auth_router
from app.models.schemas import ProcessTicketRequest

load_dotenv()

app = FastAPI(
    title="BrightCone Agentic AI Resolution System",
    version="1.1.0",
    description="Multi-agent customer support orchestration and compliance command center."
)

# Mount authentication router
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])

# Safe Production and Local CORS
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8002",
    "http://127.0.0.1:8002",
    os.getenv("FRONTEND_URL", "https://bright-cone-frontend.vercel.app")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:\d+|http://127\.0\.0\.1:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
@app.on_event("startup")
async def startup_event():
    try:
        initialize_chroma_db()
    except Exception as e:
        print(f"ChromaDB startup init notice: {e}")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "BrightCone Agentic AI Core",
        "agents": 6,
        "database": "MongoDB",
        "environment": "production-ready"
    }

@app.post("/api/process-ticket")
def process_ticket(payload: ProcessTicketRequest, current_user: str | None = Depends(get_current_user)):
    ticket_id = f"TCK-{str(uuid.uuid4())[:8].upper()}"
    raw_output = ""
    try:
        raw_output = run_full_pipeline(payload.user_id, payload.query)
        
        # Strip markdown syntax if present
        cleaned = raw_output.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        parsed_data = json.loads(cleaned)

        ticket_doc = {
            "ticket_id": ticket_id,
            "id": ticket_id,
            "user_id": payload.user_id,
            "query": payload.query,
            "status": parsed_data.get("escalation_status", "Resolved"),
            "category": parsed_data.get("issue_category", "General"),
            "priority": parsed_data.get("priority", "Medium"),
            "recommended_actions": parsed_data.get("recommended_actions", []),
            "actions_performed": parsed_data.get("actions_performed", []),
            "blocked_actions": parsed_data.get("blocked_actions", []),
            "agent_execution_history": parsed_data.get("agent_execution_history", []),
            "final_response": parsed_data.get("final_response", ""),
            "details": parsed_data,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        # Persist document to MongoDB
        tickets_collection.insert_one(ticket_doc)

        return {
            "ticket_id": ticket_id,
            "status": ticket_doc["status"],
            "details": parsed_data
        }

    except json.JSONDecodeError as decode_err:
        print(f"[Main Notice] JSON format warning: {decode_err}")
        # Always persist the escalated ticket with valid ticket_id so frontend tracking never breaks
        fallback_doc = {
            "ticket_id": ticket_id,
            "id": ticket_id,
            "user_id": payload.user_id,
            "query": payload.query,
            "status": "Escalated",
            "category": "General",
            "priority": "High",
            "recommended_actions": ["Escalated to human supervisor for manual triage."],
            "actions_performed": ["Automated reviewer format validation fallback triggered."],
            "blocked_actions": [],
            "agent_execution_history": ["Reviewer format fallback: handed over to human desk."],
            "final_response": "Your support request has been registered and escalated to our human service desk for prioritized review.",
            "details": {"raw_output": raw_output},
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        tickets_collection.insert_one(fallback_doc)
        return {
            "ticket_id": ticket_id,
            "status": "Escalated",
            "details": fallback_doc
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Agent workflow execution error: {str(exc)}"
        )

@app.get("/api/tickets")
def list_tickets():
    # Exclude MongoDB internal _id and sort by newest first
    tickets = list(tickets_collection.find({}, {"_id": 0}).sort("created_at", -1))
    return tickets

@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    ticket = tickets_collection.find_one(
        {"$or": [{"ticket_id": ticket_id}, {"id": ticket_id}]},
        {"_id": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@app.get("/api/analytics")
def get_analytics():
    total = tickets_collection.count_documents({})
    escalated = tickets_collection.count_documents({"status": "Escalated"})
    resolved = tickets_collection.count_documents({"status": "Resolved"})
    rate = round((escalated / total * 100), 1) if total > 0 else 0.0

    return {
        "total_tickets": total,
        "escalated_count": escalated,
        "resolved_count": resolved,
        "escalation_rate": rate
    }
