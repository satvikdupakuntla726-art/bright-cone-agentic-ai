from pydantic import BaseModel
from typing import List, Optional

class CustomerQuery(BaseModel):
    user_id: str
    query: str

class TicketState(BaseModel):
    ticket_id: str
    status: str = "Open"
    issue_category: Optional[str] = None
    priority: Optional[str] = None
    retrieved_knowledge: List[str] = []
    actions_performed: List[str] = []
    escalation_status: bool = False

class AgentResponse(BaseModel):
    final_response: str
    suggested_resolution: str
    execution_history: List[str]