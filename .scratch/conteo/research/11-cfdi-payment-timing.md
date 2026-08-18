# CFDI 4.0 issuance timing vs. payment receipt — RESICO contractor, USD client

**Date:** 2026-08-18. Legal texts verified against the SAT "Portal de trámites y servicios" article pages fetched this date (CFF, LISR, LIVA) and the Resolución Miscelánea Fiscal **2026** (published DOF 28-12-2025, vigente 01-01-2026) via the APTA mirror; FX/TipoCambio rules taken from the prior verified research in `10-banxico-rate.md`. Anything that could not be verified against a source actually fetched is flagged **UNVERIFIED**.

## Recommendation

**Invoice month M in USD → payment lands in month M+1 is legal.** Do it as **PPD** (CFDI for the total value issued "en el momento en que ésta se realice" — at service completion), FormaPago **99** "Por definir", and emit the **Complemento para recepción de Pagos** when the payment arrives — no later than the **5th natural day of the month following the payment month** (RMF 2026 rule 2.7.1.32). For RESICO, that income is declared in the month it is **efectivamente cobrado** (the month the money actually lands), per LISR art. 113-E (monthly) and 113-F (annual). IVA on services accrues when the consideration is **efectivamente cobrada** (LIVA art. 17), and services fully used abroad by a foreign resident without a Mexican PE are exported at **0%** (LIVA art. 29).

**PUE is only valid if the full payment arrives by the last day of the same calendar month in which the CFDI is issued** (RMF 2026 rule 2.7.1.39). So the M/M+1 split **cannot** be PUE — it must be PPD + complemento. The user's belief that "you cannot invoice before the money arrives" is **incorrect**: invoicing before receipt is the exact scenario CFF 29-A fr. VII b) and rules 2.7.1.29/2.7.1.32 are built for.

**Option B's "same fiscal month as the deposit" constraint is a *consequence*, not a standalone rule:** it keeps the RESICO cash-basis month (collection month) aligned with the CFDI's income month. With PUE it is strictly required (payment must land in the same calendar month as issuance, RMF 2.7.1.39 III); with PPD it is only about avoiding a mismatch between the SAT-preloaded income month and the bank statement.

## Answers to the seven questions

**Q1. When must the service CFDI be issued — and is there a "5th day of the following month" grace?**
No general grace for the *income* CFDI. For deferred/split payment, the CFDI for the total value is issued **"en el momento en que ésta se realice"** (when the operation/transaction is realized) — CFF 29-A fr. VII b). The "5th natural day of the month following the payment month" deadline applies to the **complemento de pago** (RMF 2026 2.7.1.32, last paragraph), i.e. the payment receipt, not the income invoice.

**Q2. Is RESICO income cash-based?**
Yes. LISR 113-E (monthly, by day 17 of the following month) and 113-F (annual, April) are both computed on "el total de los ingresos que perciban … y estén amparados por los comprobantes fiscales digitales por Internet **efectivamente cobrados**, sin incluir el impuesto al valor agregado, y sin aplicar deducción alguna." Same cash-basis principle in LISR art. 102 for PF business/professional activities ("los ingresos se consideran acumulables en el momento en que sean efectivamente percibidos").

**Q3. Is invoicing before the money arrives legal?**
Yes. CFF 29-A fr. VII b) explicitly contemplates it: "…se emitirá un comprobante fiscal digital por Internet por el valor total de la operación en el momento en que ésta se realice y se expedirá un comprobante fiscal digital por Internet por cada uno del resto de los pagos que se reciban…" RMF 2026 2.7.1.29 fr. II allows FormaPago 99 "Por definir" when the payment has not been received, provided the complemento de pago is issued once the payment arrives (per 2.7.1.32).

