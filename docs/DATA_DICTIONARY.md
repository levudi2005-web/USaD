# USaD Data Dictionary

This document describes [`../database/usad_schema.sql`](../database/usad_schema.sql)
without adding or changing database objects. The SQL file is the schema source
of truth and has not been executed by this project.

## Database conventions

- Database: `usad_dev`.
- Engine: InnoDB for all nine tables.
- Character set and collation: `utf8mb4` and `utf8mb4_unicode_ci`.
- Primary and foreign-key identifiers: `BIGINT UNSIGNED`; generated IDs use
  `AUTO_INCREMENT`.
- Timestamps use `DATETIME`; created timestamps default to
  `CURRENT_TIMESTAMP`. Tables with `updated_at` update it automatically on
  row updates.
- Named `CHECK`, `UNIQUE`, foreign-key, and index constraints are listed with
  each table below. MySQL versions before 8.0.16 parse but do not enforce
  `CHECK` constraints; use a version that enforces them when validating this
  design.

## Tables and columns

### `users`

User accounts.

| Column | Definition | Meaning |
|---|---|---|
| `user_id` | `BIGINT UNSIGNED NOT NULL AUTO_INCREMENT` | Primary identifier. |
| `username` | `VARCHAR(50) NOT NULL` | Unique username. |
| `email` | `VARCHAR(255) NOT NULL` | Unique email address. |
| `password_hash` | `VARCHAR(255) NOT NULL` | Password hash only; never plaintext. |
| `display_name` | `VARCHAR(100) NOT NULL` | Display name. |
| `account_status` | `VARCHAR(20) NOT NULL DEFAULT 'active'` | `active`, `disabled`, or `pending`. |
| `created_at` | `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP` | Creation time. |
| `updated_at` | `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | Last row update time. |

Constraints: `pk_users` primary key; `uq_users_username` unique on `username`;
`uq_users_email` unique on `email`; `chk_users_status` restricts account status
to the three listed values.

### `projects`

Projects owned by one user.

| Column | Definition | Meaning |
|---|---|---|
| `project_id` | `BIGINT UNSIGNED NOT NULL AUTO_INCREMENT` | Primary identifier. |
| `owner_user_id` | `BIGINT UNSIGNED NOT NULL` | Owner; references `users.user_id`. |
| `project_name` | `VARCHAR(150) NOT NULL` | Project name. |
| `description` | `TEXT NULL` | Optional description. |
| `project_status` | `VARCHAR(20) NOT NULL DEFAULT 'active'` | `active`, `archived`, or `disabled`. |
| `created_at` | `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP` | Creation time. |
| `updated_at` | `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | Last row update time. |

Constraints: `pk_projects`; `fk_projects_owner` references `users(user_id)`
with `ON UPDATE RESTRICT ON DELETE RESTRICT`; `chk_projects_status`; index
`idx_projects_owner(owner_user_id)`.

### `project_members`

Many-to-many membership between users and projects.

| Column | Definition | Meaning |
|---|---|---|
| `project_id` | `BIGINT UNSIGNED NOT NULL` | Project; references `projects.project_id`. |
| `user_id` | `BIGINT UNSIGNED NOT NULL` | Member; references `users.user_id`. |
| `member_role` | `VARCHAR(20) NOT NULL DEFAULT 'member'` | `owner`, `admin`, `member`, or `viewer`. |
| `joined_at` | `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP` | Membership creation time. |

Constraints: composite primary key `pk_project_members(project_id, user_id)`;
`fk_project_members_project` and `fk_project_members_user` both use
`ON UPDATE RESTRICT ON DELETE RESTRICT`; `chk_project_members_role`; index
`idx_project_members_user(user_id)`.

### `workspaces`

Workspaces belonging to a project.

