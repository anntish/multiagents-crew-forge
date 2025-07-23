import uuid
from contextlib import asynccontextmanager
from typing import Optional

from crewai import Crew
from fastapi import APIRouter, Body, FastAPI, Request

from hivetrace import SyncHivetraceSDK
from hivetrace import crewai_trace as trace
from src.agents import agent_id_mapping, editor, planner, writer
from src.config import (
    EDITOR_ID,
    HIVETRACE_ACCESS_TOKEN,
    HIVETRACE_APP_ID,
    HIVETRACE_URL,
    PLANNER_ID,
    SESSION_ID,
    USER_ID,
    WRITER_ID,
)
from src.schemas import AgentResponse, TopicRequest
from src.tasks import edit, plan, write


@asynccontextmanager
async def lifespan(app: FastAPI):
    hivetrace = SyncHivetraceSDK(
        config={
            "HIVETRACE_URL": HIVETRACE_URL,
            "HIVETRACE_ACCESS_TOKEN": HIVETRACE_ACCESS_TOKEN,
        }
    )
    app.state.hivetrace = hivetrace
    try:
        yield
    finally:
        hivetrace.close()


app = FastAPI(lifespan=lifespan)
router = APIRouter(prefix="/api")


def _build_log_params(
    agent_conversation_id: str, user_id: Optional[str], session_id: Optional[str]
) -> dict:
    """Создает параметры для логирования с агентами"""
    params = {
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
        params["user_id"] = user_id
    if session_id:
        params["session_id"] = session_id

    return params


def _build_execution_details(
    agent_conversation_id: str, user_id: Optional[str], session_id: Optional[str]
) -> dict:
    """Создает детали выполнения для ответа"""
    details = {
        "status": "completed",
        "agent_conversation_id": agent_conversation_id,
    }

    if user_id:
        details["user_id"] = user_id
    if session_id:
        details["session_id"] = session_id

    return details


def process_topic(
    topic: str,
    hivetrace: SyncHivetraceSDK,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
):
    agent_conversation_id = str(uuid.uuid4())

    log_params = _build_log_params(agent_conversation_id, user_id, session_id)

    hivetrace.input(
        application_id=HIVETRACE_APP_ID,
        message=f"Requesting information from agents on the topic: {topic}",
        additional_parameters=log_params,
    )

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

    crew = create_crew()

    kickoff_kwargs = {"inputs": {"topic": topic}}
    if user_id:
        kickoff_kwargs["user_id"] = user_id
    if session_id:
        kickoff_kwargs["session_id"] = session_id
    if agent_conversation_id:
        kickoff_kwargs["agent_conversation_id"] = agent_conversation_id

    result = crew.kickoff(**kickoff_kwargs)
    execution_details = _build_execution_details(
        agent_conversation_id, user_id, session_id
    )

    return {"result": result.raw, "execution_details": execution_details}


@router.post("/process-topic", response_model=AgentResponse)
async def api_process_topic(request: Request, request_body: TopicRequest = Body(...)):
    hivetrace: SyncHivetraceSDK = request.app.state.hivetrace
    return process_topic(
        topic=request_body.topic,
        hivetrace=hivetrace,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )


app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True)
