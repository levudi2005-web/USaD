
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from ...database import get_db
from ...api.v1.auth import get_current_user
from ...models import User

router = APIRouter(prefix="/projects", tags=["Projects"])


class ProjectCreate(BaseModel):
    project_name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=5000)


class ProjectUpdate(BaseModel):
    project_name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=5000)
    project_status: str | None = None


class WorkspaceCreate(BaseModel):
    workspace_name: str = Field(min_length=1, max_length=150)


def _get_project(db: Session, project_id: int, user_id: int):
    project = db.execute(
        text("""
            SELECT p.project_id, p.owner_user_id, p.project_name,
                   p.description, p.project_status, p.created_at, p.updated_at
            FROM projects p
            LEFT JOIN project_members pm
              ON pm.project_id = p.project_id AND pm.user_id = :user_id
            WHERE p.project_id = :project_id
              AND (p.owner_user_id = :user_id OR pm.user_id IS NOT NULL)
            LIMIT 1
        """),
        {"project_id": project_id, "user_id": user_id},
    ).mappings().first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy dự án hoặc bạn không có quyền truy cập",
        )

    return dict(project)


@router.get("")
def list_projects(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text("""
            SELECT DISTINCT p.project_id, p.owner_user_id, p.project_name,
                   p.description, p.project_status, p.created_at, p.updated_at
            FROM projects p
            LEFT JOIN project_members pm ON pm.project_id = p.project_id
            WHERE p.owner_user_id = :user_id OR pm.user_id = :user_id
            ORDER BY p.updated_at DESC
        """),
        {"user_id": user.user_id},
    ).mappings().all()

    return {"items": [dict(row) for row in rows]}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_project(
    data: ProjectCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    name = data.project_name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Tên dự án không được để trống")

    try:
        result = db.execute(
            text("""
                INSERT INTO projects
                    (owner_user_id, project_name, description, project_status)
                VALUES
                    (:owner_user_id, :project_name, :description, 'active')
            """),
            {
                "owner_user_id": user.user_id,
                "project_name": name,
                "description": data.description,
            },
        )
        project_id = result.lastrowid

        db.execute(
            text("""
                INSERT INTO project_members (project_id, user_id, member_role)
                VALUES (:project_id, :user_id, 'owner')
            """),
            {"project_id": project_id, "user_id": user.user_id},
        )
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Không thể tạo dự án")

    return _get_project(db, project_id, user.user_id)


@router.get("/{project_id}")
def get_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_project(db, project_id, user.user_id)


@router.patch("/{project_id}")
def update_project(
    project_id: int,
    data: ProjectUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _get_project(db, project_id, user.user_id)

    if project["owner_user_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Chỉ chủ dự án mới được chỉnh sửa")

    updates = data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Không có thông tin cần cập nhật")

    if "project_name" in updates:
        if updates["project_name"] is None or not updates["project_name"].strip():
            raise HTTPException(status_code=422, detail="Tên dự án không được để trống")
        updates["project_name"] = updates["project_name"].strip()

    if "project_status" in updates:
        if updates["project_status"] not in {"active", "archived", "disabled"}:
            raise HTTPException(status_code=422, detail="Trạng thái dự án không hợp lệ")

    fields = []
    params = {"project_id": project_id}

    for key, value in updates.items():
        fields.append(f"{key} = :{key}")
        params[key] = value

    try:
        db.execute(
            text(f"UPDATE projects SET {', '.join(fields)} WHERE project_id = :project_id"),
            params,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Không thể cập nhật dự án")

    return _get_project(db, project_id, user.user_id)


@router.get("/{project_id}/workspaces")
def list_workspaces(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_project(db, project_id, user.user_id)

    rows = db.execute(
        text("""
            SELECT workspace_id, project_id, workspace_name,
                   storage_path, workspace_status, created_at, updated_at
            FROM workspaces
            WHERE project_id = :project_id
            ORDER BY workspace_id DESC
        """),
        {"project_id": project_id},
    ).mappings().all()

    return {"items": [dict(row) for row in rows]}


@router.post("/{project_id}/workspaces", status_code=status.HTTP_201_CREATED)
def create_workspace(
    project_id: int,
    data: WorkspaceCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _get_project(db, project_id, user.user_id)

    if project["owner_user_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Chỉ chủ dự án mới được tạo workspace")

    workspace_name = data.workspace_name.strip()
    if not workspace_name:
        raise HTTPException(status_code=422, detail="Tên workspace không được để trống")

    # Workspace path is metadata only; this endpoint does not create host files.
    storage_path = f"projects/{project_id}/workspaces/{workspace_name}"

    try:
        result = db.execute(
            text("""
                INSERT INTO workspaces
                    (project_id, workspace_name, storage_path, workspace_status)
                VALUES
                    (:project_id, :workspace_name, :storage_path, 'active')
            """),
            {
                "project_id": project_id,
                "workspace_name": workspace_name,
                "storage_path": storage_path,
            },
        )
        workspace_id = result.lastrowid
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Không thể tạo workspace; tên có thể đã tồn tại",
        )

    row = db.execute(
        text("""
            SELECT workspace_id, project_id, workspace_name,
                   storage_path, workspace_status, created_at, updated_at
            FROM workspaces
            WHERE workspace_id = :workspace_id
        """),
        {"workspace_id": workspace_id},
    ).mappings().first()

    return dict(row)