**Q4. PUE vs PPD + complemento de pago?**
- **PUE** ("Pago en una sola exhibición"): valid only when the consideration is paid in one exhibition **at issuance** (CFF 29-A fr. VII a)) **or** — the RMF 2.7.1.39 facility — when the total is **actually received by the last day of the same calendar month** the CFDI was issued, with PUE stated on the CFDI and the form of payment specified. If not paid by month-end: cancel the CFDI, reissue with FormaPago 99 + PPD related as "Sustitución de los CFDI previos" (tipoRelación 04), and emit complemento de pago (2.7.1.29, 2.7.1.32).
- **PPD** ("Pago en parcialidades o diferido") + **Complemento para recepción de Pagos**: income CFDI for the total at operation time (MetodoPago PPD, FormaPago 99); per payment received, a CFDI with `Total=0`, no MetodoPago/FormaPago, carrying the complemento; deadline = 5th natural day of the month following the payment month; one complemento per payment or one per month per receptor (RMF 2026 2.7.1.32).
- **Services nuance (CFF 29-A fr. VII a), last paragraph):** "Tratándose de contribuyentes que presten servicios personales, cada pago que perciban por la prestación de servicios se considerará como una sola exhibición y no como una parcialidad." For a service provider, each payment received is a single exhibition — i.e. the invoice raised on the exact payment (Option B) is naturally PUE.

**Q5. TipoCambio date?**
From `10-banxico-rate.md` (verified): the SAT CFDI 4.0 schema requires the **FIX** rate; the Anexo 20 validation band is ±35% of "el valor que se publica para la fecha de la operación"; CFF art. 20 uses the DOF-published rate of the day before the tax is caused, falling back to the last published rate on non-publishing days. For a service CFDI the "fecha de la operación" is the issuance/operation date (month M). **The complemento de pago carries its own payment-node rate (FechaPago / TipoCambioP / MonedaP)** — the exact complemento fill rules are the main **UNVERIFIED** item in this file (see below). Practical consequence: the MXN total on the month-M invoice (FIX of M) can differ from the MXN actually deposited when the USD is converted at M+1 — this is precisely the gap Option B is designed to avoid.

**Q6. Is "same fiscal month as the deposit" a hard legal constraint for Option B?**
It is the natural consequence of the rules above: with **PUE** the payment must land in the same calendar month as issuance (RMF 2.7.1.39 III), so invoicing the exact deposit in a different month than the deposit would be invalid as PUE and would have to be restructured as PPD + complemento. Under RESICO cash-basis, income is declared in the collection month regardless of invoice date, so an invoice dated in a different month than the collection creates a mismatch between SAT-preloaded income and the bank statement. The app's same-month constraint is sound **for PUE**; if ever relaxed, the alternative is PPD + complemento in the collection month.

**Q7. Is "you cannot invoice before the money arrives" a rule?**
No. It is a misreading of RESICO's cash basis. The law *requires* invoicing at operation time even when payment is deferred (CFF 29-A fr. VII b)), and defers tax recognition to collection (LISR 113-E, LIVA 17). What is *not* allowed is marking an unpaid invoice as **PUE** and letting the month end — that must be corrected to PPD by month-end (RMF 2.7.1.39).

## Comparison

| Aspect | Option A (USD-direct, invoice month M, payment M+1) | Option B (invoice exact MXN bank-net deposit, same month) |
| --- | --- | --- |
| Income CFDI | Total in USD, month M, **MetodoPago PPD**, FormaPago 99, at service completion (CFF 29-A VII b), FIX of M | Invoice at/after deposit, **PUE** (payment received), FIX of deposit date |
| Payment receipt | Complemento de pago within 5th natural day of month following the payment month (RMF 2.7.1.32) | None needed (PUE paid at issuance) |
| RESICO income month | Month the deposit lands (M+1) — LISR 113-E "efectivamente cobrados" | Month of deposit |
| IVA | 0% export if service fully used abroad by foreign resident w/o PE (LIVA 29); accrues on collection anyway (LIVA 17) | Same |
| FX risk | Two FIX values (invoice M, payment M+1) — MXN totals can differ from deposit; complemento records payment at its own rate | No split; invoice = deposit in MXN |
| App complexity | Higher (two-stage CFDI + complemento + relation + FX reconciliation) | Lower (single CFDI) |

## Key facts (all text verified against fetched pages)

