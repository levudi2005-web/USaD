# Team development plan

## Repository survey

This plan reflects the repository files inspected on 2026-10-12. Docker
runtime state could not be queried in this editing environment; the network,
images, containers, existing volume contents, and actual `.env` values have
not been inspected. Never print or commit the local `.env`.

| Area | Present now | Not present / limitation |
|---|---|---|
| Frontend | Static `index.html`, `styles.css`, and `app.js`; navigation, project form, assistant form, and sandbox UI states. | No package manifest/build tool, API client, persisted project UI, configured lint rules, or frontend test runner. Forms explicitly do not save or send requests. |
| Backend | FastAPI app; health endpoint; auth login/me/account routes; authenticated project/workspace endpoints; sandbox capability endpoint. SQLAlchemy, PyMySQL, JWT, and password-hashing dependencies are declared. | The UI is not connected. Health checks process liveness only. API startup requires `JWT_SECRET`; project/auth operations require a compatible database/schema. |
| Database | MariaDB 11.4 Compose service; SQLAlchemy session setup; `users` ORM model; nine-table DDL in `database/usad_schema.sql`; Compose environment variables for DB credentials and URL. | Compose does not mount/run the DDL, migrations are absent, and the admin initializer is not automatically run. The ORM maps only `users`; its `user_id` is signed `BigInteger` while the DDL declares `BIGINT UNSIGNED`. The sample database name previously differed from the DDL name; `.env.example` now uses `usad_dev`. |
| AI API | UI placeholders and future `ai_jobs` schema design are present. | No provider client, API endpoint, key management, task queue, or real AI flow. |
| Sandbox/local agent | Contracts, policy helpers, capability endpoint, and `UnsupportedSandboxProvider`; the provider refuses operations and reports `NEEDS_SETUP`. | No isolated runtime, command execution, working-copy service, resource/network enforcement, or remote transport. Helpers/tests are not a security boundary. |
| Tests/E2E | Python `unittest` files for API contracts and sandbox policy helpers. | No database integration suite, browser automation, frontend test runner, or E2E configuration. |
| Containers | Compose defines MariaDB, Adminer, and backend on `usad_internal`; MariaDB uses named volume `mariadb_data`; backend build uses `backend/Dockerfile`. Dev Container uses local image tag `usad-dev-container-test:latest`. | Compose publishes backend at loopback port 8000 and Adminer at loopback 8081; MariaDB has no host port. The standalone Dev Container is not attached to the Compose network. |

`README.md`, `docs/API.md`, `docs/ARCHITECTURE.md`,
`docs/IMPLEMENTATION_STATUS.md`, and `docs/SECURITY.md` previously described
some APIs/database pieces as absent. The implementation itself contains auth,
project/workspace, and database code; treat the source and tests as current
until any remaining documentation drift is reconciled.

## Module ownership proposal

Use the `DEV-*` IDs as roles, not people names. Assign one owner per module and
agree on API/schema contracts before parallel implementation. File ownership
below is intentionally narrow to reduce merge conflicts.

