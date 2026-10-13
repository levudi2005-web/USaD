from fastapi import APIRouter
from pydantic import BaseModel

from local_agent.usad_agent.sandbox.provider import UnsupportedSandboxProvider
from local_agent.usad_agent.sandbox.service import SandboxService

router = APIRouter(prefix="/sandboxes", tags=["sandboxes"])
sandbox_service = SandboxService(UnsupportedSandboxProvider())


class SandboxCapabilitiesResponse(BaseModel):
    provider: str
    state: str
    execution_enabled: bool
    network_default: str
    reason: str


@router.get("/capabilities", response_model=SandboxCapabilitiesResponse)
def get_sandbox_capabilities() -> SandboxCapabilitiesResponse:
    """Read-only endpoint; it never starts a process or creates a sandbox."""
    capabilities = sandbox_service.capabilities()
    return SandboxCapabilitiesResponse(
        provider=capabilities.provider,
        state=capabilities.state.value,
        execution_enabled=capabilities.execution_enabled,
        network_default=capabilities.network_default,
        reason=capabilities.reason,
    )
