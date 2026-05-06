import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="send_email")
def send_email_task(to_email: str, subject: str, body: str) -> None:
    if not settings.EMAILS_ENABLED:
        logger.info("Email disabled. To=%s Subject=%s Body=%s", to_email, subject, body)
        return

    message = EmailMessage()
    message["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as smtp:
        if settings.MAIL_STARTTLS:
            smtp.starttls()
        if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
            smtp.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        smtp.send_message(message)
