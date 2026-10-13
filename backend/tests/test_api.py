import unittest

from fastapi.routing import APIRoute

from backend.app.api.v1.sandboxes import get_sandbox_capabilities
from backend.app.main import app, health


class BackendApiTests(unittest.TestCase):
    def test_health_reports_process_liveness_only(self) -> None:
        response = health()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, b'{"status":"ok","service":"usad-api"}')

    def test_capabilities_are_unconfigured_and_fail_closed(self) -> None:
        response = get_sandbox_capabilities()

        self.assertEqual(response.provider, "unconfigured")
        self.assertEqual(response.state, "NEEDS_SETUP")
        self.assertFalse(response.execution_enabled)
        self.assertEqual(response.network_default, "deny")

    def test_only_health_and_read_only_capabilities_are_exposed(self) -> None:
        routes = {
            (method, route.path)
            for route in app.routes
            if isinstance(route, APIRoute)
            for method in route.methods or set()
        }

        self.assertIn(("GET", "/api/v1/health"), routes)
        self.assertIn(("GET", "/api/v1/sandboxes/capabilities"), routes)
        self.assertFalse(
            any(
                path.startswith("/api/v1/sandboxes/")
                and path != "/api/v1/sandboxes/capabilities"
                for _, path in routes
            )
        )


if __name__ == "__main__":
    unittest.main()
