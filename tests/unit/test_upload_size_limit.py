import asyncio
from io import BytesIO

import pytest
from fastapi import UploadFile

from app.api.documents import UploadTooLargeError, save_upload


def test_upload_within_limit_is_saved(tmp_path):
    destination = tmp_path / "doc.pdf"

    asyncio.run(save_upload(UploadFile(BytesIO(b"x" * 100)), destination, max_bytes=100))

    assert destination.read_bytes() == b"x" * 100


def test_oversized_upload_is_rejected_and_partial_file_removed(tmp_path):
    destination = tmp_path / "doc.pdf"

    with pytest.raises(UploadTooLargeError):
        asyncio.run(save_upload(UploadFile(BytesIO(b"x" * 101)), destination, max_bytes=100))

    assert not destination.exists()
