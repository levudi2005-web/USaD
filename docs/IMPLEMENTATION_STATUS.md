# USaD implementation status

## Scope inspected

The workspace contains a static frontend (`index.html`, `styles.css`, `app.js`),
a fail-closed sandbox contract under `local_agent`, and a FastAPI API with
health, account, project/workspace, and sandbox capability routes. The frontend
is not wired to the API. There is no AI provider connection, sandbox runtime,
or frontend test/build manifest.

The backend dependencies include FastAPI, Uvicorn, SQLAlchemy, PyMySQL, JWT,
and password hashing. `JWT_SECRET` is required when the app loads;
`DATABASE_URL` configures database access. Compose also requires MariaDB
credentials and an initial-admin password. Local development should bind to
`127.0.0.1`. Health/capability API tests are in `backend/tests`; the schema
exists in `database/usad_schema.sql` but is not applied by Compose.

## Frontend consolidation

The sidebar now has seven valid destinations: Dashboard, Projects, Workspace,
AI Assistant, AI Workflow, Sandbox & Terminal, and Settings. The former
separate IDE, terminal, file manager, provider, server, reports, database, and
automation demo screens were removed from navigation/UI; backend/local-agent
modules were not removed.

Dashboard sample metrics and server/project/task lists have been removed.
Workspace shows disconnected empty states rather than pretend source files or
AI responses. Sandbox and terminal are consolidated with the existing
`NEEDS_SETUP` state and disabled controls. AI tasks, provider status, logs,
diffs, and tests are empty until real API data is available.

The project modal remains usable for opening/closing and validating input, but
its submit path explicitly reports that no project was created because the
frontend is not connected to the implemented project API.

## Sandbox vertical slice

| Area | Status | Notes |
|---|---|---|
| Workspace/source separation UI | Interface | Shows source boundary; no file access API |
| Sandbox UI/tabs | Interface | `NEEDS_SETUP`; action controls disabled |
| Sandbox metadata/state contract | Prototype | Dataclasses and required lifecycle states |
| `SandboxProvider` interface | Prototype | No local or remote execution implementation |
| Default provider | Implemented fail-closed | Rejects all operations with `NEEDS_SETUP` |
| Path/argv/owner/output helpers | Prototype | Unit tests authored; not an OS security boundary |
| Backend API | Partial | Health, JWT account routes, DB-backed project/workspace routes, and read-only sandbox capabilities; no sandbox execution |
| VPS1-to-VPS2 adapter/transport | Not implemented | No protocol, service identity, or network client |
| AI task queue/project memory/advanced permission model | Not implemented | Basic project owner/member checks exist; no full permission system |
| Audit persistence | Not implemented | No commands run, so no runtime audit records |
| Resource/network enforcement | Not implemented | Model defaults are not runtime enforcement |
| Diff/apply/discard/rollback | Not implemented | No working copy provider |
| Hibernate/wake/snapshots | Not implemented | No process or RAM snapshot claims |
| Export/import | Not implemented | Must still validate manifest and zip paths |

## Validation

Policy tests cover traversal, symlink escape, executable allowlisting, output
caps, project/owner helper checks, and fail-closed provider behavior. API tests
cover the health and read-only capability route contract and assert that no
execution route is exposed. These tests do not validate HTTP authentication,
runtime isolation, or a VPS integration.

After UI consolidation, the browser preview was reloaded and verified:

- All seven sidebar destinations activate their matching pages; all shortcut
  links resolve to existing pages.
- Both Workspace tabs and all five Sandbox tabs switch to their matching panel.
- Sandbox remains `NEEDS_SETUP`; all six runtime/action controls are disabled.
- The project modal opens and closes, Escape closes it, the required project
  name is validated, and submitting explicitly reports that no project was
  created or saved.
- At a 390px viewport, the document has no horizontal overflow (375px content
  width); the Workspace editor panel renders within the viewport.
- No browser JavaScript or console errors were observed during the smoke run.
- Editor diagnostics reported no problems in `index.html`, `app.js`, or
  `styles.css`.

No frontend test/build runner is configured in the workspace. The editor
reported no diagnostics in the changed Python files. The integrated test
runner returned `No tests found in the files` for Python `unittest` sources.
The direct command
`C:\Users\USaD\AppData\Local\Programs\Python\Python312\python.exe -m unittest backend.tests.test_api local_agent.tests.test_sandbox_policy`
could not start: the PowerShell tool reported that Windows sandbox network
filtering is unsupported because the host loopback listener requires private
network access. Therefore neither Python test module has a test result from
this session. No security test has validated runtime isolation.

## Next safe steps

1. Establish a reviewed threat model and define a versioned internal VPS
   protocol with service-to-service authentication and key rotation.
2. Review and expand authorization coverage before adding further mutation
   APIs; basic JWT and project owner/member checks already exist.
3. Select an isolated provider; do not enable execution until resource/network
   enforcement and escape tests pass.
4. Implement working-copy diff/apply/rollback and durable audit records.
5. Integrate task queue, project memory, export/import, and hibernate/wake.
