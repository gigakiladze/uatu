from fastapi import APIRouter, Depends

from uatu.models.credential import CreateCredentialRequest
from uatu.services.project import resolve_project
from uatu.services.credential import get_credentials, create_credential


router = APIRouter(
    prefix="/projects/{project_id}/credentials",
    tags=["credentials"],
    dependencies=[Depends(resolve_project)],
)


@router.get("")
def get_credential(project_id: str) -> dict:
    """Get the credentials for a project."""
    credential = get_credentials(project_id)
    if credential:
        return {"project_id": project_id, "credentials": credential}
    else:
        return {"project_id": project_id, "credentials": None}



@router.post("")
def set_credentials(project_id: str, credentials: CreateCredentialRequest) -> dict:
    """Set the credentials for a project."""
    created_credential = create_credential(
        project_id, credentials.provider, credentials.token
    )
    return {"project_id": project_id, "credentials": created_credential}