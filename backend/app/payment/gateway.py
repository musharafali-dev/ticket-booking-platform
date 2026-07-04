"""
Payment gateway abstraction.

Design goal (explicitly requested): swapping Mock for real JazzCash/EasyPaisa
later must require zero changes to booking logic or route handlers — only
a new class implementing PaymentGatewayProvider, plus config to select it.

This is the Strategy pattern: PaymentService (service.py) depends only on
this interface, never on a concrete gateway. get_payment_gateway() is the
single place that decides which concrete implementation to hand out, based
on settings.PAYMENT_PROVIDER.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.common.enums import PaymentProvider


@dataclass
class PaymentInitiationResult:
    """
    What a gateway returns when a payment is initiated. `redirect_url` is
    None for gateways that complete synchronously (like our mock); real
    JazzCash/EasyPaisa integrations redirect the user to a hosted checkout
    page and confirm asynchronously via a callback/webhook.
    """

    external_transaction_id: str
    redirect_url: str | None
    requires_redirect: bool


@dataclass
class PaymentVerificationResult:
    """Result of checking/confirming a payment's actual status with the gateway."""

    is_successful: bool
    external_transaction_id: str
    raw_status: str
    failure_reason: str | None = None


class PaymentGatewayProvider(ABC):
    """
    Every payment gateway (mock, JazzCash, EasyPaisa, and any future
    provider) implements this interface. PaymentService never imports a
    concrete gateway class directly — only this interface.
    """

    provider: PaymentProvider

    @abstractmethod
    async def initiate_payment(
        self, *, amount: float, currency: str, booking_reference: str, description: str
    ) -> PaymentInitiationResult:
        """Start a payment. May return a redirect URL for hosted checkout flows."""
        ...

    @abstractmethod
    async def verify_payment(
        self, *, external_transaction_id: str
    ) -> PaymentVerificationResult:
        """Check the actual status of a previously-initiated payment with the gateway."""
        ...

    @abstractmethod
    def verify_callback_signature(self, payload: dict, signature: str) -> bool:
        """
        Verify that an inbound webhook/callback genuinely came from the
        gateway (not a forged request). Real gateways use HMAC or a similar
        scheme with a shared secret; this is a mandatory security check
        before trusting any callback-reported payment status.
        """
        ...
