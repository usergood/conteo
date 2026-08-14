"""sqlite3.Row → JSON-ready dicts. Keys match the frontend types."""

import json

import sqlite3


def user_dict(row: sqlite3.Row) -> dict:
    return {
        "sub": row["sub"],
        "email": row["email"],
        "displayName": row["display_name"],
        "avatarUrl": row["avatar_url"],
        "language": row["language"],
        "guideStatus": row["guide_status"] if row["guide_status"] is not None else "pending",
    }


def bank_dict(row: sqlite3.Row) -> dict:
    return {
        "currency": row["currency"],
        "fixedFee": row["fixed_fee"],
        "convPct": row["conv_pct"],
        "taxPct": row["tax_pct"],
    }


def source_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "currency": row["currency"],
        "fixedSalary": row["fixed_salary"],
        "commissionMode": row["commission_mode"],
        "commissionValue": row["commission_value"],
        "active": bool(row["active"]),
    }


def project_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "sourceId": row["source_id"],
        "name": row["name"],
        "value": row["value"],
        "assigned": row["assigned"],
        "estEnd": row["est_end"],
        "approval": row["approval"],
        "settledMonth": row["settled_month"],
    }


def settlement_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "sourceId": row["source_id"],
        "month": row["month"],
        "typedMxn": row["typed_mxn"],
        "transfers": row["transfers"],
        "fixedSalaryForeign": row["fixed_salary_foreign"],
        "commissionForeign": row["commission_foreign"],
        "foreignPaid": row["foreign_paid"],
        "grossMxn": row["gross_mxn"],
        "derivedRate": row["derived_rate"],
        "tax": row["tax"],
        "netAfterTax": row["net_after_tax"],
        "paidProjectIds": json.loads(row["paid_project_ids"]),
        "commissionBreakdown": json.loads(row["commission_breakdown"]),
    }
