"""Income sources + projects (tickets 02, 03).

Currency is mutable forward-only — closed settlements keep their recorded
amounts because settlements store their own converted values. Delete is only
allowed when the source is completely empty (no projects, no settlements) and
cascade-deletes its shares (06). Mutations reject shared rows (06) — enforced
here by requiring owner_user_id = me on every write.
"""

import secrets
import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_db_conn, now_iso, require_onboarded, require_user
from ..serializers import project_dict, source_dict
from ..services.currencies import is_supported

router = APIRouter(prefix="/api", tags=["sources"])


def _get_owned_source(conn: sqlite3.Connection, source_id: str, user_id: str):
    row = conn.execute(
        "SELECT * FROM income_sources WHERE id = ? AND owner_user_id = ?", (source_id, user_id)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="source_not_found")
    return row


class SourceBody(BaseModel):
    name: str
    currency: str
    fixedSalary: float = 0
    commissionMode: str = "none"
    commissionValue: float = 0
    foreignClientId: str | None = None


@router.get("/sources")
def list_sources(conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)):
    rows = conn.execute(
        "SELECT * FROM income_sources WHERE owner_user_id = ? ORDER BY created_at", (user.sub,)
    ).fetchall()
    return [source_dict(r) for r in rows]


@router.post("/sources")
def create_source(
    body: SourceBody,
    conn: sqlite3.Connection = Depends(get_db_conn),
    bank=Depends(require_onboarded),
    user=Depends(require_user),
):
    if body.commissionMode not in ("none", "pct", "flat"):
        raise HTTPException(status_code=422, detail="invalid_commission_mode")
    if not body.name.strip() or not body.currency.strip():
        raise HTTPException(status_code=422, detail="name_and_currency_required")
    if not is_supported(body.currency):
        raise HTTPException(status_code=422, detail="unsupported_currency")
    source_id = "s" + secrets.token_hex(8)
    now = now_iso()
    conn.execute(
        "INSERT INTO income_sources (id, owner_user_id, foreign_client_id, name, currency, fixed_salary, commission_mode, "
        "commission_value, active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)",
        (source_id, user.sub, body.foreignClientId, body.name.strip(), body.currency.upper(), body.fixedSalary,
         body.commissionMode, body.commissionValue, now, now),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM income_sources WHERE id = ?", (source_id,)).fetchone()
    return source_dict(row)


@router.put("/sources/{source_id}")
def update_source(
    source_id: str, body: SourceBody, conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)
):
    _get_owned_source(conn, source_id, user.sub)
    if body.commissionMode not in ("none", "pct", "flat"):
        raise HTTPException(status_code=422, detail="invalid_commission_mode")
    if not is_supported(body.currency):
        raise HTTPException(status_code=422, detail="unsupported_currency")
    conn.execute(
        "UPDATE income_sources SET name = ?, currency = ?, fixed_salary = ?, commission_mode = ?, "
        "commission_value = ?, updated_at = ? WHERE id = ? AND owner_user_id = ?",
        (body.name.strip(), body.currency.upper(), body.fixedSalary, body.commissionMode,
         body.commissionValue, now_iso(), source_id, user.sub),
    )
    conn.commit()
    return source_dict(_get_owned_source(conn, source_id, user.sub))


@router.post("/sources/{source_id}/deactivate")
def deactivate_source(
    source_id: str, conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)
):
    _get_owned_source(conn, source_id, user.sub)
    conn.execute(
        "UPDATE income_sources SET active = 0, updated_at = ? WHERE id = ? AND owner_user_id = ?",
        (now_iso(), source_id, user.sub),
    )
    conn.commit()
    return source_dict(_get_owned_source(conn, source_id, user.sub))


@router.delete("/sources/{source_id}")
def delete_source(source_id: str, conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)):
    source = _get_owned_source(conn, source_id, user.sub)
    projects = conn.execute("SELECT COUNT(*) AS n FROM projects WHERE source_id = ?", (source_id,)).fetchone()["n"]
    settlements = conn.execute(
        "SELECT COUNT(*) AS n FROM settlements WHERE source_id = ?", (source_id,)
    ).fetchone()["n"]
    if projects or settlements:
        raise HTTPException(status_code=409, detail="source_not_empty")
    conn.execute("DELETE FROM shares WHERE source_id = ?", (source_id,))
    conn.execute("DELETE FROM income_sources WHERE id = ?", (source_id,))
    conn.commit()
    return {"ok": True, "name": source["name"]}


class ProjectBody(BaseModel):
    name: str
    value: float
    assigned: str
    estEnd: str
    approval: str | None = None


@router.get("/sources/{source_id}/projects")
def list_projects(source_id: str, conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)):
    _get_owned_source(conn, source_id, user.sub)
    rows = conn.execute(
        "SELECT * FROM projects WHERE source_id = ? AND owner_user_id = ? ORDER BY created_at",
        (source_id, user.sub),
    ).fetchall()
    return [project_dict(r) for r in rows]


@router.post("/sources/{source_id}/projects")
def create_project(
    source_id: str, body: ProjectBody, conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)
):
    _get_owned_source(conn, source_id, user.sub)
    project_id = "p" + secrets.token_hex(8)
    conn.execute(
        "INSERT INTO projects (id, source_id, owner_user_id, name, value, assigned, est_end, approval, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (project_id, source_id, user.sub, body.name.strip(), body.value, body.assigned, body.estEnd,
         body.approval, now_iso()),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    return project_dict(row)


def _get_owned_project(conn: sqlite3.Connection, project_id: str, user_id: str):
    row = conn.execute(
        "SELECT * FROM projects WHERE id = ? AND owner_user_id = ?", (project_id, user_id)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="project_not_found")
    return row


@router.put("/projects/{project_id}")
def update_project(
    project_id: str, body: ProjectBody, conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)
):
    _get_owned_project(conn, project_id, user.sub)
    conn.execute(
        "UPDATE projects SET name = ?, value = ?, assigned = ?, est_end = ?, approval = ? WHERE id = ?",
        (body.name.strip(), body.value, body.assigned, body.estEnd, body.approval, project_id),
    )
    conn.commit()
    return project_dict(_get_owned_project(conn, project_id, user.sub))


@router.delete("/projects/{project_id}")
def delete_project(project_id: str, conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)):
    project = _get_owned_project(conn, project_id, user.sub)
    if project["settled_month"]:
        raise HTTPException(status_code=409, detail="project_settled")
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    return {"ok": True}