"""
EasyPaisa payment gateway integration (stub, ready for real credentials).

EasyPaisa's integration (like JazzCash) typically involves:
  1. A store ID and a hash key issued by EasyPaisa.
  2. Request fields hashed (commonly HMAC-SHA256) using the hash key.
  3. Redirect to EasyPaisa's hosted checkout, then a server-to-server or
     redirect-based callback confirming payment status.

Exact field names, hashing scheme, and endpoints must be confirmed against
EasyPaisa's current merchant integration documentation before production
use — this stub implements the general shape (signed request, verified
callback) so only gateway-specific details need filling in.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timezone

from app.payment.gateway import (
    PaymentGatewayProvider,
    PaymentInitiationResult,
    PaymentVerificationResult,
)
from app.common.enums import PaymentProvider
from app.config import settings


class EasyPaisaGateway(PaymentGatewayProvider):
    provider = PaymentProvider.EASYPAISA

    def _compute_hash(self, fields: dict) -> str:
        sorted_values = "&".join(str(fields[k]) for k in sorted(fields.keys()))
        return hmac.new(
            settings.EASYPAISA_HASH_KEY.encode(),
            sorted_values.encode(),
            hashlib.sha256,
        ).hexdigest()

    async def initiate_payment(
        self, *, amount: float, currency: str, booking_reference: str, description: str
    ) -> PaymentInitiationResult:
        if not settings.EASYPAISA_STORE_ID:
            raise NotImplementedError(
                "EasyPaisa credentials not configured. Set EASYPAISA_STORE_ID "
                "and EASYPAISA_HASH_KEY to enable this gateway."
            )

        txn_ref = f"EP{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{secrets.token_hex(3)}"

        fields = {
            "storeId": settings.EASYPAISA_STORE_ID,
            "amount": f"{amount:.2f}",
            "orderRefNum": txn_ref,
            "postBackURL": settings.EASYPAISA_RETURN_URL,
        }
        signature = self._compute_hash(fields)

        # TODO (before production): confirm actual EasyPaisa hosted checkout
        # URL structure and required fields against current documentation.
        # The signature MUST be included as a query param / form field here —
        # omitting it (as an earlier draft of this stub did) would produce an
        # unsigned request that a real EasyPaisa integration would reject, or
        # worse, that a lax server-side check might silently accept.
        redirect_url = f"https://easypay.easypaisa.com.pk/checkout?order={txn_ref}&signature={signature}"

        return PaymentInitiationResult(
            external_transaction_id=txn_ref,
            redirect_url=redirect_url,
            requires_redirect=True,
        )

    async def verify_payment(
        self, *, external_transaction_id: str
    ) -> PaymentVerificationResult:
        # TODO (before production): call EasyPaisa's inquiry API and map
        # their response to is_successful.
        raise NotImplementedError(
            "EasyPaisa verify_payment requires real API credentials and endpoint."
        )

    def verify_callback_signature(self, payload: dict, signature: str) -> bool:
        fields = {k: v for k, v in payload.items() if k != "signature"}
        expected = self._compute_hash(fields)
        return hmac.compare_digest(expected, signature)
