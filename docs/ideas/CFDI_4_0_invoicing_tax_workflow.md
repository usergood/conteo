# Technical Specification: Mexican SAT (CFDI 4.0) Invoicing & Tax Workflow for US Clients

## 1. Overview & Business Context

This specification outlines the business rules, data schemas, validation logic, and workflows required to generate Mexican tax-compliant electronic invoices (**CFDI 4.0**) for software development / IT consulting services rendered by a Mexico-based contractor (under the **RESICO** regime) to a US-based client paying in US Dollars (USD).

---

## 2. Tax & Compliance Rules Summary

* **Authority:** SAT (*Servicio de Administración Tributaria*, Mexico).
* **Standard:** CFDI Version 4.0 (*Comprobante Fiscal Digital por Internet*).
* **Tax Regime (Issuer):** RESICO (*Régimen Simplificado de Confianza*) — Simplified tax regime with reduced ISR (Income Tax) rates (1.0% – 2.5%).
* **VAT / IVA Treatment:** **0% VAT (Tasa 0%)** applies under Article 29 of the Mexican VAT Law (*Ley del Impuesto al Valor Agregado*) for the export of intangible services (IT development/consulting) consumed abroad.
* **Tax Withholding:** Foreign clients cannot withhold Mexican taxes (0% ISR/IVA withholding).

---

## 3. Foreign Recipient Data Schema (US Client)

When issuing a CFDI 4.0 to a non-Mexican entity, SAT mandates specific generic values:

