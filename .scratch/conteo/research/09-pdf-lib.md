# 09 — Research: PDF library for the monthly salary slip

Resolves ticket [09-research-pdf-lib](../issues/09-research-pdf-lib.md). Pure research; no app code written.

## Recommendation

**Use WeasyPrint (v69, June 2026) with a Jinja2-rendered HTML/CSS template.** It is the only option that wins on all four constraints at once:

1. **Docker/headless**: a pure-Python library (no Chrome, no browser binary) that shells out to the Pango/HarfBuzz/fontconfig stack. In the FastAPI image this is two or three `apt` lines plus one fonts package. WeasyPrint's own docs publish the exact package lists, and there are maintained Docker images.
2. **Iterable-by-hand templates**: the slip is plain HTML + CSS, fed by a Jinja2 template. Editing the layout later = editing markup and CSS, which is what a person iterates fastest, and it can be previewed in any browser before rendering.
3. **Non-ASCII**: WeasyPrint resolves fonts via fontconfig/Pango and embeds them in the PDF automatically — `$`/`MXN`, `₱` (U+20B1) and accented Latin (`é`, `ü`) all render once a single DejaVu/Noto package is installed.
4. **Maintenance**: actively maintained by CourtBouillon/Kozea (BSD), v69.0 shipped 2026-06-02 as a security release; professional support is available.

ReportLab is the runner-up (zero system deps, faster, also actively maintained — 5.0.0 shipped 2026-06-18) but its layout lives in Python code (Platypus flowables), which is the wrong shape for "I will hand-iterate the slip layout later." fpdf2's HTML support is explicitly "basic" and not layout-grade. Typst is excellent typesetting but is a new markup language and an 23 MB native wheel, not HTML/CSS. xhtml2pdf is stale and has a long-standing non-Latin-1 failure. A headless-Chromium path (Playwright) is the only thing with better CSS fidelity but adds a ~150 MB browser binary for a static one-page slip — the exact dependency the constraints say to avoid if avoidable.

For this stack (FastAPI + Docker + single static page + human-maintained template), **WeasyPrint + Jinja2 is the winner**.

## Comparison table

| Library | Server-side? | Docker-friendly? | Template style | Deps weight | Maintained? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| **WeasyPrint** (recommended) | Yes — Python lib, `HTML(...).write_pdf()` | Yes. Needs Pango ≥1.44 + fonts in image (2–3 apt packages, no browser) | **HTML + CSS** via Jinja2 (hand-iterable, browser-previewable) | Medium: pure-Python wheel + system libs (Pango/HarfBuzz/fontconfig/Cairo legacy) | **Yes** — v69.0 Jun 2026, BSD, active security fixes (CVE-2026-49452) | No JS (irrelevant for static slip); fonts auto-embedded; CSS Paged Media for page control |
| **ReportLab (platypus)** | Yes — Python lib | Very — **no system deps** in core (`c`-less since 4.0) | **Python code** (Platypus flowables / canvas) — layout not markup | Low: 2 MB pure-Python wheel; optional pillow/pycairo extras | **Yes** — 5.0.0 Jun 2026, BSD | Unicode/UTF-8 default; embed TTF via `TTFont`. Best if you ever want zero apt deps; worst for hand-editing layout |
| **fpdf2** | Yes | Very — pure Python | Low-level drawing + optional "basic" HTML→PDF; tables | Low: Pillow, defusedxml, fontTools | **Yes** — 2.8.8, actively maintained, LGPL | Great lightweight/simple docs; HTML support explicitly basic — not for iterated layout |
| **Typst (`typst-py`)** | Yes — Rust compiler via Python binding | Yes — single native binary/wheel (23 MB) | **Typst markup language** (new syntax, not HTML/CSS) | Medium: 23 MB wheel, embedded fonts | **Yes** — very active (Typst 0.15, ~54k stars) | Professional typesetting; overkill for a single-page slip; requires learning Typst to edit the template |
| **Jinja2 + xhtml2pdf** | Yes | Yes | HTML/CSS (limited) | Medium | **No** — stale; own maintainers steer new work to WeasyPrint | Long-standing non-Latin-1/Unicode failures (open ~11 yrs); avoid |
| **wkhtmltopdf** | Yes (binary) | Yes | HTML/CSS | Medium (QtWebKit binary) | **No** — maintenance mode, engine frozen ~2016 | Modern CSS (flex/grid) unsupported; not for new work |
| **Playwright (headless Chromium)** | Yes | Yes but heavy | HTML/CSS (full browser) | **High**: ~150 MB browser binary | Yes | Best CSS/JS fidelity; the only real fidelity edge over WeasyPrint — unjustified here |

