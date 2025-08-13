from typing import Optional

from src.config import EDITOR_ID, PLANNER_ID, WRITER_ID


def build_agent_metadata() -> dict:
    return {
        PLANNER_ID: {
            "name": "Content Planner",
            "description": "Create a structured content plan",
        },
        WRITER_ID: {
            "name": "Content Writer",
            "description": "Write an article",
        },
        EDITOR_ID: {
            "name": "Editor",
            "description": "Edit the article",
        },
    }


def build_common_params(
    agent_conversation_id: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> dict:
    params = {"agent_conversation_id": agent_conversation_id}

    if user_id:
        params["user_id"] = user_id
    if session_id:
        params["session_id"] = session_id

    return params
