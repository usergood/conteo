"""Closed months — mine and shared (ticket 06, prototype "Closed months" screen)."""

import sqlite3
from fastapi import APIRouter, Depends

from ..auth import get_db_conn, require_user
from ..services.hydrate import _months_mine, _months_shared

router = APIRouter(prefix="/api/months", tags=["months"])


@router.get("/mine")
def months_mine(conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)):
    return _months_mine(conn, user.sub)


@router.get("/shared")
def months_shared(conn: sqlite3.Connection = Depends(get_db_conn), user=Depends(require_user)):
    return _months_shared(conn, user.sub)
