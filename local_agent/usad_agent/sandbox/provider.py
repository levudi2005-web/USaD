from abc import ABC, abstractmethod
from collections.abc import Sequence

from .models import ResourceLimits, SandboxCapabilities, SandboxRecord, SandboxState


class SandboxUnavailable(RuntimeError):
    def __init__(self, state: SandboxState, message: str) -> None:
        super().__init__(message)
        self.state = state


class SandboxProvider(ABC):
    """Execution boundary. Implementations must enforce OS-level isolation."""

    @property
    @abstractmethod
    def capabilities(self) -> SandboxCapabilities:
        raise NotImplementedError

    @abstractmethod
    def create(
        self,
        *,
        project_id: str,
        owner_id: str,
        runtime: str,
        limits: ResourceLimits,
    ) -> SandboxRecord:
        raise NotImplementedError

    @abstractmethod
    def run_approved(
        self,
        sandbox: SandboxRecord,
        argv: Sequence[str],
        *,
        timeout_seconds: int,
        output_limit_bytes: int,
    ) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def stop(self, sandbox: SandboxRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def hibernate(self, sandbox: SandboxRecord) -> None:
        """Persist files/metadata only; this contract does not imply RAM snapshots."""
        raise NotImplementedError

    @abstractmethod
    def wake(self, sandbox: SandboxRecord) -> None:
        raise NotImplementedError


class UnsupportedSandboxProvider(SandboxProvider):
    """Fail-closed provider used until an isolated runtime is configured."""

    @property
    def capabilities(self) -> SandboxCapabilities:
        return SandboxCapabilities(
            provider="unconfigured",
            state=SandboxState.NEEDS_SETUP,
            execution_enabled=False,
            network_default="deny",
            reason=(
                "No security-tested isolated runtime is configured. "
                "Commands will not run on the host."
            ),
        )

    def create(
        self,
        *,
        project_id: str,
        owner_id: str,
        runtime: str,
        limits: ResourceLimits,
    ) -> SandboxRecord:
        raise SandboxUnavailable(
            SandboxState.NEEDS_SETUP,
            "Sandbox creation is disabled until an isolated provider is configured.",
        )

    def run_approved(
        self,
        sandbox: SandboxRecord,
        argv: Sequence[str],
        *,
        timeout_seconds: int,
        output_limit_bytes: int,
    ) -> bytes:
        raise SandboxUnavailable(
            SandboxState.NEEDS_SETUP,
            "Command execution is disabled; no command was started.",
        )

    def stop(self, sandbox: SandboxRecord) -> None:
        raise SandboxUnavailable(SandboxState.NEEDS_SETUP, "No sandbox runtime is active.")

    def hibernate(self, sandbox: SandboxRecord) -> None:
        raise SandboxUnavailable(SandboxState.NEEDS_SETUP, "Hibernate is not configured.")

    def wake(self, sandbox: SandboxRecord) -> None:
        raise SandboxUnavailable(SandboxState.NEEDS_SETUP, "Wake is not configured.")
