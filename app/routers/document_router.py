"""
Document upload router.
Exposes POST /upload_pdf endpoint for authenticated users.
"""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.security import get_current_user
from app.schemas.document_schema import DocumentListResponse, DocumentUploadResponse
from app.services.pdf_service import PDFService
from app.services.vector_service import VectorStoreService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload_pdf", response_model=DocumentUploadResponse, status_code=201)
async def upload_pdf(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
) -> DocumentUploadResponse:
    """
    Upload a PDF document for processing.
    Extracts text, chunks, embeds, and stores in vector database.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted",
        )

    try:
        logger.info("User %s uploading PDF: %s", user_id, file.filename)

        # Read file content
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty",
            )

        # Process the PDF
        pdf_service = PDFService()
        chunks_created = pdf_service.process_pdf(
            file_content=content,
            filename=file.filename,
            user_id=user_id,
        )

        if chunks_created == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract any text from the PDF",
            )

        return DocumentUploadResponse(
            filename=file.filename,
            message=f"Successfully processed '{file.filename}'",
            chunks_created=chunks_created,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("PDF upload failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process PDF: {str(e)}",
        ) from e


@router.get("/", response_model=DocumentListResponse)
async def get_user_documents(
    user_id: str = Depends(get_current_user),
) -> DocumentListResponse:
    """
    Get a list of all unique documents uploaded by the current user.
    """
    try:
        vector_store = VectorStoreService()
        documents = vector_store.get_user_documents(user_id=user_id)
        return DocumentListResponse(documents=documents)
    except Exception as e:
        logger.error("Failed to fetch documents: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch documents",
        ) from e
