from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    analyses: Mapped[list["AnalysisRecord"]] = relationship(back_populates="user")


class AnalysisRecord(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    media_type: Mapped[str] = mapped_column(String(32), nullable=False)  # image|video|text|screenshot
    verdict: Mapped[str] = mapped_column(String(32), nullable=False)
    authenticity_score: Mapped[float] = mapped_column(nullable=False)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # Phase 19.1 / 19.2 — SHA-256 dedup + object storage
    media_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    media_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    user: Mapped["User | None"] = relationship(back_populates="analyses")
    report: Mapped["Report | None"] = relationship(back_populates="analysis", uselist=False)

    __table_args__ = (
        Index("ix_record_user_created", "user_id", "created_at"),
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    analysis: Mapped["AnalysisRecord"] = relationship(back_populates="report")

    __table_args__ = (
        Index("ix_report_analysis", "analysis_id"),
    )
