"""End-to-end scenario test: the whole application from specification.

Walks the complete happy path through the HTTP boundary — sign-in, setup
guide, bank settings, income source, project (approved), forecast, month
close, closed months, and the salary slip PDF. This is the "tests the whole
docker container" scenario: every screen the spec describes, one journey.
"""

import pytest
def test_full_scenario(client, app, seed_fx, login, onboard):
    seed_fx({"USD": 1, "MXN": 17.06})

    # 1. Sign in (dev mode). New user: guide pending, no bank.
    login()
    me = client.get("/api/auth/me").json()
    assert me["user"]["guideStatus"] == "pending"
    assert me["bank"] is None
    assert me["sources"] == []

    # 2. First-time setup: bank settings (guide step 1).
    onboard()
    assert client.get("/api/auth/me").json()["bank"]["fixedFee"] == 320

    # 3. Income source (guide step 2).
    sid = client.post("/api/sources", json={
        "name": "US company", "currency": "USD",
        "fixedSalary": 5000, "commissionMode": "pct", "commissionValue": 10,
    }).json()["id"]
    assert client.get("/api/sources").json()[0]["currency"] == "USD"

    # 4. Project, approved in the month we will close (guide step 3).
    pid = client.post(f"/api/sources/{sid}/projects", json={
        "name": "Website redesign", "value": 8000, "assigned": "2026-08-01",
        "estEnd": "2026-08-20", "approval": "2026-08-05",
    }).json()["id"]

    # 5. Finish the guide.
    assert client.put("/api/settings/guide-status", json={"guideStatus": "done"}).json()["guideStatus"] == "done"

    # 6. Forecast: the approved project lands this month; gross in USD + MXN.
    first = client.get("/api/forecast?window=3").json()["months"][0]
    row = first["rows"][0]
    assert row["grossForeign"] == pytest.approx(5800)  # 5000 fixed + 800 comm (10% of 8000)
    assert row["grossMxn"] == pytest.approx(5800 * 17.06)
    assert first["totals"]["bankNet"] == pytest.approx(5800 * 17.06 * 0.97 - 320)

    # 7. Close the month. The approval is carried for the UI to pre-check it.
    close_view = client.get("/api/close?month=2026-08").json()
    project = close_view["sources"][0]["projects"][0]
    assert project["approval"] == "2026-08-05"
    st = client.post("/api/close", json={
        "month": "2026-08", "sourceId": sid, "typedMxn": 86500, "transfers": 1, "paidProjectIds": [pid],
    }).json()
    assert st["netAfterTax"] == pytest.approx(84770)

    # 8. Closed months: one row with gross-in-currency, bank-net and tax.
    months = client.get("/api/months/mine").json()
    assert len(months) == 1
    assert months[0]["grossByCurrency"]["USD"] == pytest.approx(5800)
    assert months[0]["bankNet"] == pytest.approx(86500)
    assert months[0]["tax"] == pytest.approx(1730)

    # 9. Salary slip PDF for the owner.
    slip = client.get("/api/months/2026-08/slip")
    assert slip.status_code == 200
    assert slip.headers["content-type"] == "application/pdf"
    assert slip.content[:5] == b"%PDF-"

    # 10. Hydrate reflects everything.
    final = client.get("/api/auth/me").json()
    assert len(final["settlements"]) == 1
    assert final["months"][0]["id"] == "2026-08"