| ID / module | Scope and candidate files | Interface and dependency | Done criteria and tests |
|---|---|---|---|
| **DEV-1 Frontend/API client** | `index.html`, `app.js`, `styles.css`, and a new frontend API module/tests if selected. Do not edit backend routes or schema. | Depends on DEV-2's agreed auth/project response/error contract. No fake data or success states. | Real login/project/workspace views consume documented endpoints; loading/error/empty states are explicit; token handling is reviewed; keyboard/mobile behavior remains usable. Add browser/component tests when a runner is selected; smoke-test health and capabilities separately. |
| **DEV-2 Backend API and auth** | `backend/app/api/v1/`, `backend/app/main.py`, `backend/app/models.py`, `backend/tests/`. Avoid Compose and DDL edits. | Current routes: `/api/v1/auth/login`, `/me`, `/account`; `/api/v1/projects` and nested workspace routes; `/api/v1/sandboxes/capabilities`. Depends on DEV-3's schema setup and must publish request/response/error contracts to DEV-1. | Authentication/authorization and DB failure paths are tested; every project/workspace query is scoped to the authenticated user; health semantics remain process-only. Extend unit/API tests and add isolated-DB integration tests. |
| **DEV-3 Local environment and data lifecycle** | `docker-compose.yml`, `.devcontainer/`, `.env.example`, `.gitignore`, `database/`, and onboarding docs. Coordinate README changes to avoid conflict. | Owns Compose networking, per-developer project/volume/ports, schema/migration and seed strategy. Depends on DEV-2's supported schema and startup expectations. | Fresh local setup validates Compose config without secrets in output; isolated member projects use distinct volumes/networks; DB schema and optional seed process are explicit/repeatable; no existing/shared data is reset. Test with a fresh disposable local environment only. |
| **DEV-4 Sandbox security/provider** | `local_agent/usad_agent/sandbox/`, `local_agent/tests/`, and sandbox API implementation only after the security design is approved. | Depends on an authenticated identity and ownership contract from DEV-2 plus reviewed threat model. Never replace fail-closed behavior with host `subprocess` execution. | A provider remains disabled until OS-level isolation, network/resource controls, ownership checks, audit, cleanup, and escape tests are reviewed. Unit policy tests alone do not satisfy this gate. |
| **DEV-5 AI integration** | New provider/client and task-service modules, associated tests, and narrowly scoped UI integration with DEV-1. No secrets in frontend or repository. | Depends on an approved provider, server-side secret handling, auth/authorization, and a typed request/response contract. AI execution is not a sandbox. | Provider selection, timeout/rate/error handling, data-retention policy, and permission boundaries are documented and tested with mocked client boundaries; no live credentials in CI. |
| **DEV-6 Quality and integration** | Test configuration, new backend/frontend integration tests, and test documentation. Avoid owning production modules. | Integrates DEV-1 through DEV-5; waits for their public contracts. | CI runs existing Python tests and newly agreed integration checks; E2E runner/browser and fixtures are reproducible and isolated. Database tests never target a developer or shared integration DB. |

### Conflict-reduction rules

1. DEV-3 is the sole owner for Compose, Dev Container, environment templates,
   and database bootstrap changes. Do not edit these in parallel with unrelated
   feature work.
2. DEV-2 owns backend routes/models/tests; DEV-4 owns local-agent policy/provider
   code; DEV-1 owns current static UI files. Coordinate any cross-boundary
   contract change first, then split edits into separate PRs where practical.
3. DEV-5 starts with an interface/design PR; DEV-1 integrates the UI only after
   the server contract and secret-handling review are accepted.
4. Keep DDL changes reviewed by the schema owner. Do not apply DDL to any
   existing database as part of a feature test.
5. Use separate branches/PRs and run the narrow module tests before integration.
   Do not have multiple contributors edit the same Compose or schema file.

## Per-member local environments

### Clone and prepare

Each member should clone into their own directory and use a unique, lowercase
Compose project name (for example `usad-dev-alice`). On PowerShell:

```powershell
$RepositoryUrl = Read-Host "Repository URL"
git clone $RepositoryUrl web-linux-alice
Set-Location web-linux-alice
Copy-Item .env.example .env
```

Edit `.env` locally. Generate distinct MariaDB application/root passwords and
JWT secret per developer; set `DATABASE_URL` to the same app user/password and
database used by `MARIADB_USER`, `MARIADB_PASSWORD`, and `MARIADB_DATABASE`.
URL-encode reserved characters in the password portion of `DATABASE_URL`.
Replace `INITIAL_ADMIN_PASSWORD`. `.env.example` contains placeholders only;
an untracked `.env` is ignored by Git. If `.env` was already committed/tracked,
the ignore rule does not untrack it; verify repository history/status through
the normal reviewed process without displaying its contents. Do not copy
another member's `.env`.

Before starting any services, inspect the target project name and its existing
resources. For a new, unique personal name only, validate interpolation and
then start that personal Compose project:

```powershell
docker compose -p usad-dev-alice --env-file .env config --quiet
docker compose -p usad-dev-alice --env-file .env up -d --build
docker compose -p usad-dev-alice --env-file .env ps
```

Compose project names prefix the default network and named volume, so different
project names yield separate `mariadb_data` volumes and `usad_internal`
networks. Reusing a name intentionally reuses its resources. Never use
`down -v`, volume-prune, or a shared project name to reset a local database.

The current Compose file fixes host ports to loopback `8000` (backend) and
`8081` (Adminer); a unique project name does **not** change those ports. A
second stack on the same host will conflict. For one stack per developer
machine, defaults are distinct across machines. Supporting multiple concurrent
checkouts on one host requires a reviewed port-parameterization change before
launch; this plan does not silently change existing port mappings.

