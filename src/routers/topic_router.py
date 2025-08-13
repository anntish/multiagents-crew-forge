from fastapi import APIRouter, Body, Request
from hivetrace import SyncHivetraceSDK

from src.config import SESSION_ID, USER_ID
from src.schemas import AgentResponse, TopicRequest
from src.services.topic_service import process_topic

router = APIRouter(prefix="/api")


@router.post("/process-topic", response_model=AgentResponse)
async def api_process_topic(request: Request, request_body: TopicRequest = Body(...)):
    hivetrace: SyncHivetraceSDK = request.app.state.hivetrace
    return process_topic(
        topic=request_body.topic,
        hivetrace=hivetrace,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
