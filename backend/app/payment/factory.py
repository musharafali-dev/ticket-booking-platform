"""
Single factory function that decides which concrete gateway to hand out.

This is the ONLY place in the codebase that imports concrete gateway
classes. PaymentService and all route handlers depend on
PaymentGatewayProvider (the interface) and call get_payment_gateway() —
they never know or care which concrete class is behind it. Switching the
active gateway in any environment is a one-line config change
(PAYMENT_PROVIDER=jazzcash), not a code change.
"""

from app.payment.gateway import PaymentGatewayProvider
from app.payment.gateways.mock_gateway import MockPaymentGateway
from app.payment.gateways.jazzcash_gateway import JazzCashGateway
from app.payment.gateways.easypaisa_gateway import EasyPaisaGateway
from app.config import settings

_GATEWAY_REGISTRY: dict[str, type[PaymentGatewayProvider]] = {
    "mock": MockPaymentGateway,
    "jazzcash": JazzCashGateway,
    "easypaisa": EasyPaisaGateway,
}


def get_payment_gateway() -> PaymentGatewayProvider:
    gateway_cls = _GATEWAY_REGISTRY.get(settings.PAYMENT_PROVIDER)
    if gateway_cls is None:
        raise ValueError(
            f"Unknown PAYMENT_PROVIDER '{settings.PAYMENT_PROVIDER}'. "
            f"Valid options: {list(_GATEWAY_REGISTRY.keys())}"
        )
    return gateway_cls()