| Column | Definition | Meaning |
|---|---|---|
| `workspace_id` | `BIGINT UNSIGNED NOT NULL AUTO_INCREMENT` | Primary identifier. |
| `project_id` | `BIGINT UNSIGNED NOT NULL` | Parent project; references `projects.project_id`. |
| `workspace_name` | `VARCHAR(150) NOT NULL` | Name unique within its project. |
| `storage_path` | `VARCHAR(500) NOT NULL` | Unique configured storage path. |
| `workspace_status` | `VARCHAR(20) NOT NULL DEFAULT 'active'` | `active`, `archived`, or `disabled`. |
| `created_at` | `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP` | Creation time. |
| `updated_at` | `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | Last row update time. |

Constraints: `pk_workspaces`; `fk_workspaces_project` references
`projects(project_id)` with `ON UPDATE RESTRICT ON DELETE RESTRICT`;
`uq_workspaces_project_name(project_id, workspace_name)`;
`uq_workspaces_storage_path(storage_path)`; `chk_workspaces_status`; index
`idx_workspaces_project(project_id)`.

### `runtime_nodes`

Execution-node metadata, such as a future VPS2 runtime. This table explicitly
does not store private keys or authentication tokens.

| Column | Definition | Meaning |
|---|---|---|
| `node_id` | `BIGINT UNSIGNED NOT NULL AUTO_INCREMENT` | Primary identifier. |
| `node_name` | `VARCHAR(100) NOT NULL` | Unique node name. |
| `node_type` | `VARCHAR(30) NOT NULL DEFAULT 'docker'` | `docker` or `virtual_machine`. |
| `internal_endpoint` | `VARCHAR(255) NULL` | Optional internal endpoint; not proof of connectivity. |
| `node_status` | `VARCHAR(20) NOT NULL DEFAULT 'unconfigured'` | `unconfigured`, `online`, `offline`, or `maintenance`. |
| `created_at` | `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP` | Creation time. |
| `updated_at` | `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | Last row update time. |

Constraints: `pk_runtime_nodes`; `uq_runtime_nodes_name(node_name)`;
`chk_runtime_nodes_type`; `chk_runtime_nodes_status`. No authentication
credential column is defined.

### `sandboxes`

Sandbox metadata associated with a workspace and runtime node. A database row
does not establish that a container exists or is running.

