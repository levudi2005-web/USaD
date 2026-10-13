import tempfile
import unittest
from pathlib import Path

from local_agent.usad_agent.sandbox.models import ResourceLimits, SandboxRecord, SandboxState
from local_agent.usad_agent.sandbox.policy import (
    CommandPolicy,
    SandboxAccessDenied,
    SandboxPolicyError,
    limit_output,
    require_sandbox_owner,
    resolve_workspace_path,
)
from local_agent.usad_agent.sandbox.provider import SandboxUnavailable, UnsupportedSandboxProvider
from local_agent.usad_agent.sandbox.service import SandboxService


class SandboxPolicyTests(unittest.TestCase):
    def test_rejects_parent_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "workspace"
            root.mkdir()
            with self.assertRaises(SandboxPolicyError):
                resolve_workspace_path(root, "../outside.txt")

    def test_rejects_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "workspace"
            root.mkdir()
            outside = base / "outside"
            outside.mkdir()
            try:
                (root / "escape").symlink_to(outside, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"Symlink creation is unavailable: {error}")
            with self.assertRaises(SandboxPolicyError):
                resolve_workspace_path(root, "escape/secret.txt")

    def test_command_policy_requires_exact_allowlisted_executable(self) -> None:
        policy = CommandPolicy(frozenset({"pytest"}))
        self.assertEqual(policy.validate_argv(["pytest", "-q"]), ("pytest", "-q"))
        with self.assertRaises(SandboxPolicyError):
            policy.validate_argv(["powershell.exe", "-Command", "whoami"])
        with self.assertRaises(SandboxPolicyError):
            policy.validate_argv(["pytest\x00", "-q"])
        with self.assertRaises(SandboxPolicyError):
            policy.validate_argv([r"C:\untrusted\pytest", "-q"])

    def test_output_is_bounded_and_reports_truncation(self) -> None:
        self.assertEqual(limit_output(b"123456", 4), (b"1234", True))
        self.assertEqual(limit_output(b"12", 4), (b"12", False))

    def test_sandbox_access_is_bound_to_owner_and_project(self) -> None:
        sandbox = SandboxRecord(project_id="project-a", owner_id="user-a", runtime="python")
        require_sandbox_owner(sandbox, owner_id="user-a", project_id="project-a")
        with self.assertRaises(SandboxAccessDenied):
            require_sandbox_owner(sandbox, owner_id="user-b", project_id="project-a")
        with self.assertRaises(SandboxAccessDenied):
            require_sandbox_owner(sandbox, owner_id="user-a", project_id="project-b")

    def test_unconfigured_provider_fails_closed(self) -> None:
        provider = UnsupportedSandboxProvider()
        service = SandboxService(provider)
        self.assertEqual(service.capabilities().state, SandboxState.NEEDS_SETUP)
        self.assertFalse(service.capabilities().execution_enabled)
        with self.assertRaises(SandboxUnavailable):
            provider.create(
                project_id="project-a",
                owner_id="user-a",
                runtime="python",
                limits=ResourceLimits(),
            )
        record = SandboxRecord(project_id="project-a", owner_id="user-a", runtime="python")
        for operation in (
            lambda: provider.run_approved(
                record, ["pytest"], timeout_seconds=5, output_limit_bytes=64
            ),
            lambda: provider.stop(record),
            lambda: provider.hibernate(record),
            lambda: provider.wake(record),
        ):
            with self.assertRaises(SandboxUnavailable):
                operation()


if __name__ == "__main__":
    unittest.main()
