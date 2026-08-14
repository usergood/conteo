# 09 - Research PDF generation for salary slips

Type: research
Status: resolved
Blocked by:

## Question

Which PDF library fits the stack for generating the monthly salary slip (the SAT-friendly PDF)?

Constraints:

- Stack: Python FastAPI backend, Next.js/React frontend, Docker, SQLite.
- The slip: a clean single-page document with per-project commission breakdown, fixed salary, gross USD (or source currency), conversion + bank fees, tax before/after, net MXN.
- Should render well from server-side data (not client-side); support a reliable headless path in Docker (fonts, no Chrome dependency if avoidable).
- Human-readable maintenance (the slip layout will be iterated by hand later).

## Notes / context

- This is AFK: resolve with a `/research` subagent.
- Compare ReportLab, WeasyPrint, and any current alternative for this stack.
- Findings land on a throwaway `research/` branch with a context pointer from this ticket.

## Answer

**Recommended: WeasyPrint + Jinja2** (HTML/CSS templates). Pure-Python, server-side, no browser dependency; renders headlessly in Docker with just the Pango stack + `fonts-dejavu-core`. Keeps the slip as human-editable HTML/CSS that can be previewed in a browser before rendering — ideal for hand-iterating the layout. Actively maintained (v69.0, June 2026). ReportLab is the runner-up (zero system deps) but Python-code layout is worse to iterate. Note: Mexico's peso renders as `$` + `MXN` (₱ U+20B1 is the Philippine peso); one DejaVu/Noto fonts package covers all glyphs.

Full comparison + Docker font notes in `research/09-pdf-lib.md`.