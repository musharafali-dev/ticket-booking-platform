"""
JazzCash payment gateway integration (stub, ready for real credentials).

JazzCash's actual integration (Mobile Wallet / Page Redirection API) works like:
  1. Merchant builds a request with merchant ID, a transaction reference,
     amount (in paisa, i.e. PKR * 100), and other fixed fields.
  2. All fields are concatenated in a specific order and HMAC-SHA256 signed
     using the "Integrity Salt" provided by JazzCash — this becomes
     `pp_SecureHash`.
  3. User is redirected to JazzCash's hosted page with these fields as a
     POST form.
  4. JazzCash redirects back to JAZZCASH_RETURN_URL with the result, which
     must be verified by recomputing the hash server-side before trusting it.

This class implements that *structure* correctly (field naming, hashing
approach) so that swapping in real JAZZCASH_MERCHANT_ID /
JAZZCASH_INTEGRITY_SALT values and confirming field names against
JazzCash's current merchant documentation is the only remaining work —
no architectural changes needed. The exact field list/order should be
verified against JazzCash's current integration guide before going live,
since payment gateway APIs occasionally revise required fields.
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


class JazzCashGateway(PaymentGatewayProvider):
    provider = PaymentProvider.JAZZCASH

    def _compute_secure_hash(self, fields: dict) -> str:
        """
        JazzCash requires fields sorted alphabetically by key, concatenated
        with '&', prefixed with the integrity salt, then HMAC-SHA256 signed.
        Confirm this exact scheme against current JazzCash docs before
        production use — integration details are gateway-specific and can
        change.
        """
        sorted_values = "&".join(str(fields[k]) for k in sorted(fields.keys()))
        message = f"{settings.JAZZCASH_INTEGRITY_SALT}&{sorted_values}"
        return hmac.new(
            settings.JAZZCASH_INTEGRITY_SALT.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

    async def initiate_payment(
        self, *, amount: float, currency: str, booking_reference: str, description: str
    ) -> PaymentInitiationResult:
        if not settings.JAZZCASH_MERCHANT_ID:
            raise NotImplementedError(
                "JazzCash credentials not configured. Set JAZZCASH_MERCHANT_ID, "
                "JAZZCASH_PASSWORD, and JAZZCASH_INTEGRITY_SALT to enable this gateway."
            )

        amount_in_paisa = int(round(amount * 100))
        txn_ref = f"T{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{secrets.token_hex(3)}"

        fields = {
            "pp_Amount": amount_in_paisa,
            "pp_MerchantID": settings.JAZZCASH_MERCHANT_ID,
            "pp_TxnRefNo": txn_ref,
            "pp_Description": description,
            "pp_TxnCurrency": currency,
            "pp_ReturnURL": settings.JAZZCASH_RETURN_URL,
        }
        secure_hash = self._compute_secure_hash(fields)
        fields["pp_SecureHash"] = secure_hash

        # TODO (before production): construct the actual hosted-page redirect
        # URL per JazzCash's current documentation, and consider whether the
        # form fields should be returned to the frontend for a POST-redirect
        # instead of a GET redirect_url.
        redirect_url = f"https://sandbox.jazzcash.com.pk/checkout?txn={txn_ref}"

        return PaymentInitiationResult(
            external_transaction_id=txn_ref,
            redirect_url=redirect_url,
            requires_redirect=True,
        )

    async def verify_payment(
        self, *, external_transaction_id: str
    ) -> PaymentVerificationResult:
        # TODO (before production): call JazzCash's status inquiry API
        # (typically a POST with pp_TxnRefNo + pp_MerchantID + recomputed
        # hash) and map their response code to is_successful.
        raise NotImplementedError(
            "JazzCash verify_payment requires real API credentials and endpoint. "
            "Implement against JazzCash's Transaction Status Inquiry API."
        )

    def verify_callback_signature(self, payload: dict, signature: str) -> bool:
        fields = {k: v for k, v in payload.items() if k != "pp_SecureHash"}
        expected = self._compute_secure_hash(fields)
        # Constant-time comparison — a naive `==` here would leak timing
        # information about how many leading characters matched, which is
        # a real (if narrow) side-channel for forging a valid signature.
        return hmac.compare_digest(expected, signature)
