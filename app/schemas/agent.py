from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AgentQueryRequest(BaseModel):
    query: str = Field(..., description="Spoken or text question from caller")
    caller_phone: Optional[str] = Field(None, description="Telephone number of incoming caller")
    call_id: Optional[str] = Field(None, description="Unique session ID of the telephone call")
    chat_history: Optional[List[Dict[str, str]]] = Field(default_factory=list)


class AgentQueryResponse(BaseModel):
    query: str
    response_text: str
    is_safe: bool
    evidence_valid: bool
    sources_used: List[Dict[str, str]] = []
    audit_trail: List[str] = []
