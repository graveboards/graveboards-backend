"""OAuth token model storing encrypted access and refresh tokens."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql import literal
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Integer, LargeBinary

from app.utils import aware_utcnow

from .base import Base

if TYPE_CHECKING:
    from sqlalchemy.sql.elements import ColumnElement


class OAuthToken(Base):
    """An OAuth token pair belonging to a user."""

    __tablename__ = "oauth_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    access_token_enc: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    refresh_token_enc: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=aware_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=aware_utcnow, onupdate=aware_utcnow
    )

    @hybrid_property
    def access_token(self) -> str:
        """Return the decrypted access token."""
        from app.security.oauth_encryption import decrypt_token

        return decrypt_token(self.access_token_enc)

    @access_token.inplace.expression
    def _access_token_expr(self) -> ColumnElement:
        return literal(None)

    @hybrid_property
    def refresh_token(self) -> str | None:
        """Return the decrypted refresh token, or ``None`` if none is stored."""
        if self.refresh_token_enc is None:
            return None
        from app.security.oauth_encryption import decrypt_token

        return decrypt_token(self.refresh_token_enc)

    def set_access_token(self, token: str) -> None:
        """Encrypt and store the given access token."""
        from app.security.oauth_encryption import encrypt_token

        self.access_token_enc = encrypt_token(token)

    def set_refresh_token(self, token: str) -> None:
        """Encrypt and store the given refresh token."""
        from app.security.oauth_encryption import encrypt_token

        self.refresh_token_enc = encrypt_token(token)
