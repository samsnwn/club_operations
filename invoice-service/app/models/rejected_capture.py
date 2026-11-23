"""Captures turned away for a reason that will not change on a retry.

A file over the PDF page limit fails the same way every time, so its MD5 is
remembered here and the invoice folder skips it without downloading it again.
Transient failures (a download error, an extraction crash) are never recorded:
those files are retried on the next import.
"""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RejectedCapture(Base):
    __tablename__ = "rejected_captures"

    content_md5: Mapped[str] = mapped_column(String(32), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    reason: Mapped[str] = mapped_column(String(255))
    rejected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
