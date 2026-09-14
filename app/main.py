import os
import json
import uuid
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from app.database import tickets_collection, get_db
from app.agents.ticket_agents import run_full_pipeline
from app.services.rag_service import initialize_chroma_db

# Graceful Auth Import
try:
    from app.auth import get_current_user, router as auth_router
    HAS_AUTH_ROUTER = True
except Exception:
    HAS_AUTH_ROUTER = False

load_dotenv()

app = FastAPI(
    title="BrightCone Agentic AI Resolution System",
    version="1.0.0"
)

# Authentication routes if present
if HAS_AUTH_ROUTER:
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])

# Safe Production CORS
# Safe Production CORS
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://frontend-rr8w.vercel.app",
    os.getenv("FRONTEND_URL", "https://bright-cone-frontend.vercel.app"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

class ProcessTicketRequest(BaseModel):
    user_id: str
    query: str

@app.post("/api/process-ticket")
def process_ticket(payload: ProcessTicketRequest):
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

        # Generate ticket identifier
        ticket_id = f"TCK-{str(uuid.uuid4())[:8].upper()}"

        ticket_doc = {
            "ticket_id": ticket_id,
            "id": ticket_id,
            "user_id": payload.user_id,
            "query": payload.query,
            "status": parsed_data.get("escalation_status", "Requires More Information"),
            "category": parsed_data.get("issue_category", "General"),
            "priority": parsed_data.get("priority", "Medium"),
            "recommended_actions": parsed_data.get("recommended_actions", []),
            "actions_performed": parsed_data.get("actions_performed", []),
            "blocked_actions": parsed_data.get("blocked_actions", []),
            "agent_execution_history": parsed_data.get("agent_execution_history", []),
            "final_response": parsed_data.get("final_response", ""),
            "full_crewai_output": parsed_data,
            "details": parsed_data,
            "created_at": datetime.utcnow().isoformat()
        }

        # Persist document to MongoDB
        tickets_collection.insert_one(ticket_doc)

        return {
            "ticket_id": ticket_id,
            "status": ticket_doc["status"],
            "details": parsed_data
        }

    except json.JSONDecodeError:
        return {
            "status": "Escalated",
            "message": "Reviewer format validation failed. Handed over to human desk.",
            "raw_output": raw_output
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Agent workflow execution error: {str(exc)}"
        )

@app.get("/api/tickets")
def list_tickets():
    # Exclude MongoDB internal _id for JSON serialization
    tickets = list(tickets_collection.find({}, {"_id": 0}))
    return tickets

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