| Column | Definition | Meaning |
|---|---|---|
| `sandbox_id` | `BIGINT UNSIGNED NOT NULL AUTO_INCREMENT` | Primary identifier. |
| `workspace_id` | `BIGINT UNSIGNED NOT NULL` | Workspace; references `workspaces.workspace_id`. |
| `node_id` | `BIGINT UNSIGNED NOT NULL` | Runtime node; references `runtime_nodes.node_id`. |
| `created_by_user_id` | `BIGINT UNSIGNED NOT NULL` | Creator; references `users.user_id`. |
| `runtime_ref` | `VARCHAR(255) NULL` | Optional reference assigned by runtime. |
| `sandbox_name` | `VARCHAR(150) NOT NULL` | Sandbox name. |
| `image_name` | `VARCHAR(255) NOT NULL` | Runtime image name. |
| `cpu_limit` | `DECIMAL(5,2) NOT NULL DEFAULT 0.50` | Requested CPU limit; schema does not enforce runtime limits. |
| `memory_limit_mb` | `INT UNSIGNED NOT NULL DEFAULT 512` | Requested memory limit in MiB. |
| `pids_limit` | `INT UNSIGNED NOT NULL DEFAULT 128` | Requested process limit. |
| `network_enabled` | `BOOLEAN NOT NULL DEFAULT FALSE` | Requested network flag; not runtime enforcement. |
| `sandbox_status` | `VARCHAR(20) NOT NULL DEFAULT 'pending'` | `pending`, `running`, `stopped`, `failed`, or `deleting`. |
| `created_at` | `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP` | Creation time. |
| `updated_at` | `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | Last row update time. |

Constraints: `pk_sandboxes`; `fk_sandboxes_workspace`,
`fk_sandboxes_node`, and `fk_sandboxes_creator`, each with
`ON UPDATE RESTRICT ON DELETE RESTRICT`; `uq_sandboxes_node_runtime(node_id,
runtime_ref)`; positive-value checks `chk_sandboxes_cpu`,
`chk_sandboxes_memory`, and `chk_sandboxes_pids`; `chk_sandboxes_status`;
indexes `idx_sandboxes_workspace(workspace_id)`,
`idx_sandboxes_node_status(node_id, sandbox_status)`, and
`idx_sandboxes_creator(created_by_user_id)`.

### `sandbox_sessions`

Terminal-use sessions associated with a sandbox and user.

| Column | Definition | Meaning |
|---|---|---|
| `session_id` | `BIGINT UNSIGNED NOT NULL AUTO_INCREMENT` | Primary identifier. |
| `sandbox_id` | `BIGINT UNSIGNED NOT NULL` | Sandbox; references `sandboxes.sandbox_id`. |
| `user_id` | `BIGINT UNSIGNED NOT NULL` | User; references `users.user_id`. |
| `session_status` | `VARCHAR(20) NOT NULL DEFAULT 'active'` | `active`, `closed`, or `failed`. |
| `started_at` | `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP` | Start time. |
| `ended_at` | `DATETIME NULL` | Optional end time. |

Constraints: `pk_sandbox_sessions`; `fk_sandbox_sessions_sandbox` and
`fk_sandbox_sessions_user` with `ON UPDATE RESTRICT ON DELETE RESTRICT`;
`chk_sandbox_sessions_status`; `chk_sandbox_sessions_time` ensures end time is
null or no earlier than start time; indexes
`idx_sandbox_sessions_sandbox(sandbox_id)` and
`idx_sandbox_sessions_user_status(user_id, session_status)`.

### `audit_logs`

Event records optionally associated with a user, project, and sandbox.

| Column | Definition | Meaning |
|---|---|---|
| `log_id` | `BIGINT UNSIGNED NOT NULL AUTO_INCREMENT` | Primary identifier. |
| `user_id` | `BIGINT UNSIGNED NULL` | Optional user; references `users.user_id`. |
| `project_id` | `BIGINT UNSIGNED NULL` | Optional project; references `projects.project_id`. |
| `sandbox_id` | `BIGINT UNSIGNED NULL` | Optional sandbox; references `sandboxes.sandbox_id`. |
| `action_name` | `VARCHAR(100) NOT NULL` | Event/action name. |
| `result_status` | `VARCHAR(20) NOT NULL` | `success`, `failure`, or `denied`. |
| `details` | `TEXT NULL` | Optional event details; must not contain secrets. |
| `created_at` | `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP` | Event time. |

Constraints: `pk_audit_logs`; `fk_audit_logs_user`,
`fk_audit_logs_project`, and `fk_audit_logs_sandbox` with
`ON UPDATE RESTRICT ON DELETE RESTRICT`; `chk_audit_logs_result`; indexes
`idx_audit_logs_user_time(user_id, created_at)`,
`idx_audit_logs_project_time(project_id, created_at)`, and
`idx_audit_logs_sandbox_time(sandbox_id, created_at)`.

### `ai_jobs`

AI job tracking associated with a user and project, with an optional workspace.

| Column | Definition | Meaning |
|---|---|---|
| `job_id` | `BIGINT UNSIGNED NOT NULL AUTO_INCREMENT` | Primary identifier. |
| `user_id` | `BIGINT UNSIGNED NOT NULL` | Requesting user; references `users.user_id`. |
| `project_id` | `BIGINT UNSIGNED NOT NULL` | Project; references `projects.project_id`. |
| `workspace_id` | `BIGINT UNSIGNED NULL` | Optional workspace; references `workspaces.workspace_id`. |
| `job_type` | `VARCHAR(50) NOT NULL` | Job type. |
| `job_status` | `VARCHAR(20) NOT NULL DEFAULT 'queued'` | `queued`, `running`, `completed`, `failed`, or `cancelled`. |
| `input_summary` | `TEXT NULL` | Optional input summary. |
| `result_summary` | `TEXT NULL` | Optional result summary. |
| `error_message` | `TEXT NULL` | Optional error description. |
| `created_at` | `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP` | Creation time. |
| `started_at` | `DATETIME NULL` | Optional start time. |
| `finished_at` | `DATETIME NULL` | Optional finish time. |

Constraints: `pk_ai_jobs`; `fk_ai_jobs_user`, `fk_ai_jobs_project`, and
`fk_ai_jobs_workspace` with `ON UPDATE RESTRICT ON DELETE RESTRICT`;
`chk_ai_jobs_status`; indexes `idx_ai_jobs_user_created(user_id, created_at)`,
`idx_ai_jobs_project_status(project_id, job_status)`, and
`idx_ai_jobs_workspace(workspace_id)`.

## Relationship summary

- One user may own many projects (`projects.owner_user_id`).
- Users and projects have an N-N membership relation through
  `project_members`.
- One project may have many workspaces.
- A sandbox references one workspace, one runtime node, and its creator.
- A sandbox may have many terminal sessions; each session references a user.
- Audit entries optionally reference one user, project, and sandbox.
- An AI job references one user and project, and may reference one workspace.

All declared foreign keys use `ON UPDATE RESTRICT ON DELETE RESTRICT`. Foreign
keys ensure referenced rows exist; they do not enforce the cross-row access and
consistency rules listed in the security notes in the PowerDesigner guide.
