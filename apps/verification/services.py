"""Boundary for a future malware-scanning integration.

The Phase 2 local environment has no scanner. Documents therefore remain in
PENDING status and are never made downloadable merely because they uploaded.
"""

from .models import VerificationDocument


def queue_document_scan(document: VerificationDocument) -> None:
    """Queue a scan when a configured worker/service is introduced later.

    Deliberately a no-op for now: it must not mark a file clean without a real
    malware scanner.
    """
    return None
