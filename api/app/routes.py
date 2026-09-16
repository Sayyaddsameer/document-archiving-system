import io
import socket
import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, File, UploadFile, HTTPException, Response

from app.database import Database
from app.storage import ObjectStorage

logger = logging.getLogger(__name__)

router = APIRouter()

# These will be set during application startup
db: Database = None
storage: ObjectStorage = None


def _format_document(doc: dict) -> dict:
    """Format a document record for the API response."""
    result = {
        "id": doc["id"],
        "filename": doc["filename"],
        "s3_key": doc["s3_key"],
        "content_type": doc["content_type"],
    }
    created_at = doc["created_at"]
    if isinstance(created_at, datetime):
        result["created_at"] = created_at.strftime("%Y-%m-%dT%H:%M:%S.") + f"{created_at.microsecond // 1000:03d}Z"
    else:
        result["created_at"] = str(created_at)
    return result


@router.post("/documents", status_code=201)
async def upload_document(file: UploadFile = File(...)):
    """Upload a document. Stores the file in MinIO and metadata in PostgreSQL."""
    contents = await file.read()
    file_size = len(contents)
    
    content_type = file.content_type or "application/octet-stream"
    s3_key = f"{uuid.uuid4().hex}_{file.filename}"
    
    storage.upload_file(
        key=s3_key,
        data=io.BytesIO(contents),
        length=file_size,
        content_type=content_type,
    )
    
    doc = db.insert_document(
        filename=file.filename,
        s3_key=s3_key,
        content_type=content_type,
    )
    
    logger.info("Document uploaded: %s (id=%d)", file.filename, doc["id"])
    return _format_document(doc)


@router.get("/documents")
async def list_documents():
    """List metadata for all archived documents."""
    docs = db.get_all_documents()
    return [_format_document(doc) for doc in docs]


@router.get("/documents/{doc_id}")
async def get_document(doc_id: int):
    """Retrieve a specific document by its ID. Returns the raw file content."""
    doc = db.get_document_by_id(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_data = storage.get_file(doc["s3_key"])
    
    return Response(
        content=file_data,
        media_type=doc["content_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{doc["filename"]}"',
        },
    )
