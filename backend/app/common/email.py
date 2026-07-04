"""
Email sending abstraction.

Same pattern as the payment gateway: one interface, swappable backends.
`ConsoleEmailBackend` logs the email instead of sending it, so local dev
and CI never need real credentials, and the registration endpoint's
response shape stays identical regardless of which backend is active —
the verification token never appears in the API response, only in
whichever backend actually delivers it.
"""

import logging
from abc import ABC, abstractmethod

from app.config import settings

logger = logging.getLogger("app.email")


class EmailBackend(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> None: ...


class ConsoleEmailBackend(EmailBackend):
    """Logs the email content instead of sending it. Used for local dev."""

    async def send(self, to: str, subject: str, body: str) -> None:
        logger.info(
            "\n"
            "==================== DEV EMAIL (console backend) ====================\n"
            f"To:      {to}\n"
            f"Subject: {subject}\n"
            f"Body:\n{body}\n"
            "=======================================================================\n"
        )


class SendGridEmailBackend(EmailBackend):
    """Real email delivery via SendGrid. Requires SENDGRID_API_KEY."""

    async def send(self, to: str, subject: str, body: str) -> None:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email=settings.SENDGRID_FROM_EMAIL,
            to_emails=to,
            subject=subject,
            html_content=body,
        )
        client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        # SendGrid's client is sync; run it in a thread to avoid blocking the event loop.
        import asyncio

        await asyncio.to_thread(client.send, message)


def get_email_backend() -> EmailBackend:
    if settings.EMAIL_BACKEND == "sendgrid":
        return SendGridEmailBackend()
    return ConsoleEmailBackend()


async def send_verification_email(to_email: str, token: str) -> None:
    verify_url = f"http://localhost:3000/verify-email?token={token}"
    backend = get_email_backend()
    await backend.send(
        to=to_email,
        subject="Verify your Ticket Booking Platform account",
        body=(
            f"Welcome! Please verify your email by visiting:\n{verify_url}\n\n"
            f"This link expires in {settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS} hours."
        ),
    )
