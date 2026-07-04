"""
Mock payment gateway for local development.

Completes synchronously and always succeeds — no redirect, no external
network call, no real money. This lets the entire booking→payment→
confirmation flow be built and tested end-to-end before any real gateway
credentials exist.
"""

import secrets

from app.payment.gateway import (
    PaymentGatewayProvider,
    PaymentInitiationResult,
    PaymentVerificationResult,
)
from app.common.enums import PaymentProvider


class MockPaymentGateway(PaymentGatewayProvider):
    provider = PaymentProvider.MOCK

    async def initiate_payment(
        self, *, amount: float, currency: str, booking_reference: str, description: str
    ) -> PaymentInitiationResult:
        transaction_id = f"MOCK-{secrets.token_hex(6).upper()}"
        return PaymentInitiationResult(
            external_transaction_id=transaction_id,
            redirect_url=None,
            requires_redirect=False,
        )

    async def verify_payment(
        self, *, external_transaction_id: str
    ) -> PaymentVerificationResult:
        # Mock gateway: every initiated payment is immediately "successful".
        return PaymentVerificationResult(
            is_successful=True,
            external_transaction_id=external_transaction_id,
            raw_status="SUCCESS",
        )

    def verify_callback_signature(self, payload: dict, signature: str) -> bool:
        # No real callback in mock mode; always considered valid for local dev.
        return True