| Field Name (CFDI 4.0 Node) | Value / Format | Description & Rule |
| --- | --- | --- |
| `RFC` | `XEXX010101000` | Generic RFC for foreign clients (*RFC Genérico Extranjero*). |
| `Nombre` / `Razón Social` | Text (e.g., `"Acme Software Corp LLC"`) | Official legal business name of the US company. |
| `RégimenFiscalReceptor` | `616` | Code for *"Sin obligaciones fiscales"*. |
| `UsoCFDI` | `S01` | Code for *"Sin efectos fiscales"*. |
| `DomicilioFiscalReceptor` | 5-digit String (Issuer's Postal Code) | SAT rule: Must match the **issuer's** Mexican fiscal zip code when using `XEXX010101000`. |
| `ResidenciaFiscal` | `USA` | 3-letter ISO 3166-1 alpha-3 country code for the United States. |
| `NumRegIdTrib` | String (Optional) | US Employer Identification Number (EIN) or SSN of the recipient. |
| `Exportacion` | `01` | Code for *"No aplica"* (applies to intangible services/consulting, not physical goods). |

---

## 4. Invoicing Strategies (Currency Handling)

The application must support **two options** for handling foreign currency transactions:

### Option A: Direct USD Invoicing (`Moneda: USD`)

* **Use Case:** Invoice is issued in USD using the official daily exchange rate.
* **Field Config:**
* `Moneda`: `"USD"`
* `TipoCambio`: Official exchange rate published by **Banco de México (Banxico)** in the *Diario Oficial de la Federación* (DOF) on the date of transaction/payment receipt.


* **Calculation Engine:**
* `SubTotal (USD)` = Sum of line items in USD.
* `Total (USD)` = SubTotal in USD.
* `SubTotal (MXN)` = `SubTotal (USD)` × `TipoCambio`.
* `Total (MXN)` = `Total (USD)` × `TipoCambio`.


* **Pros & Cons:** Fully supported natively by SAT. Automated MXN equivalence calculation in the XML layout. Requires an automated integration or manual input for the Banxico/DOF exchange rate.

### Option B: Post-Settlement MXN Invoicing (`Moneda: MXN`)

* **Use Case:** Waiting until USD funds are converted and deposited into the Mexican bank account, then issuing the invoice for the exact MXN amount received.
* **Field Config:**
* `Moneda`: `"MXN"`
* `TipoCambio`: `"1"` (or omitted per MXN standard).


* **Calculation Engine:**
* `SubTotal (MXN)` = Exact net MXN deposited in bank account.
* `Total (MXN)` = `SubTotal (MXN)`.


* **Constraint:** The invoice **must** be generated within the same fiscal month as the payment receipt date to align with monthly RESICO auto-populated tax filings.

---

## 5. Line Item & Tax Calculation Rules

For each item/service in the invoice (`Concepto` node):

* **Product/Service Code (`ClaveProdServ`):**
* `83121603` (Software maintenance and support)
* `80101507` (Information technology consultation)
* `81111508` (Application development)


* **Unit Code (`ClaveUnidad`):** `E48` (Service unit) or `HUR` (Hours) / `DAY` (Days).
* **Tax Object (`ObjetoImp`):** `02` (*Sí objeto de impuesto*).
* **Tax Breakdown (`Impuestos` -> `Traslados`):**
* `Impuesto`: `002` (IVA / VAT).
* `TipoFactor`: `Tasa`.
* `TasaOCuota`: `0.000000` (0%).
* `Base`: Subtotal amount for the line item.
* `Importe`: `0.00`.


* **Withholding (`Retenciones`):** Omitted / None.

---

## 6. Monthly Tax & Filing Workflow State Machine

1. **Payment Ingest:** Record foreign bank transfer (SWIFT / Wise / direct bank transfer).
2. **CFDI Generation:**
* Select Option A (USD + Banxico rate) or Option B (Bank-settled MXN amount).
* Apply foreign recipient defaults (`XEXX010101000`, `616`, `S01`, `0% IVA`).
* Sign XML payload using issuer's **e.firma** (Private Key `.key`, Certificate `.cer`, and Passphrase) via a certified PAC (*Proveedor Autorizado de Certificación*).


3. **Monthly Pre-Filing (Due by the 17th of the following month):**
* Fetch all stamped CFDIs for the month.
* SAT auto-calculates RESICO ISR based on gross MXN revenues:
* Up to $25,000 MXN: **1.00%**
* Up to $50,000 MXN: **1.10%**
* Up to $83,333 MXN: **1.50%**
* Up to $166,666 MXN: **2.00%**
* Up to $2,916,666 MXN: **2.50%**




4. **Filing Confirmation:** User approves pre-filled monthly tax declaration on the SAT portal and completes payment.

---

## 7. Data Model / Entity Suggestions for Developers

```typescript
interface ForeignClient {
  id: string;
  legalName: string; // e.g. "US Tech Corp LLC"
  genericRfc: "XEXX010101000";
  fiscalRegime: "616";
  cfdiUsage: "S01";
  countryCode: "USA";
  taxIdNumber?: string; // US EIN
}

interface InvoiceItem {
  satProductCode: string; // e.g. "80101507"
  satUnitCode: string; // e.g. "E48"
  description: string;
  quantity: number;
  unitPrice: number;
  taxObject: "02"; // Subject to tax
  vatRate: 0.00; // 0% Export VAT
}

interface InvoiceRequest {
  clientId: string;
  currencyOption: "USD_DIRECT" | "MXN_POST_SETTLEMENT";
  currency: "USD" | "MXN";
  exchangeRate?: number; // Banxico DOF rate if USD_DIRECT, 1.0 if MXN
  items: InvoiceItem[];
  paymentForm: "03" | "31" | "99"; // Transfer, Intermediary, or To be defined
  paymentMethod: "PUE" | "PPD"; // Single payment (PUE) recommended for completed transfers
}

```

---

## 8. App Implementation Rules & Validations

1. **Enforce Default Overrides for Foreign Clients:** When `isForeignClient === true`, automatically lock RFC to `XEXX010101000`, Fiscal Regime to `616`, CFDI Usage to `S01`, and Export status to `01`.
2. **Prevent Non-Zero VAT:** If destination is foreign service export, prevent users from manually adding 16% VAT. Force 0% VAT rate (`Tasa 0%`).
3. **Banxico API Integration (Optional but recommended):** For Option A, fetch the official daily exchange rate from Banxico's public API (`[https://www.banxico.org.mx/SieAPIRest/service/v1/](https://www.banxico.org.mx/SieAPIRest/service/v1/)`).
4. **Month-End Safeguard:** For Option B, warn the user if an invoice is created in a different month than when the funds were deposited, as it will disrupt SAT's automatic monthly RESICO income calculation.
