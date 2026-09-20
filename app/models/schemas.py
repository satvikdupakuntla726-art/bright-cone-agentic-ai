from pydantic import BaseModel, Field
from typing import List, Optional, Any

class LoginRequest(BaseModel):
    email: str = Field(..., description="Enterprise operator email")
    password: str = Field(..., description="Operator password")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str = "Enterprise Operator"
    email: Optional[str] = None

class ProcessTicketRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    query: str = Field(..., min_length=1, max_length=5000)

class TicketState(BaseModel):
    ticket_id: str
    user_id: str
    query: str
    status: str = "Open"
    issue_category: Optional[str] = None
    priority: Optional[str] = "Medium"
    retrieved_knowledge: Optional[str] = None
    recommended_actions: List[str] = []
    actions_performed: List[str] = []
    blocked_actions: List[str] = []
    agent_execution_history: List[str] = []
    final_response: str = ""
    created_at: Optional[str] = None
    details: Optional[Any] = None

class AgentResponse(BaseModel):
    final_response: str
    suggested_resolution: str
    execution_history: List[str]