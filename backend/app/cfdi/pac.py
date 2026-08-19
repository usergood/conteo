"""PAC provider interface abstraction (ticket 01).

Abstract interface for PAC (Proveedor Autorizado de Certificación) stamping.
The app generates unsigned CFDI 4.0 XML; PAC validates, signs, and stamps.
Provider-agnostic — swap implementations without changing invoice logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class StampResult:
    """Successful stamp response from a PAC."""
    uuid: str
    sat_xml: str  # stamped XML (includes TimbreFiscalDigital)
    pac_response: dict = field(default_factory=dict)
    fecha_timbrado: str = ""
    no_certificado_sat: str = ""


@dataclass(frozen=True)
class CancellationResult:
    """Successful cancellation response from a PAC."""
    uuid: str
    sat_xml: str  # cancellation acknowledgment XML
    pac_response: dict = field(default_factory=dict)


@dataclass(frozen=True)
class PACError:
    """PAC rejection with SAT error code."""
    code: str
    message: str
    detail: str = ""
    severity: str = "error"


class PACProvider(Protocol):
    """Protocol defining the PAC stamping interface.

    Implementations: Finkok, Facturama, SW SmarterWeb, etc.
    """

    def stamp(self, unsigned_xml: str, credentials: dict) -> StampResult:
        """Validate, sign, and stamp a CFDI XML.

        Args:
            unsigned_xml: The unsigned CFDI 4.0 XML string.
            credentials: PAC authentication (api_key, api_secret, etc.)

        Returns:
            StampResult with UUID and stamped XML.

        Raises:
            PACError if stamping fails.
        """
        ...

    def cancel(self, uuid: str, reason: str, credentials: dict) -> CancellationResult:
        """Cancel a previously stamped CFDI.

        Args:
            uuid: The UUID of the CFDI to cancel.
            reason: Cancellation reason code.
            credentials: PAC authentication.

        Returns:
            CancellationResult.

        Raises:
            PACError if cancellation fails.
        """
        ...

    def status(self, uuid: str, credentials: dict) -> dict:
        """Check the status of a stamped CFDI.

        Returns a dict with at minimum {"status": str, "sat_status": str}.
        """
        ...


class FinkokProvider:
    """Finkok PAC implementation.

    Finkok uses a REST API with basic auth (user + password).
    Sandbox: https://sandbox.finkok.com/svc/…​
    Production: https://app.finkok.com/svc/…​
    """

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password

    def stamp(self, unsigned_xml: str, credentials: dict | None = None) -> StampResult:
        # Implementation will use httpx to call Finkok API
        raise NotImplementedError("Finkok stamp — implement with live PAC credentials")

    def cancel(self, uuid: str, reason: str, credentials: dict | None = None) -> CancellationResult:
        raise NotImplementedError("Finkok cancel — implement with live PAC credentials")

    def status(self, uuid: str, credentials: dict | None = None) -> dict:
        raise NotImplementedError("Finkok status — implement with live PAC credentials")


class NullPACProvider:
    """Test/null PAC that accepts any XML and returns a deterministic UUID.

    Used for testing and development. Does NOT contact any PAC.
    """

    def stamp(self, unsigned_xml: str, credentials: dict | None = None) -> StampResult:
        import uuid as _uuid
        return StampResult(
            uuid=str(_uuid.uuid4()),
            sat_xml=unsigned_xml,  # echo back unchanged
            pac_response={"provider": "null"},
            fecha_timbrado="2026-01-01T00:00:00",
            no_certificado_sat="00000000000000000000",
        )

    def cancel(self, uuid: str, reason: str, credentials: dict | None = None) -> CancellationResult:
        return CancellationResult(
            uuid=uuid,
            sat_xml="",
            pac_response={"provider": "null", "cancelled": True},
        )

    def status(self, uuid: str, credentials: dict | None = None) -> dict:
        return {"status": "stamped", "sat_status": "active", "provider": "null"}
