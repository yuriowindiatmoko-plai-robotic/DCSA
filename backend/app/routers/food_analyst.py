# app/routers/food_analyst.py

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
import httpx
import json
import os
import logging
from pydantic import BaseModel
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/food-analyst", tags=["food-analyst"])
logger = logging.getLogger(__name__)

# ADK Agent Backend Configuration
ADK_AGENT_URL = os.getenv("ADK_AGENT_URL", "http://localhost:8000")
ADK_APP_NAME = os.getenv("ADK_APP_NAME", "food_analyst_agent_adk")

# Pydantic Models
class SessionCreateRequest(BaseModel):
    userId: str
    systemInstruction: Optional[dict] = None


class SessionCreateResponse(BaseModel):
    sessionId: str
    appName: str


class ChatMessage(BaseModel):
    role: str
    parts: list[dict]


class ChatRequest(BaseModel):
    appName: str
    userId: str
    sessionId: str
    newMessage: ChatMessage


@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session(
    request: SessionCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new Food Analyst Agent session.

    Proxies the request to the ADK Agent backend.
    """
    try:
        logger.info(f"User {current_user.id} creating new Food Analyst session")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ADK_AGENT_URL}/apps/{ADK_APP_NAME}/users/{request.userId}/sessions",
                json={
                    "systemInstruction": request.systemInstruction or {
                        "parts": [{"text": "You are a helpful Indonesian food analyst assistant."}]
                    }
                },
                headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                logger.error(f"Failed to create session: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to create session: {response.text}"
                )

            data = response.json()
            logger.info(f"Session created successfully for user {current_user.id}: {data.get('id')}")

            return SessionCreateResponse(
                sessionId=data.get("id", ""),
                appName=ADK_APP_NAME
            )

    except httpx.RequestError as e:
        logger.error(f"Failed to connect to ADK Agent backend: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to ADK Agent backend: {str(e)}"
        )


@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Send a message to the Food Analyst Agent with SSE streaming.

    Proxies the request to the ADK Agent backend and streams the response.
    """

    async def stream_agent_response():
        """Generator function to stream SSE events from ADK agent."""
        try:
            logger.info(f"User {current_user.id} sending message to session {request.sessionId}")

            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{ADK_AGENT_URL}/run",
                    json={
                        "appName": request.appName,
                        "userId": request.userId,
                        "sessionId": request.sessionId,
                        "newMessage": {
                            "role": request.newMessage.role,
                            "parts": request.newMessage.parts
                        }
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream"
                    }
                ) as response:

                    if response.status_code != 200:
                        error_data = await response.aread()
                        logger.error(f"ADK Agent error: {response.status_code} - {error_data.decode()}")
                        yield f"data: {json.dumps({'error': error_data.decode()})}\n\n"
                        return

                    # Stream the SSE events and format properly
                    buffer = b""
                    async for chunk in response.aiter_bytes():
                        buffer += chunk

                        # Try to parse complete JSON objects from buffer
                        # The ADK Agent returns a JSON array, so we need to extract and yield each item
                        try:
                            # Try to parse as JSON array
                            data = json.loads(buffer.decode('utf-8'))

                            if isinstance(data, list):
                                # Yield each array item as a separate SSE event
                                for item in data:
                                    yield f"data: {json.dumps(item)}\n\n"
                            else:
                                # Single object, yield as-is
                                yield f"data: {json.dumps(data)}\n\n"

                            buffer = b""  # Clear buffer after processing
                        except json.JSONDecodeError:
                            # Incomplete JSON, wait for more chunks
                            continue

            logger.info(f"Successfully processed message for user {current_user.id}")

        except httpx.RequestError as e:
            logger.error(f"Connection error for user {current_user.id}: {str(e)}")
            error_msg = json.dumps({"error": f"Connection error: {str(e)}"})
            yield f"data: {error_msg}\n\n"
        except Exception as e:
            logger.error(f"Unexpected error for user {current_user.id}: {str(e)}")
            error_msg = json.dumps({"error": f"Unexpected error: {str(e)}"})
            yield f"data: {error_msg}\n\n"

    return StreamingResponse(
        stream_agent_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get session details and conversation history.

    Proxies the request to the ADK Agent backend.
    """
    try:
        logger.info(f"User {current_user.id} fetching session {session_id}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{ADK_AGENT_URL}/apps/{ADK_APP_NAME}/users/{current_user.id}/sessions/{session_id}",
                headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                logger.error(f"Failed to get session: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get session: {response.text}"
                )

            return response.json()

    except httpx.RequestError as e:
        logger.error(f"Failed to connect to ADK Agent backend: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to ADK Agent backend: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for Food Analyst Agent service.
    Verifies ADK Agent is running and the app is registered.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check if ADK Agent is running and app is registered
            response = await client.get(f"{ADK_AGENT_URL}/list-apps?detailed=false")

            if response.status_code == 200:
                apps = response.json()
                if ADK_APP_NAME in apps:
                    return {
                        "status": "healthy",
                        "adk_agent_connected": True,
                        "app_registered": True
                    }
                else:
                    return {
                        "status": "degraded",
                        "adk_agent_connected": True,
                        "app_registered": False,
                        "error": f"App '{ADK_APP_NAME}' not found in registered apps"
                    }
            else:
                return {
                    "status": "degraded",
                    "adk_agent_connected": False,
                    "adk_agent_status": response.status_code
                }

    except httpx.RequestError as e:
        return {
            "status": "unhealthy",
            "adk_agent_connected": False,
            "error": f"Failed to connect to ADK Agent backend: {str(e)}"
        }
