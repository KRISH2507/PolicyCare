import os
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

router = APIRouter()

@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_policy(
    name: str = Form(...),
    insurer: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """
    Secure endpoint for admins only. Uploads a policy file (pdf/txt/json).
    Saves file to uuid path, details natively to SQL table, and vectors to Chroma.
    """
    # 1. Save physical file
    file_path, file_ext = save_upload(file)
    
    # 2. Store metadata in SQL
    new_policy = Policy(
        name=name,
        insurer=insurer,
        file_type=file_ext,
        file_path=file_path,
        uploaded_by=admin_user["username"],
        is_active=True,
        uploaded_at=datetime.now(timezone.utc)
    )
    
    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)
    
    # 3. Document Intelligence Layer (RAG Pipeline)
    try:
        pages = extract_document_text(file_path, file_ext)
        chunks = chunk_document(pages)
        store_policy_chunks(
            policy_id=new_policy.id,
            policy_name=new_policy.name,
            insurer=new_policy.insurer,
            chunks=chunks
        )
    except Exception as e:
        # If parsing or embeddings fail gracefully rollback DB and File!
        db.delete(new_policy)
        db.commit()
        delete_file(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document vectors. Setup rolled back entirely: {str(e)}"
        )
    
    return {
        "message": "Policy uploaded and vectorized successfully",
        "policy_id": new_policy.id,
        "name": new_policy.name,
        "insurer": new_policy.insurer
    }


@router.get("/policies", response_model=List[PolicyResponse])
def list_policies(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """
    Returns all policies registered in the system ordered from newest to oldest. 
    """
    policies = db.query(Policy).order_by(Policy.uploaded_at.desc()).all()
    return policies


@router.patch("/policies/{policy_id}", response_model=PolicyResponse)
def update_policy(
    policy_id: int,
    policy_update: PolicyUpdate,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """
    Admin edit method. Patches only the name and insurer metadata dynamically.
    """
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
        
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
    admin_user: dict = Depends(require_admin)
):
    """
    Completely scrubs a policy out of the system physically and relationally.
    """
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
        
    # 1. Delete the physical local file from uploads
    success = delete_file(policy.file_path)
    
    # 2. RAG Intelligence vector deletion explicitly matching relation logic
    delete_policy_vectors(policy.id)
    
    # 3. Drop metadata dynamically mapped table record
    db.delete(policy)
    db.commit()
    
    return {
        "message": "Policy deleted completely from SQL + Vector DB", 
        "physical_file_deleted": success
    }