## Fonts in Docker (what's needed for clean MXN/peso rendering)

- WeasyPrint finds fonts through **fontconfig (via Pango)** and embeds them into the PDF automatically. The docs' troubleshooting is explicit: if no characters render, or you get squares/tofu, you forgot to install fonts. A working Debian-based FastAPI image adds:
  ```dockerfile
  RUN apt-get update && apt-get install -y --no-install-recommends \
      libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
      fonts-dejavu-core \
      && rm -rf /var/lib/apt/lists/*
  ```
  WeasyPrint v69 requires **Pango ≥ 1.44** and **Python ≥ 3.10**; modern Debian/Ubuntu (bookworm+) satisfies this. (`fonts-noto-core` is an equivalent, broader alternative.)
- **The peso itself**: Mexico's peso uses the plain dollar sign `$` (U+0024, always available), conventionally paired with the `MXN` code — SAT/CFDI-style slips render amounts as `$1,234.56 MXN`. The Unicode **Peso sign `₱` (U+20B1) is the Philippine peso**, not Mexican. Even so, DejaVu Sans covers the whole Currency Symbols block (incl. U+20B1) and all Latin accents (`é`, `ü`), so `fonts-dejavu-core` alone covers every glyph the slip can need and it embeds correctly.
- For **ReportLab** (if ever used instead): register a TTF explicitly — `registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))` (same Debian package). Built-in Helvetica only carries Latin-1, which already covers `$`, `é`, `ü`; the TTF guarantees consistent metrics and full coverage.
- Sanity checks in the container: `fc-list` to see installed fonts, `fc-match sans-serif` to see what a `font-family: sans-serif` will resolve to.

## Sources (URLs verified 2026-08)

- WeasyPrint "First Steps" (v69) — install deps, Pango ≥ 1.44, Python ≥ 3.10, Docker note, missing-fonts troubleshooting, Python API: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html
- WeasyPrint releases — v69.0 2026-06-02 (security, CVE-2026-49452), v68.x 2026-01/02: https://github.com/Kozea/WeasyPrint/releases
- WeasyPrint man page — fonts resolved via Pango/fontconfig, `fc-list`/`fc-match`, fonts embedded in PDF: https://manpages.ubuntu.com/manpages/jammy/man1/weasyprint.1.html
- ReportLab on PyPI — 5.0.0 2026-06-18, BSD, pure-Python wheel, release history: https://pypi.org/project/reportlab/
- ReportLab User Guide, Ch. 3 "Fonts" — Unicode/UTF-8 default input, `TTFont` TrueType embedding, Latin-1 for standard fonts: https://docs.reportlab.com/reportlab/userguide/ch3_fonts/
- fpdf2 on PyPI — 2.8.8, actively maintained, pure Python, Unicode TTF subsetting, "basic" HTML→PDF: https://pypi.org/project/fpdf2/
- `typst-py` on PyPI — Python binding, native wheels: https://pypi.org/project/typst/
- Self-hosted PDF comparison (WeasyPrint vs wkhtmltopdf vs Typst vs Paged.js, 2026) — stars, maintenance status, deployment models, `ghcr.io/kozea/weasyprint` image: https://www.pistack.xyz/posts/2026-06-25-self-hosted-pdf-document-generation-weasyprint-wkhtmltopdf-typst-pagedjs
- xhtml2pdf maintenance roadmap (#317) — contributor calls project stale, recommends WeasyPrint for new work: https://github.com/xhtml2pdf/xhtml2pdf/issues/317
- xhtml2pdf non-Latin-1 failure + upstream README pointing to WeasyPrint (SasView migration issue): https://github.com/SasView/sasview/issues/2034
- Example Dockerfile with WeasyPrint apt deps incl. `fonts-dejavu-core` (avoids blank PDFs): https://github.com/HKUDS/Vibe-Trading/blob/main/Dockerfile
- DejaVu Sans coverage of Currency Symbols block incl. PESO SIGN U+20B1: https://www.fileformat.info/info/unicode/font/dejavu_sans_condensed_bold/blockview.htm?block=currency_symbols
- ₱ U+20B1 is the Philippine peso sign; Latin-American pesos use `$` (Mexican peso sign article): https://en.wikipedia.org/wiki/Philippine_peso_sign
- Playwright headless browser ~150 MB, vs pure-Python alternatives (Nutrient guide): https://www.nutrient.io/blog/top-10-ways-to-generate-pdfs-in-python/