1. **CFF 29-A fr. VII a)** — PUE: "Cuando la contraprestación se pague en una sola exhibición, en el momento en que se expida el comprobante… se señalará expresamente dicha situación…". Last paragraph: "…cada pago que perciban por la prestación de servicios se considerará como una sola exhibición y no como una parcialidad."
2. **CFF 29-A fr. VII b)** — deferred/split: CFDI total "en el momento en que ésta se realice" + CFDI per each later payment, referencing the total's folio.
3. **RMF 2026 2.7.1.29 fr. II** — FormaPago 99 "Por definir" when payment not yet received, conditional on later complemento de pago per 2.7.1.32; not applicable when paid in one exhibition at/before issuance.
4. **RMF 2026 2.7.1.32** — PPD mechanics: income CFDI for total at operation time; per payment a CFDI with Total=0, no MetodoPago/FormaPago, with "Complemento para recepción de Pagos"; one complemento per payment or per month per receptor; **deadline: "a más tardar al quinto día natural del mes inmediato siguiente al que corresponda el o los pagos recibidos."**
5. **RMF 2026 2.7.1.39** — PUE facility: (I) payment pactado/estimado by last day of the month of issuance; (II) PUE + forma de pago on the CFDI; (III) total actually received by that day. Otherwise cancel → reissue FormaPago 99 + PPD related as "Sustitución de los CFDI previos" → complemento de pago. Financial-sector exception: day 17 of the following month (not applicable here).
6. **LISR 113-E** (RESICO monthly) — payment by day 17 of following month on "ingresos … amparados por los CFDI **efectivamente cobrados**, sin incluir el IVA, sin deducciones"; 3.5M pesos annual cap; table 1.00%–2.50%.
7. **LISR 113-F** (RESICO annual) — April declaration on the same "efectivamente cobrados" basis; monthly ISR paid is credited.
8. **LISR 102** — PF business/professional income accumulates "en el momento en que sean efectivamente percibidos"; receipt = cash, goods, services, anticipos, deposits; cheques at cobro; extinction of obligations; (goods) exports accumulate on collection or after 12 months.
9. **LIVA 1-B** — "efectivamente cobradas" definition (cash/goods/services, anticipos, deposits; cheques at cobro; credit instruments presumed a guarantee; cards/vales when received/accepted).
10. **LIVA 17** — services: "el impuesto se causa en el momento en que se cobren efectivamente las contraprestaciones y sobre el monto de cada una de ellas"; partial collections taxed proportionally.
11. **LIVA 29** — 0% export; last paragraph: applies to "los residentes en el país que presten servicios personales independientes que sean aprovechados en su totalidad en el extranjero por residentes en el extranjero sin establecimiento en el país."
12. **RMF 2026** was published in the DOF on 28-12-2025, vigente from 01-01-2026 (APTA mirror header); rule 2.7.1.32 currently reads **5** days (a 2026 reduction from the prior 10 — secondary blogs confirm the change; primary RMF 2025 text not compared directly, see UNVERIFIED).

## Verified URLs (checked 2026-08-18)

Fetched directly (primary unless noted):
- `https://wwwmat.sat.gob.mx/articulo/99662/articulo-29-a` — CFF **29-A** full text (fr. VII a/b/c, penultimate "residentes en el extranjero" paragraph)
- `https://wwwmat.sat.gob.mx/articulo/86201/articulo-29` — CFF **29** (first paragraphs + fr. I) [fetched in the prior session]
- `https://wwwmatnp.sat.gob.mx/articulo/58872/articulo-113-f` — LISR **113-F** (annual declaration, "efectivamente cobrados")
- `https://wwwmatnp.sat.gob.mx/articulo/58780/articulo-113-e` — LISR **113-E** (RESICO eligibility, monthly payments day 17, cash basis, 3.5M cap, tasas)
- `https://wwwmat.sat.gob.mx/articulo/75346/articulo-102` — LISR **102** (cash basis, "efectivamente percibidos", export 12-month rule)
- `https://wwwmatnp.sat.gob.mx/articulo/29289/articulo-17` — LIVA **17** (services IVA accrues on "cobren efectivamente"; partial collections)
- `https://wwwmat.sat.gob.mx/articulo/68429/regla-2.7.1.29` — SAT portal **RMF rule 2.7.1.29** (FormaPago 99, complemento condition; page URL slug says 2.7.1.32 but returns 2.7.1.29)
- `http://www.apta.com.mx/aptace/reglasfis/regla.php?regla=2.7.1.32` — **RMF 2026 rule 2.7.1.32** full text (mirror; header confirms RMF 2026, DOF 28-12-2025)
- `http://www.apta.com.mx/aptace/reglasfis/regla.php?regla=2.7.1.39` — **RMF 2026 rule 2.7.1.39** full text (mirror; the PUE facility)
- `https://leyes-mx.com/codigo_fiscal_de_la_federacion/29-A.htm` — CFF 29-A (mirror, cross-check; last update 10/08/2026)
- `https://leyesmx.com/lisr/articulo/102/` — LISR 102 (mirror, cross-check)

