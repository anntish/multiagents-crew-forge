import uuid
from typing import Optional

from crewai import Crew
from fastapi import APIRouter, Body, FastAPI

from hivetrace.crewai_adapter import trace
from src.agents import agent_id_mapping, editor, planner, writer
from src.config import (
    EDITOR_ID,
    HIVETRACE_APP_ID,
    PLANNER_ID,
    SESSION_ID,
    USER_ID,
    WRITER_ID,
)
from src.init_hivetrace import hivetrace
from src.schemas import AgentResponse, TopicRequest
from src.tasks import edit, plan, write

app = FastAPI()
router = APIRouter(prefix="/api")


@trace(
    hivetrace=hivetrace,
    application_id=HIVETRACE_APP_ID,
    agent_id_mapping=agent_id_mapping,
)
def create_crew():
    return Crew(
        agents=[planner, writer, editor],
        tasks=[plan, write, edit],
        verbose=True,
    )


def process_topic(
    topic: str, user_id: Optional[str] = None, session_id: Optional[str] = None
):
    # Генерируем уникальный ID для этого разговора с агентами
    agent_conversation_id = str(uuid.uuid4())

    log_additional_params = {
        "agent_conversation_id": agent_conversation_id,
        "agents": {
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
        },
    }

    if user_id:
        log_additional_params["user_id"] = user_id
    if session_id:
        log_additional_params["session_id"] = session_id

    hivetrace.input(
        application_id=HIVETRACE_APP_ID,
        message=f"Requesting information from agents on the topic: {topic}",
        additional_parameters=log_additional_params,
    )

    # Создаем crew (без статических параметров)
    crew = create_crew()

    # Передаем user_id, session_id и agent_conversation_id в runtime только если они есть
    kickoff_kwargs = {"inputs": {"topic": topic}}
    if user_id:
        kickoff_kwargs["user_id"] = user_id
    if session_id:
        kickoff_kwargs["session_id"] = session_id
    if agent_conversation_id:
        kickoff_kwargs["agent_conversation_id"] = agent_conversation_id

    result = crew.kickoff(**kickoff_kwargs)

    execution_details = {
        "status": "completed",
        "agent_conversation_id": agent_conversation_id,
    }
    if user_id:
        execution_details["user_id"] = user_id
    if session_id:
        execution_details["session_id"] = session_id

    return {"result": result.raw, "execution_details": execution_details}


@router.post("/process-topic", response_model=AgentResponse)
async def api_process_topic(request: TopicRequest = Body(...)):
    return process_topic(
        topic=request.topic,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )


app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
