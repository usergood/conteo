"""Builds the full "me" payload the client hydrates from (ticket 05 / 06)."""

import json
import sqlite3

from . import fx
from ..serializers import bank_dict, project_dict, settlement_dict, source_dict, user_dict
from .months import fully_closed_months, owner_month_fully_closed


def _user_row(conn, user_id):
    return conn.execute("SELECT * FROM users WHERE sub = ?", (user_id,)).fetchone()


def _months_mine(conn, user_id):
    closed = fully_closed_months(conn, user_id)
    rows = []
    for month in closed:
        settlements = conn.execute(
            "SELECT s.net_after_tax, s.typed_mxn, s.tax, s.foreign_paid, src.name, src.currency "
            "FROM settlements s JOIN income_sources src ON src.id = s.source_id "
            "WHERE s.owner_user_id = ? AND s.month = ?",
            (user_id, month),
        ).fetchall()
        year, month_num = (int(p) for p in month.split("-"))
        gross: dict = {}
        for r in settlements:
            gross[r["currency"]] = gross.get(r["currency"], 0) + r["foreign_paid"]
        rows.append({
            "id": month,
            "year": year,
            "monthNum": month_num,
            "netTotal": round(sum(r["net_after_tax"] for r in settlements), 2),
            "sourceCount": len(settlements),
            "sources": [r["name"] for r in settlements],
            "grossByCurrency": {cur: round(v, 2) for cur, v in gross.items()},
            "bankNet": round(sum(r["typed_mxn"] for r in settlements), 2),
            "tax": round(sum(r["tax"] for r in settlements), 2),
        })
    return rows


def _months_shared(conn, user_id):
    shares = conn.execute(
        "SELECT sh.id, sh.source_id, sh.owner_user_id, src.name AS source_name, src.currency, u.email AS owner "
        "FROM shares sh "
        "JOIN income_sources src ON src.id = sh.source_id "
        "JOIN users u ON u.sub = sh.owner_user_id "
        "WHERE sh.sharee_user_id = ? AND sh.status = 'active'",
        (user_id,),
    ).fetchall()
    if not shares:
        return []
    owners = sorted({sh["owner_user_id"] for sh in shares})
    rows = []
    for owner_id in owners:
        owner_shares = [sh for sh in shares if sh["owner_user_id"] == owner_id]
        shared_source_ids = {sh["source_id"] for sh in owner_shares}
        settlements = conn.execute(
            "SELECT s.source_id, s.month, s.net_after_tax, s.foreign_paid, s.typed_mxn, s.tax, "
            "src.name AS source_name, src.currency "
            "FROM settlements s JOIN income_sources src ON src.id = s.source_id "
            "WHERE s.owner_user_id = ?",
            (owner_id,),
        ).fetchall()
        by_month: dict = {}
        for st in settlements:
            by_month.setdefault(st["month"], []).append(st)
        owner_email = owner_shares[0]["owner"]
        for month in sorted(by_month):
            if not owner_month_fully_closed(conn, owner_id, month):
                continue  # ticket 06: only closed months are shared
            month_settlements = by_month[month]
            if not all(st["source_id"] in shared_source_ids for st in month_settlements):
                continue  # sharee must cover every source contributing to this month
            for st in month_settlements:
                year, month_num = (int(p) for p in st["month"].split("-"))
                rows.append({
                    "id": f"{owner_shares[0]['id']}-{st['month']}",
                    "owner": owner_email,
                    "source": st["source_name"],
                    "currency": st["currency"],
                    "year": year,
                    "monthNum": month_num,
                    "netAfterTax": st["net_after_tax"],
                    "grossForeign": st["foreign_paid"],
                    "bankNet": st["typed_mxn"],
                    "tax": st["tax"],
                })
    rows.sort(key=lambda r: (r["year"], r["monthNum"]))
    return rows


def _shares_by_me(conn, user_id):
    rows = conn.execute(
        "SELECT sh.*, u.email AS sharee_email FROM shares sh "
        "LEFT JOIN users u ON u.sub = sh.sharee_user_id "
        "WHERE sh.owner_user_id = ? ORDER BY sh.updated_at DESC",
        (user_id,),
    ).fetchall()
    return [_share_json(r, r["sharee_email"] or r["pending_email"]) for r in rows]


def _shares_with_me(conn, user_id):
    rows = conn.execute(
        "SELECT sh.*, u.email AS sharee_email, src.name AS source_name, "
        "       owner.email AS owner_email "
        "FROM shares sh "
        "LEFT JOIN users u ON u.sub = sh.sharee_user_id "
        "JOIN income_sources src ON src.id = sh.source_id "
        "JOIN users owner ON owner.sub = sh.owner_user_id "
        "WHERE sh.sharee_user_id = ? AND sh.status != 'rejected' "
        "ORDER BY sh.updated_at DESC",
        (user_id,),
    ).fetchall()
    return [_share_json(r, r["owner_email"] or r["pending_email"]) for r in rows]


def _share_json(row, email):
    return {
        "id": row["id"],
        "sourceId": row["source_id"],
        "email": email,
        "status": row["status"],
        "updatedAt": row["updated_at"],
    }


def hydrate_payload(conn: sqlite3.Connection, user_id: str) -> dict:
    bank = conn.execute(
        "SELECT currency, fixed_fee, conv_pct, tax_pct FROM bank_settings WHERE owner_user_id = ?",
        (user_id,),
    ).fetchone()
    sources = conn.execute(
        "SELECT * FROM income_sources WHERE owner_user_id = ? ORDER BY created_at", (user_id,)
    ).fetchall()
    projects = conn.execute(
        "SELECT * FROM projects WHERE owner_user_id = ? ORDER BY created_at", (user_id,)
    ).fetchall()
    settlements = conn.execute(
        "SELECT * FROM settlements WHERE owner_user_id = ? ORDER BY month, created_at", (user_id,)
    ).fetchall()
    foreign_clients = conn.execute(
        "SELECT * FROM foreign_clients WHERE owner_user_id = ? ORDER BY created_at", (user_id,)
    ).fetchall()
    snapshot = fx.current_snapshot(conn)
    from ..serializers import fc_dict
    return {
        "user": user_dict(_user_row(conn, user_id)),
        "bank": bank_dict(bank) if bank else None,
        "sources": [source_dict(s) for s in sources],
        "projects": [project_dict(p) for p in projects],
        "settlements": [settlement_dict(s) for s in settlements],
        "sharesByMe": _shares_by_me(conn, user_id),
        "sharesWithMe": _shares_with_me(conn, user_id),
        "months": _months_mine(conn, user_id),
        "sharedMonths": _months_shared(conn, user_id),
        "fx": {
            "base": "USD",
            "rates": snapshot["rates"] if snapshot else {},
            "fetchedAt": snapshot["fetched_at"] if snapshot else None,
            "stale": bool(snapshot["stale"]) if snapshot else True,
        } if snapshot else None,
        "foreignClients": [fc_dict(r) for r in foreign_clients],
    }