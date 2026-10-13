# USaD security status

## Current protections

- No sandbox command is run by the browser or current backend.
- The local-agent default provider fails closed with `NEEDS_SETUP`.
- The sandbox API exposes only a read-only capability endpoint; separate
  account and project/workspace routes are implemented.
- The command-policy helper accepts argv rather than shell command strings and
  checks an explicit executable allowlist.
- The workspace path helper resolves paths and rejects traversal/symlink
  escapes at validation time.
- Ownership helper compares both project and owner identifiers.
- Output truncation helper reports when bytes were capped.
- Network is documented and reported as deny by default.
- Health and sandbox capability routes are read-only, and the configured
  provider is still `UnsupportedSandboxProvider`.

These helpers are not a complete runtime security boundary. In particular,
validation alone cannot prevent filesystem TOCTOU races or impose operating
system CPU, memory, process, disk, and network limits.

## Local backend configuration

The backend reads `JWT_SECRET` at import time and uses `DATABASE_URL` for
SQLAlchemy sessions. Compose additionally requires MariaDB credentials and an
initial-admin password. Auth routes issue/verify bearer JWTs, while project
routes check ownership or membership for implemented operations. This is not a
reviewed production security boundary: keep the API bound to `127.0.0.1`, do
not enable broad CORS, and never add real credentials to an example
configuration. The health and sandbox-capabilities routes do not require
authentication and provide no deployment-level access control.

VPS1-to-VPS2 transport is not implemented. A future integration must authenticate
the VPS1 service to VPS2, enforce authorization independently on VPS2, use a
narrow protocol rather than Docker API access, and validate identifiers,
workspace paths, limits, request deadlines, idempotency, and bounded output at
the execution boundary.

## Not implemented / not security-tested

- No WSL2, Docker, VM, container, or remote sandbox provider exists.
- No code execution, terminal, test/build runner, file API, or working-copy
  creation exists.
- Basic JWT account routes, SQLAlchemy database access, and owner/member checks
  on current project/workspace routes exist. Comprehensive authorization
  review, durable audit log, task queue, and end-to-end user-isolation tests do
  not.
- No VPS2 provider, network transport, or service-to-service authentication
  protocol exists.
- No resource limits are enforced; values in the model are requested limits
  only.
- No patch application, rollback, hibernate/wake, snapshot, or export/import
  flow exists.
- Sandbox isolation has **not** been security-tested. Unit tests cover API
  status responses and policy helper behavior only; they are not proof of
  sandbox isolation, ownership enforcement by an HTTP API, or VPS-to-VPS
  security.

Do not configure this service to execute untrusted code or expose it as a
production sandbox. Do not mount a Docker socket, grant host root, or pass
credentials into AI task contexts.
