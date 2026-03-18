"""
Chat router.
Exposes POST /chat endpoint for authenticated RAG conversations.
"""

import logging

import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database.postgres import get_db
from app.schemas.chat_schema import ChatRequest
from app.services.chat_service import ChatService
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("")
async def chat(
    data: ChatRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Process a user question through the RAG pipeline.
    Creates a new session if not provided, saves the conversation,
    and returns an AI-generated StreamingResponse.
    """
    try:
        chat_service = ChatService(db=db)

        # Create or use existing session
        if data.session_id:
            session_id = data.session_id
        else:
            # Create a new session with the question as title
            title = data.question[:100] if len(data.question) > 100 else data.question
            session = await chat_service.create_session(
                user_id=user_id,
                title=title,
            )
            session_id = str(session.id)

        rag_service = RAGService()
        
        # Determine sources ahead of creating the generator
        generator = rag_service.answer_question_stream(
            question=data.question,
            user_id=user_id,
        )
        
        sources_list = []
        
        async def response_generator():
            full_response = ""
            # Because the underlying LLM stream is sync, we iterate over it synchronously
            # but inside an async generator for FastAPI compatibility.
            for chunk_type, chunk_data in generator:
                if chunk_type == 'token':
                    yield chunk_data
                elif chunk_type == 'sources':
                    sources_list.extend(chunk_data)
                elif chunk_type == 'full_response':
                    full_response = chunk_data
                    
            # After streaming is complete, save to database
            try:
                await chat_service.save_message(
                    session_id=session_id,
                    user_message=data.question,
                    assistant_response=full_response,
                )
                logger.info("Chat response saved for user: %s, session: %s", user_id, session_id)
            except Exception as e:
                logger.error("Failed to save message to database: %s", str(e))

        # We need headers for Streamlit to know session id and sources immediately
        headers = {
            "X-Session-ID": session_id,
            "X-Sources": json.dumps([]), # Initially empty, updated client-side or we stream sources at end
        }
        
        return StreamingResponse(
            response_generator(), 
            media_type="text/event-stream",
            headers=headers
        )

    except Exception as e:
        logger.error("Chat failed for user %s: %s", user_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}",
        ) from e
