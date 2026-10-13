from .models import SandboxCapabilities
from .provider import SandboxProvider


class SandboxService:
    """Service boundary; callers must supply identities from authenticated auth."""

    def __init__(self, provider: SandboxProvider) -> None:
        self._provider = provider

    def capabilities(self) -> SandboxCapabilities:
        return self._provider.capabilities
