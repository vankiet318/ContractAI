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
    session_id: str
    filename: str
    file_path: str
    status: DocumentStatus
    created_at: datetime
    error_message: str | None = None

# Shown to users instead of the raw exception, which can contain internal
# paths or library details; the full error goes to the server log.
PROCESSING_FAILED_MESSAGE = (
    "Không xử lý được tài liệu. Vui lòng kiểm tra file và thử lại."
)
