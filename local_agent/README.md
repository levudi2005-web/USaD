# USaD Local Agent — Sandbox boundary

This package currently contains sandbox data contracts, path/command policy
helpers, and a fail-closed `SandboxProvider` interface. It does **not** launch
processes, create working copies, or claim that WSL2, Docker, or a remote runtime
is installed.

The only provided implementation, `UnsupportedSandboxProvider`, returns
`NEEDS_SETUP` and refuses create/run/stop/hibernate/wake operations. Do not
replace it with direct `subprocess` execution or rely on a separate directory as
a security boundary.

`policy.py` provides input-validation helpers, not an OS sandbox. Path checks
must be repeated at the privileged file-operation boundary to address races and
symlink changes. An eventual provider must enforce command allowlists,
timeouts/output caps, CPU/memory/process/disk limits, network policy, audit
logging, cleanup, and per-project ownership inside an isolated runtime.

The API imports this package from the repository root. The browser frontend is
static and is not connected to the API yet.