Verified via search-result excerpts of these primary SAT pages (not fetched in full this session):
- `https://wwwmat.sat.gob.mx/articulo/80321/articulo-29` — LIVA **29** (0% export; last paragraph services) — excerpt only
- `https://wwwmat.sat.gob.mx/articulo/09020/articulo-1-b` — LIVA **1-B** ("efectivamente cobradas") — excerpt only

Secondary (interpretation/support, flagged):
- `https://resicocalc.com/blog/diferencia-pue-ppd-resico` — PUE/PPD under RESICO; confirms SAT preloads PUE as income of the invoice month, PPD income activates only on the complemento (REP); confirms 2026 = 5 days (was 10)
- `https://blog.mysuitemex.com/2022/02/09/lo-que-debes-saber-sobre-la-opcion-de-metodo-de-pago-pue-en-el-cfdi-con-pago-posterior` — correction workflow for unpaid-PUE (cancel + reissue PPD + complemento)
- `https://wwwmat.sat.gob.mx/ordenamiento/37585/ley-del-impuesto-al-valor-agregado` — LIVA index (art. 17 "Momento de pago del IVA por prestación de servicios") — excerpt only
- Prior session, `10-banxico-rate.md`: CFF art. 20, cfdv40.xsd TipoCambio=FIX, Anexo 20 ±35% band, Guía de llenado CFDI — re-used here

## UNVERIFIED / flagged

- **Complemento de pago field-level rules** (FechaPago, TipoCambioP, MonedaP, DoctoRelacionado/Parcialidad/ImpSaldoAnt/ImpPagado; how USD payments are recorded on the payment node) — not fetched this session; inferred from the complemento's existence and the PPD flow. Get the SAT "Guía de llenado del complemento para recepción de pagos" / Anexo 20 before implementing.
- **RMF 2025 vs 2026 change for 2.7.1.32 (10 → 5 days)**: the 5-day text is verified for RMF 2026 (APTA + resicocalc + todoconta); the prior 10-day wording was not compared directly against a fetched RMF 2025 primary text.
- **SAT portal pages for rules 2.7.1.32/2.7.1.39** could not be reached with correct content (the `/articulo/68429/regla-2.7.1.32` slug returns 2.7.1.29; `/articulo/62770/regla-2.7.1.39` returns 2.7.1.35) — RMF text relied on the APTA mirror (which reproduces the DOF-published RMF 2026, header verified).
- **LIVA 29 and LIVA 1-B** are relied on via search-excerpts of the SAT pages, not full-page fetches — text quoted matches the official wording but should be re-verified in the SAT portal before citation in deliverables.
- **"Fecha de la operación" for services** under the Anexo 20 ±35% band: file 10 established the FIX band applies to "la fecha de la operación"; for a service CFDI this is taken as the issuance/operation date, but no SAT primary doc explicitly equating the two for services was found.
- Whether the RESICO IVA monthly return treats the 0%-export month's income any differently (e.g., acreditamiento/devolución of input IVA) — LIVA 5-D mechanics referenced but not fetched.