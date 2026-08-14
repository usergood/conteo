"""Read-only sharing — status ledger pending/active/dismissed/rejected (06).

Rows are never deleted (except with their source). Rejected shares vanish from
the receiver's list but persist for the owner. Re-grant re-activates the
existing row. Activation of pending shares happens silently at the invitee's
first sign-in (routers/auth). Mutations reject shared rows by requiring
ownership (this router) on every write.
"""

import secrets
import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from ..auth import get_db_conn, now_iso, require_user
from ..services.hydrate import _shares_by_me, _shares_with_me

router = APIRouter(prefix="/api/shares", tags=["shares"])


@router.get("")
def list_shares(conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)):
    return {"byMe": _shares_by_me(conn, user.sub), "withMe": _shares_with_me(conn, user.sub)}


class ShareBody(BaseModel):
    sourceId: str
    email: EmailStr


def _find_share(conn, share_id: str):
    row = conn.execute("SELECT * FROM shares WHERE id = ?", (share_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="share_not_found")
    return row


def _share_out(row) -> dict:
    return {
        "id": row["id"],
        "sourceId": row["source_id"],
        "status": row["status"],
        "email": row["pending_email"] or "",
        "updatedAt": row["updated_at"],
    }


@router.post("")
def create_share(body: ShareBody, conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)):
    source = conn.execute(
        "SELECT id FROM income_sources WHERE id = ? AND owner_user_id = ?", (body.sourceId, user.sub)
    ).fetchone()
    if source is None:
        raise HTTPException(status_code=404, detail="source_not_found")
    email = body.email.lower()
    sharee = conn.execute("SELECT sub FROM users WHERE LOWER(email) = ?", (email,)).fetchone()
    # One row per (owner, sharee, source): re-grant re-activates the existing row.
    existing = conn.execute(
        "SELECT * FROM shares WHERE owner_user_id = ? AND source_id = ? "
        "AND (LOWER(pending_email) = ? OR sharee_user_id = ?)",
        (user.sub, body.sourceId, email, sharee["sub"] if sharee else None),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE shares SET status = ?, sharee_user_id = ?, pending_email = ?, updated_at = ? WHERE id = ?",
            ("active" if sharee else "pending", sharee["sub"] if sharee else None, email, now_iso(), existing["id"]),
        )
        conn.commit()
        return _share_out(_find_share(conn, existing["id"]))
    share_id = "sh" + secrets.token_hex(8)
    conn.execute(
        "INSERT INTO shares (id, owner_user_id, sharee_user_id, pending_email, source_id, status, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (share_id, user.sub, sharee["sub"] if sharee else None, email, body.sourceId,
         "active" if sharee else "pending", now_iso(), now_iso()),
    )
    conn.commit()
    return _share_out(_find_share(conn, share_id))


@router.post("/{share_id}/revoke")
def revoke_share(share_id: str, conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)):
    share = _find_share(conn, share_id)
    if share["owner_user_id"] != user.sub:
        raise HTTPException(status_code=403, detail="not_owner")
    conn.execute("UPDATE shares SET status = 'rejected', updated_at = ? WHERE id = ?", (now_iso(), share_id))
    conn.commit()
    return _share_out(_find_share(conn, share_id))


@router.post("/{share_id}/dismiss")
def dismiss_share(share_id: str, conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)):
    share = _find_share(conn, share_id)
    if share["sharee_user_id"] != user.sub:
        raise HTTPException(status_code=403, detail="not_sharee")
    if share["status"] != "active":
        raise HTTPException(status_code=409, detail="only_active_can_dismiss")
    conn.execute("UPDATE shares SET status = 'dismissed', updated_at = ? WHERE id = ?", (now_iso(), share_id))
    conn.commit()
    return _share_out(_find_share(conn, share_id))


@router.post("/{share_id}/undismiss")
def undismiss_share(share_id: str, conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)):
    share = _find_share(conn, share_id)
    if share["sharee_user_id"] != user.sub:
        raise HTTPException(status_code=403, detail="not_sharee")
    if share["status"] != "dismissed":
        raise HTTPException(status_code=409, detail="only_dismissed_can_undismiss")
    conn.execute("UPDATE shares SET status = 'active', updated_at = ? WHERE id = ?", (now_iso(), share_id))
    conn.commit()
    return _share_out(_find_share(conn, share_id))