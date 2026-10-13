from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .models import ResourceLimits, SandboxRecord


class SandboxPolicyError(ValueError):
    pass


class SandboxAccessDenied(PermissionError):
    pass


@dataclass(frozen=True)
class CommandPolicy:
    allowed_executables: frozenset[str]
    limits: ResourceLimits = ResourceLimits()
    max_arguments: int = 64
    max_argument_characters: int = 4096

    def validate_argv(self, argv: Sequence[str]) -> tuple[str, ...]:
        if not argv or len(argv) > self.max_arguments:
            raise SandboxPolicyError("Command argument count is invalid.")
        if any(not isinstance(arg, str) or not arg or "\x00" in arg for arg in argv):
            raise SandboxPolicyError("Command arguments must be non-empty strings without NUL.")
        if any(len(arg) > self.max_argument_characters for arg in argv):
            raise SandboxPolicyError("A command argument exceeds the configured size limit.")

        executable = argv[0].lower()
        if (
            "/" in executable
            or "\\" in executable
            or ":" in executable
            or executable not in self.allowed_executables
        ):
            raise SandboxPolicyError("Executable is not in the workspace command allowlist.")
        return tuple(argv)


def resolve_workspace_path(workspace_root: Path, requested_path: str) -> Path:
    """Resolve an existing workspace path and reject traversal/symlink escapes."""
    if not requested_path or "\x00" in requested_path:
        raise SandboxPolicyError("Workspace path is invalid.")

    root = workspace_root.resolve(strict=True)
    if not root.is_dir():
        raise SandboxPolicyError("Workspace root must be a directory.")

    candidate = (root / requested_path).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SandboxPolicyError("Path is outside the granted workspace.") from exc
    return candidate


def require_sandbox_owner(
    sandbox: SandboxRecord, *, owner_id: str, project_id: str
) -> None:
    if sandbox.owner_id != owner_id or sandbox.project_id != project_id:
        raise SandboxAccessDenied("Sandbox is not owned by this user and project.")


def limit_output(data: bytes, max_bytes: int) -> tuple[bytes, bool]:
    if max_bytes <= 0:
        raise SandboxPolicyError("Output limit must be positive.")
    if len(data) <= max_bytes:
        return data, False
    return data[:max_bytes], True
