CREATE DATABASE IF NOT EXISTS usad_dev
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE usad_dev;

-- 1. USERS: tài khoản người dùng
CREATE TABLE users (
    user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    account_status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_users PRIMARY KEY (user_id),
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT chk_users_status
        CHECK (account_status IN ('active', 'disabled', 'pending'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. PROJECTS: dự án, mỗi dự án có một chủ sở hữu
CREATE TABLE projects (
    project_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    owner_user_id BIGINT UNSIGNED NOT NULL,
    project_name VARCHAR(150) NOT NULL,
    description TEXT NULL,
    project_status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_projects PRIMARY KEY (project_id),
    CONSTRAINT fk_projects_owner
        FOREIGN KEY (owner_user_id) REFERENCES users(user_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT chk_projects_status
        CHECK (project_status IN ('active', 'archived', 'disabled')),
    INDEX idx_projects_owner (owner_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. PROJECT_MEMBERS: bảng nối quan hệ N-N users và projects
CREATE TABLE project_members (
    project_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    member_role VARCHAR(20) NOT NULL DEFAULT 'member',
    joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_project_members PRIMARY KEY (project_id, user_id),
    CONSTRAINT fk_project_members_project
        FOREIGN KEY (project_id) REFERENCES projects(project_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_project_members_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT chk_project_members_role
        CHECK (member_role IN ('owner', 'admin', 'member', 'viewer')),
    INDEX idx_project_members_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. WORKSPACES: workspace thuộc một dự án
CREATE TABLE workspaces (
    workspace_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    project_id BIGINT UNSIGNED NOT NULL,
    workspace_name VARCHAR(150) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    workspace_status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_workspaces PRIMARY KEY (workspace_id),
    CONSTRAINT fk_workspaces_project
        FOREIGN KEY (project_id) REFERENCES projects(project_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT uq_workspaces_project_name
        UNIQUE (project_id, workspace_name),
    CONSTRAINT uq_workspaces_storage_path UNIQUE (storage_path),
    CONSTRAINT chk_workspaces_status
        CHECK (workspace_status IN ('active', 'archived', 'disabled')),
    INDEX idx_workspaces_project (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. RUNTIME_NODES: máy thực thi, ví dụ VPS2
-- Không lưu private key hoặc token xác thực tại đây.
CREATE TABLE runtime_nodes (
    node_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    node_name VARCHAR(100) NOT NULL,
    node_type VARCHAR(30) NOT NULL DEFAULT 'docker',
    internal_endpoint VARCHAR(255) NULL,
    node_status VARCHAR(20) NOT NULL DEFAULT 'unconfigured',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_runtime_nodes PRIMARY KEY (node_id),
    CONSTRAINT uq_runtime_nodes_name UNIQUE (node_name),
    CONSTRAINT chk_runtime_nodes_type
        CHECK (node_type IN ('docker', 'virtual_machine')),
    CONSTRAINT chk_runtime_nodes_status
        CHECK (node_status IN ('unconfigured', 'online', 'offline', 'maintenance'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. SANDBOXES: metadata của môi trường Linux
-- Bản ghi database không chứng minh container thực sự đang chạy.
CREATE TABLE sandboxes (
    sandbox_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    workspace_id BIGINT UNSIGNED NOT NULL,
    node_id BIGINT UNSIGNED NOT NULL,
    created_by_user_id BIGINT UNSIGNED NOT NULL,
    runtime_ref VARCHAR(255) NULL,
    sandbox_name VARCHAR(150) NOT NULL,
    image_name VARCHAR(255) NOT NULL,
    cpu_limit DECIMAL(5,2) NOT NULL DEFAULT 0.50,
    memory_limit_mb INT UNSIGNED NOT NULL DEFAULT 512,
    pids_limit INT UNSIGNED NOT NULL DEFAULT 128,
    network_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    sandbox_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_sandboxes PRIMARY KEY (sandbox_id),
    CONSTRAINT fk_sandboxes_workspace
        FOREIGN KEY (workspace_id) REFERENCES workspaces(workspace_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_sandboxes_node
        FOREIGN KEY (node_id) REFERENCES runtime_nodes(node_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_sandboxes_creator
        FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT uq_sandboxes_node_runtime
        UNIQUE (node_id, runtime_ref),
    CONSTRAINT chk_sandboxes_cpu CHECK (cpu_limit > 0),
    CONSTRAINT chk_sandboxes_memory CHECK (memory_limit_mb > 0),
    CONSTRAINT chk_sandboxes_pids CHECK (pids_limit > 0),
    CONSTRAINT chk_sandboxes_status
        CHECK (sandbox_status IN (
            'pending', 'running', 'stopped', 'failed', 'deleting'
        )),
    INDEX idx_sandboxes_workspace (workspace_id),
    INDEX idx_sandboxes_node_status (node_id, sandbox_status),
    INDEX idx_sandboxes_creator (created_by_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. SANDBOX_SESSIONS: phiên sử dụng terminal
CREATE TABLE sandbox_sessions (
    session_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    sandbox_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    session_status VARCHAR(20) NOT NULL DEFAULT 'active',
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME NULL,

    CONSTRAINT pk_sandbox_sessions PRIMARY KEY (session_id),
    CONSTRAINT fk_sandbox_sessions_sandbox
        FOREIGN KEY (sandbox_id) REFERENCES sandboxes(sandbox_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_sandbox_sessions_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT chk_sandbox_sessions_status
        CHECK (session_status IN ('active', 'closed', 'failed')),
    CONSTRAINT chk_sandbox_sessions_time
        CHECK (ended_at IS NULL OR ended_at >= started_at),
    INDEX idx_sandbox_sessions_sandbox (sandbox_id),
    INDEX idx_sandbox_sessions_user_status (user_id, session_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. AUDIT_LOGS: nhật ký sự kiện, không lưu bí mật hoặc mật khẩu
CREATE TABLE audit_logs (
    log_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NULL,
    project_id BIGINT UNSIGNED NULL,
    sandbox_id BIGINT UNSIGNED NULL,
    action_name VARCHAR(100) NOT NULL,
    result_status VARCHAR(20) NOT NULL,
    details TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_audit_logs PRIMARY KEY (log_id),
    CONSTRAINT fk_audit_logs_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_audit_logs_project
        FOREIGN KEY (project_id) REFERENCES projects(project_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_audit_logs_sandbox
        FOREIGN KEY (sandbox_id) REFERENCES sandboxes(sandbox_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT chk_audit_logs_result
        CHECK (result_status IN ('success', 'failure', 'denied')),
    INDEX idx_audit_logs_user_time (user_id, created_at),
    INDEX idx_audit_logs_project_time (project_id, created_at),
    INDEX idx_audit_logs_sandbox_time (sandbox_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. AI_JOBS: theo dõi tác vụ AI
CREATE TABLE ai_jobs (
    job_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    project_id BIGINT UNSIGNED NOT NULL,
    workspace_id BIGINT UNSIGNED NULL,
    job_type VARCHAR(50) NOT NULL,
    job_status VARCHAR(20) NOT NULL DEFAULT 'queued',
    input_summary TEXT NULL,
    result_summary TEXT NULL,
    error_message TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME NULL,
    finished_at DATETIME NULL,

    CONSTRAINT pk_ai_jobs PRIMARY KEY (job_id),
    CONSTRAINT fk_ai_jobs_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_ai_jobs_project
        FOREIGN KEY (project_id) REFERENCES projects(project_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_ai_jobs_workspace
        FOREIGN KEY (workspace_id) REFERENCES workspaces(workspace_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT chk_ai_jobs_status
        CHECK (job_status IN (
            'queued', 'running', 'completed', 'failed', 'cancelled'
        )),
    INDEX idx_ai_jobs_user_created (user_id, created_at),
    INDEX idx_ai_jobs_project_status (project_id, job_status),
    INDEX idx_ai_jobs_workspace (workspace_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
