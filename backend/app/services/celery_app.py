import base64
import asyncio
from celery import Celery
from app.config import settings

celery_app = Celery(
    "sentry_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300
)

@celery_app.task(bind=True, name="app.services.celery_app.analyze_email_task", max_retries=3)
def analyze_email_task(self, raw_bytes_b64: str, source: str = "celery_async"):
    """
    Background worker task to process and analyze incoming email payloads.
    """
    try:
        from app.db.database import AsyncSessionLocal
        from app.api.v1.emails import process_and_store_email

        raw_bytes = base64.b64decode(raw_bytes_b64)

        async def _run():
            async with AsyncSessionLocal() as db:
                email_rec = await process_and_store_email(raw_bytes, source=source, db=db)
                return email_rec.id

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        email_id = loop.run_until_complete(_run())
        loop.close()

        return {"status": "success", "email_id": email_id}
    except Exception as exc:
        self.retry(exc=exc, countdown=5)
