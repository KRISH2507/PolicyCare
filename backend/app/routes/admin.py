import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, Form, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.policy import Policy
from app.schemas.policy import PolicyUpdate, PolicyResponse
from app.services.file_service import save_upload, delete_file
from app.routes.auth import require_admin
from app.services.parser_service import extract_document_text
from app.services.chunk_service import chunk_document
from app.services.vector_service import store_policy_chunks, delete_policy_vectors

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_policy(
    name: str = Form(...),
    insurer: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
):
    file_path, file_ext = save_upload(file)

    policy = Policy(
        name=name,
        insurer=insurer,
        file_type=file_ext,
        file_path=file_path,
        uploaded_by=admin_user["email"],
        is_active=True,
        uploaded_at=datetime.now(timezone.utc),
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)

    try:
        pages = extract_document_text(file_path, file_ext)
        chunks = chunk_document(pages)
        store_policy_chunks(
            policy_id=policy.id,
            policy_name=policy.name,
            insurer=policy.insurer,
            chunks=chunks,
        )
    except Exception as e:
        logger.error("RAG pipeline failed for policy %s: %s", policy.id, e)
        db.delete(policy)
        db.commit()
        delete_file(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}",
        )

    return {"message": "Policy uploaded successfully",
            "policy_id": policy.id, "name": policy.name, "insurer": policy.insurer}


@router.get("/policies", response_model=List[PolicyResponse])
def list_policies(db: Session = Depends(get_db), admin_user: dict = Depends(require_admin)):
    return db.query(Policy).order_by(Policy.uploaded_at.desc()).all()


@router.patch("/policies/{policy_id}", response_model=PolicyResponse)
def update_policy(
    policy_id: int,
    policy_update: PolicyUpdate,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Policy not found")

    if policy_update.name is not None:
        policy.name = policy_update.name
    if policy_update.insurer is not None:
        policy.insurer = policy_update.insurer

    db.commit()
    db.refresh(policy)
    return policy


@router.delete("/policies/{policy_id}")
def delete_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Policy not found")

    file_deleted = delete_file(policy.file_path)
    delete_policy_vectors(policy.id)
    db.delete(policy)
    db.commit()

    return {"message": "Policy deleted", "file_deleted": file_deleted}
