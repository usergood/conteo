# Banxico SieAPIRest — official USD/MXN FIX rate for CFDI 4.0 "Option A"

**Date:** 2026-08-18. All API facts verified against `banxico.org.mx` primary docs fetched this date; legal texts verified against the current CFF (DOF 09-04-2026) and Ley Monetaria PDFs on `diputados.gob.mx`; CFDI requirements verified against the SAT CFDI 4.0 XSD and Anexo 20 fill guides. Anything that could not be verified against a source actually fetched is flagged **UNVERIFIED**.

## Recommendation

Use the **Banxico SieAPIRest** series **`SF43718`** — *"Tipo de cambio Pesos por dólar E.U.A. Tipo de cambio para solventar obligaciones denominadas en moneda extranjera Fecha de determinación (FIX)"* — for the official USD/MXN FIX rate. Endpoint:

```
GET https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF43718/datos/{fechaIni}/{fechaFin}
```

e.g. `…/series/SF43718/datos/2026-08-17/2026-08-18`, with `Accept: application/json` (default) and header `Bmx-Token: <64-char token>`. It returns the FIX per business day as `bmx → series → datos → [{fecha, dato}]`. This is the **only** rate the SAT's CFDI schema names for `TipoCambio` (the XSD says "tipo de cambio FIX"), so it is the correct source for Option A invoicing. This is a different thing from the ticket-08 forecast feed (open.er-api.com / Frankfurter): those are market reference rates for *forecasting*, not the official FIX, and must never be put on a CFDI. No authentication secret of note — the token is a free, one-time generated string — but the client **must** poll **at most once per business day after ~12:00 CDMX** and cache, because the FIX itself only changes once per bank business day (see Publishing time & freshness).

## Comparison

| Series / source | What it is | Published when | Use for CFDI? |
| --- | --- | --- | --- |
| **`SF43718`** — "Pesos por Dólar. FIX." (Fecha de determinación) | The FIX: daily reference rate determined by Banxico from wholesale interbank quotes | Determined every bank business day; announced **from 12:00 CDMX** (not 10:00) | **Yes — this is the "tipo de cambio FIX" the CFDI 4.0 schema requires.** Rate by *determination date*. |
| **`SF60653`** — "Pesos por Dólar. Fecha de liquidación" ("tipo de cambio para solventar obligaciones…") | The same FIX re-indexed to the date it *settles* obligations (operational name: "Para Pagos" / the DOF publication) | Value for day X = FIX determined 2 business days earlier; DOF publishes it on X−1 | Useful to cross-check the "DOF-published value for the operation date". Same underlying FIX number, shifted dates. |
| DOF daily publication ("Tipo de cambio para solventar obligaciones denominadas en moneda extranjera pagaderas en la República Mexicana") | The FIX printed in the DOF one business day after determination | Every bank business day (morning edition) | It *is* the FIX of the prior business day. Not a separate API series. |
| open.er-api.com / Frankfurter (ticket 08) | Blended market / central-bank reference rates, updated ~daily | Independent of Banxico | **No.** Not the FIX; SAT validates against Banxico's FIX. Keep strictly for forecasting. |

## Key facts

### 1. Endpoint & series ID

- API base: `https://www.banxico.org.mx/SieAPIRest/service/v1/`. All requests require a token (see §2). TLS **1.3** is required since 24-Mar-2023 (official press note linked from the landing page).
- Series **`SF43718`** = "Pesos por Dólar. FIX." Full official title returned by the API: *"Tipo de cambio Pesos por dólar E.U.A. Tipo de cambio para solventar obligaciones denominadas en moneda extranjera Fecha de determinación (FIX)"*. It **is** the FIX (fixing) rate, keyed to the determination date. Verified in three independent places: the SieAPIRest landing page's series list, the API docs' example payloads, and the SIE web-catalog metadata for SF43718.
- There is no separate "DOF-published" SieAPIRest series — the DOF publishes exactly the FIX, one bank business day after determination (see §4). A second series, **`SF60653`** "Pesos por Dólar. Fecha de liquidación", carries the same FIX re-indexed to settlement/liquidation dates (operationally the "Para Pagos" value). Verified live in the SIE web table on 2026-08-18: `SF43718[18/08/2026]=17.0638` and `SF60653[20/08/2026]=17.0638` — same number, two business days apart.
- Date-range endpoint: `GET /SieAPIRest/service/v1/series/:idSerie/datos/:fechaIni/:fechaFin`. Formats: **JSON (default), XML, HTML** — chosen via `Accept` header or `mediaType=json|xml|html`; language via `locale=es|en`. Up to **20 series** per request (comma list or `SF1-SF5` range).

