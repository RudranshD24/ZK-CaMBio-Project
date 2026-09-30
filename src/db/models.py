"""src/db/models.py

SQLAlchemy 2.0 ORM models for ZK-CaMBio.
Implements:
- users: Account identities and status.
- templates: Packed cancelable binary templates (m=512 bits = 64 bytes).
- user_keys: Per-user master keys for server_key mode ONLY (encrypted at rest; not used for user_secret mode).
- audit_log: Operation history with zero biometric data or secret leakage.

STRICT DATA ISOLATION ENFORCEMENT:
NO columns for raw images, pixel data, continuous embeddings (512-d / 256-d),
fused vectors (768-d), or plaintext user secrets.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    """User identity record."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    key_mode: Mapped[str] = mapped_column(
        String(32), nullable=False, default="user_secret"
    )  # "user_secret" or "server_key"
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    templates: Mapped[list[Template]] = relationship(
        "Template", back_populates="user", cascade="all, delete-orphan"
    )
    keys: Mapped[list[UserKey]] = relationship(
        "UserKey", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        "AuditLog", back_populates="user", cascade="all, delete-orphan"
    )


class Template(Base):
    """Cancelable biometric template storage (packed bitstring, m=512 bits = 64 bytes)."""

    __tablename__ = "templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    algo_version: Mapped[str] = mapped_column(String(32), nullable=False, default="zkcambio_v1")
    key_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="user_secret")
    m: Mapped[int] = mapped_column(Integer, nullable=False, default=512)
    template: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)  # Packed 64 bytes for m=512
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship("User", back_populates="templates")

    __table_args__ = (
        Index("ix_templates_user_active", "user_id", "revoked_at"),
    )


class UserKey(Base):
    """Stores per-user keys for 'server_key' mode ONLY.

    For 'user_secret' mode, this table is NOT used and no key material exists on the server.
    """

    __tablename__ = "user_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    key_material: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship("User", back_populates="keys")


class AuditLog(Base):
    """Audit trail for operational events. NEVER logs biometrics or secrets."""

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event: Mapped[str] = mapped_column(String(32), nullable=False)  # enroll, verify, identify, revoke
    key_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    result: Mapped[str] = mapped_column(String(32), nullable=False)  # success, failure, lockout, rejected
    score: Mapped[float | None] = mapped_column(nullable=True)  # Normalized Hamming distance
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )

    user: Mapped[User | None] = relationship("User", back_populates="audit_logs")
