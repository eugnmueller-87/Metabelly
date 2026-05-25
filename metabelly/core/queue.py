from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel


class QueueStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class QueueItem(BaseModel):
    id: UUID = uuid4()
    gmail_id: str
    thread_id: str
    sender_email: str
    subject: str
    content_encrypted: str          # raw email body, encrypted at rest
    status: QueueStatus = QueueStatus.PENDING
    attempts: int = 0
    created_at: datetime = datetime.now(timezone.utc)
    processed_at: datetime | None = None
