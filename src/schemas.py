from typing import Any, Dict, Optional

from pydantic import BaseModel


class TopicRequest(BaseModel):
    topic: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    result: str
    execution_details: Dict[str, Any]
