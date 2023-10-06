from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from danswer.auth.users import current_admin_user
from danswer.auth.users import current_user
from danswer.db.document_set import fetch_document_sets
from danswer.db.document_set import insert_document_set
from danswer.db.document_set import mark_document_set_as_to_be_deleted
from danswer.db.document_set import update_document_set
from danswer.db.engine import get_session
from danswer.db.models import User
from danswer.server.models import ConnectorCredentialPairDescriptor
from danswer.server.models import ConnectorSnapshot
from danswer.server.models import CredentialSnapshot
from danswer.server.models import DocumentSet
from danswer.server.models import DocumentSetCreationRequest
from danswer.server.models import DocumentSetUpdateRequest


router = APIRouter(prefix="/manage")


@router.post("/admin/document-set")
def create_document_set(
    document_set_creation_request: DocumentSetCreationRequest,
    user: User = Depends(current_admin_user),
    db_session: Session = Depends(get_session),
) -> int:
    try:
        document_set_db_model, _ = insert_document_set(
            document_set_creation_request=document_set_creation_request,
            user_id=user.id if user else None,
            db_session=db_session,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return document_set_db_model.id


@router.patch("/admin/document-set")
def patch_document_set(
    document_set_update_request: DocumentSetUpdateRequest,
    _: User = Depends(current_admin_user),
    db_session: Session = Depends(get_session),
) -> None:
    try:
        update_document_set(
            document_set_update_request=document_set_update_request,
            db_session=db_session,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/admin/document-set/{document_set_id}")
def delete_document_set(
    document_set_id: int,
    _: User = Depends(current_admin_user),
    db_session: Session = Depends(get_session),
) -> None:
    try:
        mark_document_set_as_to_be_deleted(
            document_set_id=document_set_id, db_session=db_session
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


"""Endpoints for non-admins"""


@router.get("/document-set")
def list_document_sets(
    _: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> list[DocumentSet]:
    document_set_info = fetch_document_sets(db_session=db_session)
    return [
        DocumentSet(
            id=document_set_db_model.id,
            name=document_set_db_model.name,
            description=document_set_db_model.description,
            cc_pair_descriptors=[
                ConnectorCredentialPairDescriptor(
                    id=cc_pair.id,
                    name=cc_pair.name,
                    connector=ConnectorSnapshot.from_connector_db_model(
                        cc_pair.connector
                    ),
                    credential=CredentialSnapshot.from_credential_db_model(
                        cc_pair.credential
                    ),
                )
                for cc_pair in cc_pairs
            ],
            is_up_to_date=document_set_db_model.is_up_to_date,
        )
        for document_set_db_model, cc_pairs in document_set_info
    ]
