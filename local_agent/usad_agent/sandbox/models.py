from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4


class SandboxState(StrEnum):
    CREATED = "CREATED"
    STARTING = "STARTING"
    READY = "READY"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    HIBERNATED = "HIBERNATED"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    NEEDS_SETUP = "NEEDS_SETUP"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class ResourceLimits:
    cpu_cores: float = 1.0
    memory_bytes: int = 512 * 1024 * 1024
    process_count: int = 64
    disk_bytes: int = 2 * 1024 * 1024 * 1024
    command_timeout_seconds: int = 30
    output_bytes: int = 256 * 1024
    network_enabled: bool = False

    def __post_init__(self) -> None:
        if self.cpu_cores <= 0:
            raise ValueError("cpu_cores must be positive")
        if min(
            self.memory_bytes,
            self.process_count,
            self.disk_bytes,
            self.command_timeout_seconds,
            self.output_bytes,
        ) <= 0:
            raise ValueError("resource limits must be positive")


@dataclass
class SandboxRecord:
    project_id: str
    owner_id: str
    runtime: str
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    sandbox_id: str = field(default_factory=lambda: str(uuid4()))
    status: SandboxState = SandboxState.CREATED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_active_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    logs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SandboxCapabilities:
    provider: str
    state: SandboxState
    execution_enabled: bool
    network_default: str
    reason: str
