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
    user_id=USER_ID,
    session_id=SESSION_ID,
    agent_id_mapping=agent_id_mapping,
)
def create_crew():
    return Crew(
        agents=[planner, writer, editor],
        tasks=[plan, write, edit],
        verbose=True,
    )


def process_topic(topic: str, user_id: str = USER_ID, session_id: str = SESSION_ID):
    hivetrace.input(
        application_id=HIVETRACE_APP_ID,
        message=f"Requesting information from agents on the topic: {topic}",
        additional_parameters={
            "session_id": session_id,
            "user_id": user_id,
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
        },
    )
    crew = create_crew()
    result = crew.kickoff(inputs={"topic": topic})

    return {"result": result.raw, "execution_details": {"status": "completed"}}


@router.post("/process-topic", response_model=AgentResponse)
async def api_process_topic(request: TopicRequest = Body(...)):
    user_id = request.user_id or USER_ID
    session_id = request.session_id or SESSION_ID
    return process_topic(topic=request.topic, user_id=user_id, session_id=session_id)


app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
