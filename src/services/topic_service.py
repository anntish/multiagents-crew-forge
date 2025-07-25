import uuid
from typing import Optional

from crewai import Crew
from hivetrace import SyncHivetraceSDK
from hivetrace import crewai_trace as trace

from src.agents import agent_id_mapping, editor, planner, writer
from src.config import HIVETRACE_APP_ID
from src.tasks import edit, plan, write
from src.utils.params import _build_agent_metadata, _build_common_params


def process_topic(
    topic: str,
    hivetrace: SyncHivetraceSDK,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
):
    agent_conversation_id = str(uuid.uuid4())
    common_params = _build_common_params(agent_conversation_id, user_id, session_id)

    hivetrace.input(
        application_id=HIVETRACE_APP_ID,
        message=f"Requesting information from agents on the topic: {topic}",
        additional_parameters={
            **common_params,
            "agents": _build_agent_metadata(),
        },
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
    result = crew.kickoff(inputs={"topic": topic}, **common_params)

    return {
        "result": result.raw,
        "execution_details": {**common_params, "status": "completed"},
    }