### 2. Authentication

- **Yes, a token is mandatory** for every request: a 64-char alphanumeric string, obtained **free and once** at `https://www.banxico.org.mx/SieAPIRest/service/v1/token` via a web form (security image + security code = a simple captcha; no account, no registration, no payment mentioned). Reused indefinitely. The token-status page lets you check your token's current state.
- Send it as the HTTP header **`Bmx-Token: <token>`** *or* the query param **`token=<token>`** (header wins if both present).
- Rate limits are per token: **oportuna** (metadata + `datos/oportuno`): max **80 req / 1 min**, 40,000/day; **histórica** (`datos` + date-range): max **200 req / 5 min**, 10,000/day. Exceeding blocks the token for that category until the window ends (daily limit → blocked until end of the calendar day, CDMX time). The docs explicitly recommend **caching** rather than hammering the API.

### 3. Response format

JSON shape (exact, from the API docs):

```json
{
  "bmx": {
    "series": [
      {
        "idSerie": "SF43718",
        "titulo": "Tipo de cambio Pesos por dólar E.U.A. … Fecha de determinación (FIX)",
        "datos": [
          { "fecha": "18/08/2026", "dato": "17.0638" }
        ]
      }
    ]
  }
}
```

- Query dates in: `yyyy-MM-dd`. **Response `fecha` is `dd/MM/yyyy`** (different format — parse accordingly). `dato` is a string, e.g. `"17.0638"`.
- The series is business-day daily: observations exist **only on bank business days** — no weekends, no bank holidays (the FIX is only determined on bank business days). So a date-range query returns entries only for those days.
- Missing value for a date: **UNVERIFIED via API** (needs a token; a request without one is rejected before data lookup). The SIE web app (same underlying series) renders SF43718 dates without a value as **"N/E" (No Especificado)** — observed live for 19–20/08/2026. Expect the API to simply omit dates with no observation from the `datos` array; verify with your token on day one.

### 4. Publishing time & freshness

- **Official publication time: the FIX is announced "a partir de las 12:00 horas de todos los días hábiles bancarios" (from 12:00 noon, every bank business day)** — Banxico's own *Regímenes Cambiarios en México a partir de 1954* (banxico.org.mx PDF). The brief's "~10:00" figure is **not supported** by any source fetched; the official statement is **12:00** (quoting windows run 9:00–12:00, then the rate is released after 12:00). Mexico City time (America/Mexico_City).
- DOF cadence (Banxico, same document): determined on business day D → published in the DOF on business day **D+1** → used to settle dollar-denominated obligations payable in Mexico **the day after DOF publication**. So "the DOF-published rate for a given day" = the FIX of the prior business day.
- **SAT freshness rule for the CFDI:**
  - CFDI 4.0 schema (fetched `cfdv40.xsd`): `TipoCambio` = *"Atributo condicional para representar el tipo de cambio FIX conforme con la moneda usada. Es requerido cuando la clave de moneda es distinta de MXN y de XXX."* Value = pesos per unit of the currency, up to 6 decimals.
  - Anexo 20 v4.0 PAC validation rules: TipoCambio must lie between the FIX-based upper/lower limits — i.e. within ±(`Porcentaje variación` from catalog `c_Moneda`, **35% for USD**) of **"el valor que se publica para la fecha de la operación"** (the value published for the date of the operation). Outside that band the emitter must obtain a PAC `Confirmacion` key.
  - **CFF article 20** (current text, Cámara de Diputados, reforma DOF 09-04-2026): taxes are determined at "el tipo de cambio que el Banco de México publique en el Diario Oficial de la Federación el día anterior a aquél en que se causen las contribuciones. **Los días en que el Banco de México no publique dicho tipo de cambio se aplicará el último tipo de cambio publicado con anterioridad…**"
  - **Ley Monetaria art. 8**: foreign-currency obligations payable in Mexico are settled "al tipo de cambio que rija en el lugar y fecha en que se haga el pago", determined per Banxico rules.
  - **Net rule for Option A:** use the FIX for the transaction date; when that date is a weekend or bank holiday (no FIX published), use the **last published FIX (prior business day)**. This is the "transaction date or prior business day" behavior the brief describes. Caveat flagged below: no single SAT primary doc was found stating the prior-business-day fallback for CFDI verbatim; it follows from CFF art. 20 + the business-day-only cadence of the FIX + Anexo 20's "value published for the operation date".

