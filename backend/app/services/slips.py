"""PDF salary slip — WeasyPrint (HTML/CSS → PDF), ticket 09 + ticket 10 layout.

One slip per fully-closed month. Internal record, not a CFDI. Per-source
sections: fixed salary (foreign → MXN at the settlement's derived rate),
per-project commission breakdown, gross total → MXN, bank fee (conv % +
fixed fees), bank-net (typed), tax, net-after-tax. Totals across sources at
the foot, per-source derived rates listed.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


def _fmt_mxn(value) -> str:
    if value is None:
        return "—"
    return f"$ {value:,.2f} MXN"


def _fmt_foreign(value, currency) -> str:
    if value is None:
        return "—"
    return f"{value:,.2f} {currency}"


def build_slip_data(month: str, user: dict, bank: dict, sections: list[dict], generated: str) -> dict:
    totals = {"netAfterTax": sum(s["netAfterTax"] for s in sections if s["netAfterTax"] is not None)}
    year, month_num = (int(p) for p in month.split("-"))
    month_label = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][month_num - 1]
    return {
        "appName": "Salary Tracker",
        "monthLabel": f"{month_label} {year}",
        "userName": user["displayName"],
        "userEmail": user["email"],
        "generated": generated,
        "sections": sections,
        "totals": totals,
        "bank": bank,
        "note": "Internal record — not a fiscal document. CFDI is generated manually in the SAT platform.",
    }


def render_pdf(slip_data: dict) -> bytes:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("slip.html")
    html = template.render(data=slip_data, fmt_mxn=_fmt_mxn, fmt_foreign=_fmt_foreign)
    return HTML(string=html).write_pdf()
