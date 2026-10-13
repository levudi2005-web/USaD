# USaD architecture

## Current workspace

The existing browser application is a static HTML/CSS/JavaScript demo. Its
workspace and sandbox pages communicate the source/working-copy boundary, but
they are not connected to file storage, task queue, project memory, or runtime
services.

The current backend is FastAPI with:

- `/api/v1/health` for API process health only.
- `/api/v1/sandboxes/capabilities` as a read-only provider status endpoint.
- `/api/v1/auth/*` for JWT login and account operations.
- `/api/v1/projects/*` for authenticated project and workspace metadata
  operations backed by SQLAlchemy and MariaDB.
- `local_agent.usad_agent.sandbox` for metadata/state contracts, validation
  helpers, and the `SandboxProvider` abstraction.
- `UnsupportedSandboxProvider` as the only configured provider; create/run/
  stop/hibernate/wake remain unavailable.

The static frontend calls health, sandbox capabilities, account, project, and
workspace routes through the local preview server's same-origin `/api/v1/*`
proxy. AI Chat, task queue, terminal/log streaming, and file access remain
unwired. The DDL exists in `database/usad_schema.sql`, but Compose does not
apply it or initialize the admin account automatically. API process liveness
does not imply database readiness. Run the backend bound to loopback.

## Sandbox design boundary

An authenticated sandbox service should eventually create an isolated working
copy for a specific `(owner_id, project_id)`. The current account/project
routes do not create a working copy or authorize sandbox operations. AI reads
only granted source paths. Proposed changes and tests run against the copy,
then logs and diff are reviewed before a policy-authorized apply. Original
files must remain unchanged if review or permission checks fail.

Provider implementations are intended for a local WSL2 boundary and a separately
isolated remote runtime. Neither is implemented here. Docker is not assumed.
Host subprocesses, a separate directory, or a Windows user process are not
considered a secure sandbox.

## VPS1/VPS2 target boundary (design only)

- **VPS1 control plane:** current basic account/project routes are a prototype;
  future work includes complete project authorization, sandbox metadata,
  session orchestration, and durable audit records.
- **VPS2 execution plane:** future isolated runtime lifecycle, workspace
  storage, enforced resource/network limits, and bounded command execution.
- **Transport:** not implemented. Before connecting the hosts, specify and
  test a narrow versioned service API plus service-to-service authentication,
  identity rotation/revocation, replay/idempotency rules, request deadlines,
  and ownership checks at both ends.

The existing `SandboxProvider` is the local abstraction seam. There is
intentionally no VPS2 adapter or network transport yet: the protocol,
authentication, authorization store, and runtime threat model are not defined.
No Docker socket is mounted, Docker TCP API is exposed, arbitrary host command
is accepted, or VPS configuration is changed by this project in its current
state.

The required lifecycle is `CREATED → STARTING → READY → RUNNING → STOPPING →
STOPPED`, with `HIBERNATED` and `FAILED` branches. Current provider readiness is
`NEEDS_SETUP`; lifecycle transitions are contracts only. Future hibernate
persists file/metadata state and must not claim RAM/process snapshots unless
those are actually supported.

## Related services not yet integrated

AI task queue, project memory, permissions, audit persistence, export/import,
Auto Hibernate, snapshot/restore, and frontend API wiring remain separate
implementation steps. Sandbox command execution must remain disabled until
those boundaries and OS-level resource/network enforcement are in place.
