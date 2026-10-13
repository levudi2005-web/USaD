# USaD API

API prefix: `/api/v1`

## Implemented

### `GET /api/v1/health`

Returns `{"status":"ok","service":"usad-api"}` while the FastAPI process can
serve requests. This is a process liveness check only; it does not assert
database, Redis, local-agent, WSL2, or sandbox readiness.

### `GET /api/v1/sandboxes/capabilities`

Read-only capability response for the currently configured provider:

```json
{
  "provider": "unconfigured",
  "state": "NEEDS_SETUP",
  "execution_enabled": false,
  "network_default": "deny",
  "reason": "No security-tested isolated runtime is configured. Commands will not run on the host."
}
```

No sandbox control, arbitrary command, patch-apply, export/import, hibernate, or
wake endpoint is enabled. The frontend currently displays these controls as
disabled rather than sending requests that could imply a successful operation.
This read-only endpoint provides runtime capability status, not caller
authentication or authorization. Keep the API bound to loopback; this endpoint
does not make the sandbox authenticated or safe to expose.

### Authentication and account routes

The current API has the following routes:

- `POST /api/v1/auth/login` — verifies a username/password and returns a bearer
  JWT.
- `GET /api/v1/auth/me` — returns the current account; requires a bearer JWT.
- `PATCH /api/v1/auth/account` — changes the authenticated user's username
  and/or password; requires a bearer JWT.

The JWT secret is read from `JWT_SECRET` at app import time. Account lookup and
password updates use the configured SQLAlchemy database session.

### Project and workspace routes

- `GET /api/v1/projects` — lists projects owned by or shared with the
  authenticated user.
- `POST /api/v1/projects` — creates a project owned by the authenticated user.
- `GET /api/v1/projects/{project_id}` — reads a project if the caller owns or
  belongs to it.
- `PATCH /api/v1/projects/{project_id}` — updates an owned project.
- `GET /api/v1/projects/{project_id}/workspaces` — lists workspace metadata
  after project access is checked.
- `POST /api/v1/projects/{project_id}/workspaces` — creates workspace metadata
  for an owned project.

These routes require the DDL in `database/usad_schema.sql` to have been applied
to the configured database. Creating workspace metadata does **not** create a
directory or working copy. Compose does not apply the DDL automatically.

## Future sandbox contract (not implemented)

Future sandbox resource endpoints must authenticate the caller and authorize
both owner and project association on every request. A client-provided owner ID
is not an identity. Mutating operations must be audited and protected by
project permissions. Existing account/project routes do not implement sandbox
authorization or runtime controls.

For a future VPS1-to-VPS2 internal protocol, define a versioned, narrow
service-to-service API before implementing a provider. Send typed lifecycle and
approved-command requests with opaque sandbox/project identifiers, bounded
request and response sizes, deadlines, idempotency keys for mutations, and
correlation IDs. VPS2 must independently verify the VPS1 service identity and
re-check sandbox ownership/association before every operation. Do not expose
Docker's API or accept host shell commands. Authentication details and key
rotation remain undecided; no network client or credentials are configured.

- `POST /sandboxes` — create isolated working copy
- `GET /sandboxes/{sandbox_id}` — read owned sandbox metadata
- `POST /sandboxes/{sandbox_id}/commands` — run only policy-approved argv
- `POST /sandboxes/{sandbox_id}/stop`
- `POST /sandboxes/{sandbox_id}/hibernate`
- `POST /sandboxes/{sandbox_id}/wake`
- `GET /sandboxes/{sandbox_id}/diff`
- `POST /sandboxes/{sandbox_id}/apply` — permission-checked, reviewed patch only
- `DELETE /sandboxes/{sandbox_id}/working-copy` — explicit discard confirmation

These routes must not be exposed until authentication, authorization,
idempotency, resource controls, audit persistence, and a security-tested
`SandboxProvider` are implemented.
