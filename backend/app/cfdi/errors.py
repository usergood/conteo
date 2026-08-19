"""SAT/PAC error code mapping (ticket 10).

Maps SAT rejection codes from PAC responses to friendly user messages
with remediation steps. Config-driven so new codes can be added without deploy.
"""

from __future__ import annotations

# Canonical error code catalog
# Each entry: code → {title, description, user_message, remediation_steps, severity}
ERROR_CODES: dict[str, dict] = {
    # XML structure / validation
    "201": {
        "title": "El comprobante tiene errores de estructura",
        "description": "El XML no cumple con la estructura del XSD de CFDI 4.0",
        "user_message": "The invoice XML has structural errors. Please regenerate it.",
        "remediation_steps": [
            "Verify all required fields are present",
            "Check data types and formats (dates, decimals)",
            "Ensure namespace declarations are correct",
        ],
        "severity": "error",
    },
    "202": {
        "title": "El comprobante tiene errores en los datos",
        "description": "Los datos del comprobante no son válidos según las reglas del SAT",
        "user_message": "The invoice contains invalid data. Please check the details.",
        "remediation_steps": [
            "Verify RFC format (12 or 13 characters)",
            "Check that amounts are positive and correctly formatted",
            "Validate date format (YYYY-MM-DDThh:mm:ss)",
        ],
        "severity": "error",
    },
    "203": {
        "title": "El sello es inválido",
        "description": "El sello digital no pudo ser verificado",
        "user_message": "The digital seal could not be verified. Check your CSD credentials.",
        "remediation_steps": [
            "Verify your CSD certificate is not expired",
            "Ensure the private key matches the certificate",
            "Check that the passphrase is correct",
        ],
        "severity": "error",
    },
    "204": {
        "title": "El certificado es inválido",
        "description": "El certificado de sello digital no es válido",
        "user_message": "Your digital certificate is invalid or expired.",
        "remediation_steps": [
            "Download a new certificate from the SAT portal",
            "Ensure the certificate is active and not revoked",
        ],
        "severity": "error",
    },
    "205": {
        "title": "El certificado ya fue dado de baja",
        "description": "El CSD ha sido revocado por el SAT",
        "user_message": "Your CSD has been revoked by the SAT. You need a new certificate.",
        "remediation_steps": [
            "Generate a new e.firma at the SAT portal",
            "Update your CSD in the app settings",
        ],
        "severity": "error",
    },
    # Duplicate / UUID
    "301": {
        "title": "El comprobante ya fue registrado",
        "description": "Un CFDI con el mismo UUID ya existe en el SAT",
        "user_message": "This invoice has already been registered. No duplicate allowed.",
        "remediation_steps": [
            "Check if this invoice was already stamped",
            "Use the existing UUID for reference",
        ],
        "severity": "warning",
    },
    "302": {
        "title": "El comprobante no puede ser cancelado",
        "description": "El CFDI no puede ser cancelado por restricciones del SAT",
        "user_message": "This invoice cannot be cancelled at this time.",
        "remediation_steps": [
            "Check the cancellation deadline (within the same fiscal year)",
            "Verify the receiver hasn't accepted it yet",
        ],
        "severity": "error",
    },
    # Certificate
    "401": {
        "title": "El certificado no está activo",
        "description": "El CSD no se encuentra activo en el SAT",
        "user_message": "Your CSD is not active. Please check its status.",
        "remediation_steps": [
            "Verify your CSD status at the SAT portal",
            "Renew if expired",
        ],
        "severity": "error",
    },
    # General
    "501": {
        "title": "Error interno del PAC",
        "description": "El PAC experimentó un error interno",
        "user_message": "The stamping service is temporarily unavailable. Please try again.",
        "remediation_steps": [
            "Wait a few minutes and retry",
            "Contact support if the issue persists",
        ],
        "severity": "error",
    },
    "502": {
        "title": "El PAC no puede procesar la solicitud",
        "description": "El PAC no puede procesar la solicitud en este momento",
        "user_message": "The stamping service cannot process your request right now.",
        "remediation_steps": [
            "Try again in a few minutes",
            "Check PAC service status",
        ],
        "severity": "error",
    },
    # Rate / exchange
    "601": {
        "title": "Tipo de cambio fuera de rango",
        "description": "El tipo de cambio está fuera del rango permitido por el SAT",
        "user_message": "The exchange rate is outside the allowed range. A PAC confirmation may be needed.",
        "remediation_steps": [
            "Verify the exchange rate is from Banxico DOF",
            "Request a PAC confirmation key if needed",
        ],
        "severity": "warning",
    },
    # Total
    "602": {
        "title": "El total excede el límite",
        "description": "El total del comprobante excede el límite de la RMF",
        "user_message": "The invoice total exceeds the limit. A PAC confirmation is required.",
        "remediation_steps": [
            "Request a PAC confirmation key",
            "Verify the total amount is correct",
        ],
        "severity": "warning",
    },
}


def get_error_info(code: str) -> dict:
    """Look up an error code and return its info, or a generic fallback."""
    if code in ERROR_CODES:
        return ERROR_CODES[code]
    return {
        "title": f"Error {code}",
        "description": f"SAT/PAC error code {code}",
        "user_message": f"An error occurred (code: {code}). Please check the details.",
        "remediation_steps": [
            "Check the error code in SAT documentation",
            "Contact support if needed",
        ],
        "severity": "error",
    }


def format_pac_error(code: str, detail: str = "") -> dict:
    """Format a PAC error response into a user-friendly structure."""
    info = get_error_info(code)
    return {
        "code": code,
        "title": info["title"],
        "description": info["description"],
        "user_message": info["user_message"],
        "remediation_steps": info["remediation_steps"],
        "severity": info["severity"],
        "detail": detail,
    }