### 5. Timezone

- FIX determination/announcement times are **Central Time, Mexico City (`America/Mexico_City`)**. The API's own rate-limit message shows this zone explicitly (`"…2022-12-27 17:06:27 America/Mexico_City"`); daily quota windows reset on CDMX calendar days.
- The API itself carries **no time-of-day or timezone** — query params are calendar dates (`yyyy-MM-dd`), response `fecha` is `dd/MM/yyyy`. There is no published timestamp per observation.

### 6. Error handling

- **Missing/invalid token → HTTP 400** (verified live 2026-08-18): body `{"error":{"url":"https://www.banxico.org.mx/SieAPIRest/service/v1/token","mensaje":"Token inválido","detalle":"El token enviado no es válido, favor de verificar. …"}}`.
- **Rate limit exceeded → HTTP 400** (per docs; note: **not** 429) with `{"error":{"mensaje":"Límite de consultas superado.","detalle":"…America/Mexico_City","timeReset":<epoch s>,"secondsToReset":<s>}}` plus response headers `Bmx-timeReset` and `Bmx-secondsToReset`.
- There is an **`error` node** in error responses (`mensaje`, `detalle`; rate-limit adds `timeReset`/`secondsToReset`).
- **Status for an unknown/nonexistent series: UNVERIFIED** — the token is validated before the series is looked up, so it cannot be tested without a token; the docs publish no status-code table. (404 was observed only for wrong doc-page URLs.)
- **Weekends/holidays:** the FIX is simply not determined → no observation for that date; `datos/oportuno` returns the most recent *published* observation (i.e. the prior business day's FIX until ~12:00 that day). The exact `datos` content for a range spanning non-business days is UNVERIFIED without a token.

### 7. Date range & query params

- Date-range endpoint: `…/series/SF43718/datos/{fechaIni}/{fechaFin}` — dates `yyyy-MM-dd`; **a single date = same start/end** (e.g. `…/datos/2026-08-18/2026-08-18`). No documented limit on range length (**UNVERIFIED** whether a very long span is truncated); full-history variant `…/series/SF43718/datos` exists too.
- Extra params: `decimales=sinCeros`; `incremento=PorcObsAnt|PorcAnual|PorcAcumAnual` (if not computable, `datos` is omitted and an `error` node returned); `locale=es|en`; `mediaType=html|json|xml`.

## Failure / fallback behavior

- **Cache aggressively.** The FIX updates at most once per bank business day, after ~12:00 CDMX. Poll `datos/oportuno` once per business day (e.g. 12:30–13:00 CDMX); never per-invoice, never per-second. On weekends/holidays keep serving the cached prior-business-day FIX.
- **Handle HTTP 400 by body, not status alone:** distinguish "Token inválido" (token problem — alert) from "Límite de consultas superado" (use `secondsToReset` to back off; fall back to cache meanwhile). Do not retry hot.
- **Ordered fallback for the FIX value:** (1) cached Banxico FIX → (2) fresh `datos/oportuno` or date-range query → (3) the daily DOF publication page (`dof.gob.mx` / `sidof.segob.gob.mx`) as a last-resort cross-check. The ticket-08 forecast providers (open.er-api, Frankfurter) are **not** acceptable substitutes for a CFDI — the SAT validates against the FIX.
- **Non-business-day invoice dates:** query the range including the date; if there is no observation for it, use the last observation ≤ that date (CFF art. 20 fallback).
- **Watch for `error` nodes** in otherwise-200-looking payloads (e.g. `incremento` params, rate-limit) and for the mangled-UTF-8 messages (the API returns `charset=UTF-8`; our capture showed byte-level mojibake in one non-UTF-8 console — decode as UTF-8).

## Verified URLs (checked 2026-08-18)

Fetched directly (primary unless noted):
- `https://www.banxico.org.mx/SieAPIRest/` — API landing: series list (incl. SF43718, SF60653), TLS 1.3 requirement, token intro, example JSON
- `https://www.banxico.org.mx/SieAPIRest/service/v1/token` — token request form (captcha), header/query usage
- `https://www.banxico.org.mx/SieAPIRest/service/v1/doc/consultaDatosSerieRango` — range endpoint, formats, params, limits, example
- `https://www.banxico.org.mx/SieAPIRest/service/v1/doc/consultaDatosSerieOp` — `datos/oportuno` endpoint
- `https://www.banxico.org.mx/SieAPIRest/service/v1/doc/consultaDatosSeries` — full-history endpoint
- `https://www.banxico.org.mx/SieAPIRest/service/v1/doc/consultaSeries` — metadata endpoint
- `https://www.banxico.org.mx/SieAPIRest/service/v1/doc/limiteConsultas` — per-token limits, 400 + error/timeReset/secondsToReset, blocking rules
- `https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF43718/datos/oportuno` — live request, no token → HTTP 400, error body captured
- `https://www.banxico.org.mx/mercados/d/{C260B142-835E-2F6B-D7BD-3C9E182BB8B9}.pdf` — *Regímenes Cambiarios en México a partir de 1954* (official): FIX "a partir de las 12:00 horas", DOF next business day, settlement day-after-publication
- `https://www.banxico.org.mx/SieInternet/consultarDirectorioInternetAction.do?accion=consultarCuadro&idCuadro=CF102&sector=22&locale=es` — SIE web table: SF43718/SF60653 metadata, live values (17.0638), "N/E" for no-value dates
- `https://www.banxico.org.mx/apps/dao-web/4/52/fix48-en.html` — FIX app page ("…made public in the DOF the following business day")
- `https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf` — CFF "TEXTO VIGENTE, última reforma DOF 09-04-2026"; **Art. 20** (prior-day DOF rate + last-published fallback)
- `https://www.diputados.gob.mx/LeyesBiblio/pdf_mov/Ley_Monetaria.pdf` — **Art. 8** (rate "en el lugar y fecha en que se haga el pago")
- `https://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd` — CFDI 4.0 schema: `TipoCambio` = FIX, required unless MXN/XXX, 6 decimals
- `http://m.sat.gob.mx/informacion_fiscal/factura_electronica/Documents/GuíaAnexo20.pdf` — SAT fill guide (CFDI 3.3-era): `c_Moneda` (USD: 2 decimals, 35% variation), ±FIX band, `Confirmacion` note
- `http://omawww.sat.gob.mx/tramitesyservicios/Paginas/documentos/Guia_llenado_CFDI_global.pdf` — SAT 4.0 guide (mirrored on sat.gob.mx): TipoCambio = FIX, ±35% band vs FIX
- `http://diariooficial.gob.mx/nota_detalle.php?codigo=5721988&fecha=02%2F04%2F2024` — daily DOF FIX publication (legal basis: Ley Monetaria art. 8, Ley Banxico art. 35)
- `https://www.gncys.com/anexo20/4.0/estandar/i/f/` — Anexo 20 v4.0 PAC validation rules (mirror of SAT's Anexo 20): "valor que se publica para la fecha de la operación" ± band

## UNVERIFIED / flagged

- Exact API `datos`/`dato` output for a range spanning weekends/holidays (empty array vs `N/E`) — requires a token; verify empirically on first integration.
- HTTP status for a nonexistent series ID — token validation happens first; no official status-code table in the docs.
- Whether the `Confirmacion` / ±35%-band validation is actually enforced in 2026 — the guides say it applies "únicamente a partir de que el SAT publique… los procedimientos"; no primary evidence of activation found.
- No SAT primary doc was found that states the "prior business day" rule for CFDI `TipoCambio` verbatim; the rule is assembled from CFF art. 20, Ley Monetaria art. 8, the business-day-only FIX cadence, and Anexo 20's "value published for the operation date".
- The brief's ~10:00 publish time conflicts with Banxico's official 12:00 statement — **12:00 is the official figure**.