### Database/test separation

Current Python unit tests use no DB. Compose has one MariaDB service/database
and one project-scoped data volume; the schema is not automatically applied,
and `backend.app.init_admin` is not automatically run. The schema file creates
`usad_dev` while the Compose database name is controlled by `.env`; the
template aligns them, but the actual local `.env` has not been inspected.

Until DEV-3 documents migrations/bootstrap, apply the DDL only to a newly
created, personal, disposable database after confirming its target and empty
state. Never use the shared/integration DB for development or tests. A future
DB integration test suite must use a separate database/volume or disposable
service with explicit test credentials and cleanup that cannot resolve to a
developer/shared DB. Do not add a reset command until that guard is tested.

### Dev Container fallback

Current `.devcontainer/devcontainer.json` retains the existing local image
`usad-dev-container-test:latest`, workspace bind mount to `/workspace`, and
`developer` remote user. If a member does not have that tag, build a compatible
local image from the repository before **Dev Containers: Reopen in Container**:

```powershell
docker build -t usad-dev-container-test:latest -f .devcontainer/Dockerfile .
```

The repository Dockerfile uses `node:24-trixie` and installs OpenJDK 21, Git,
Python 3/venv, and renames the base image's `node` user to `developer`, keeping
its UID for common bind-mount ownership. Building may pull the base image and
OS packages if they are not cached. The current image configuration does not
automatically build or pull a different Dev Container image. Do not alter the
existing running container to make this fallback available.

### Service connectivity boundary

Compose services can resolve one another by service name (`backend`,
`mariadb`) on `usad_internal`; the Compose backend can use `mariadb` as its DB
host. The standalone Dev Container is created from an image-based
`devcontainer.json` and is not attached to `usad_internal`. MariaDB has no
published host port, so `mariadb:3306` is not reachable from that Dev Container
as configured. The backend's host port is bound to `127.0.0.1`; connectivity
from a Docker Desktop container through the host gateway has not been tested
and must not be assumed.

No runtime network inspection was possible here. Do not attach the development
container to an existing network by guessed name or run `docker network
connect`. If integrated container-to-service DNS is required, DEV-3 should
inspect the actual Compose project/network and propose a per-developer
Compose-backed Dev Container or explicit project-scoped network design first.
That change must preserve separate per-member DB volumes and must not connect
a personal development container to a shared/integration database by default.

## New-member verification checklist

- [ ] `git status --short` does not show `.env`; do not print `.env` to logs.
- [ ] Dev Container opens at `/workspace`; `whoami` is `developer` and `pwd`
      reports `/workspace`.
- [ ] `node -v` reports Node 24, `java -version` reports Java 21, and
      `git --version` succeeds. The pre-existing local image may have a pinned
      patch version; fallback base tags guarantee the major version only.
- [ ] `docker compose -p usad-dev-alice --env-file .env config --quiet`
      succeeds without exposing secret values.
- [ ] `docker compose -p usad-dev-alice --env-file .env ps` shows only this
      personal project; do not stop or recreate unrelated services.
- [ ] Confirm network and volume names include the chosen Compose project
      prefix; never inspect or mutate another project's database volume.
- [ ] Confirm the expected project source is mounted at `/workspace` and can
      be read/written without creating a second checkout inside the container.
- [ ] Run the Python unit tests using the repository's documented command.
- [ ] Check `GET /api/v1/health` and `GET /api/v1/sandboxes/capabilities`;
      health is process liveness only and capabilities should remain
      `NEEDS_SETUP` with execution disabled.
- [ ] Before testing authenticated/project endpoints, confirm the database
      schema exists in this personal environment and the admin user was
      explicitly initialized. Do not run schema/seed steps against any
      pre-existing or shared database.
- [ ] E2E, real AI calls, and sandbox execution remain unavailable until their
      implementation and safety gates are completed.

## Validation status for this change

The repository files were inspected directly. Shell and Docker commands were
not run: the available shell tool reported that sandbox startup failed because
`bubblewrap` (`bwrap`) is unavailable. Therefore Compose interpolation,
Dockerfile build, image contents, actual network membership, host port
availability, DB schema state, and test results are **not verified**. No
container, image, network, volume, database, or Git history was changed by
validation.
