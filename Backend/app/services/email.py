import logging

from app.tasks.email import send_email_task

logger = logging.getLogger(__name__)


def queue_email(to_email: str, subject: str, body: str) -> None:
    """Queue email work with Celery.

    In local development Celery runs eagerly by default, so the task logs the
    message instead of requiring a worker. In production, run a worker process.
    """

    try:
        send_email_task.delay(to_email, subject, body)
    except Exception as exc:
        logger.warning("Could not queue email to %s: %s", to_email, exc)
        logger.info("Email fallback for %s | %s | %s", to_email, subject, body)


def queue_verification_email(to_email: str, verification_link: str) -> None:
    queue_email(
        to_email=to_email,
        subject="Verify your email address",
        body=(
            "Welcome! Verify your account by opening this link:\n"
            f"{verification_link}\n\n"
            "This link expires automatically."
        ),
    )


def queue_password_reset_email(to_email: str, reset_link: str) -> None:
    queue_email(
        to_email=to_email,
        subject="Reset your password",
        body=(
            "Reset your password by opening this link:\n"
            f"{reset_link}\n\n"
            "If you did not request this, you can ignore this email."
        ),
    )
