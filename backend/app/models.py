from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

tool_tags = Table(
    "tool_tags",
    Base.metadata,
    Column("tool_id", ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    tools: Mapped[list[Tool]] = relationship(back_populates="category")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    tools: Mapped[list[Tool]] = relationship(secondary=tool_tags, back_populates="tags")


class Tool(Base):
    __tablename__ = "tools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(280), nullable=False, unique=True)
    aliases: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    official_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical_url: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_saved: Mapped[str | None] = mapped_column(Text, nullable=True)
    use_cases: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    pricing_model: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    platforms: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )
    last_viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    category: Mapped[Category | None] = relationship(back_populates="tools")
    tags: Mapped[list[Tag]] = relationship(secondary=tool_tags, back_populates="tools")
