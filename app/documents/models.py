from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


@dataclass
class Document:
    document_id: str
    filename: str
    file_path: str
    status: DocumentStatus
    created_at: datetime
    error_message: str | None = None