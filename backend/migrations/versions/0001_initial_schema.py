"""Create the AIpedia Hub MVP schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-01
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("slug", sa.String(length=120), nullable=False, unique=True),
    )
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("slug", sa.String(length=120), nullable=False, unique=True),
    )
    op.create_table(
        "tools",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=280), nullable=False, unique=True),
        sa.Column("aliases", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("official_url", sa.Text(), nullable=True),
        sa.Column("canonical_url", sa.Text(), nullable=True, unique=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("why_saved", sa.Text(), nullable=True),
        sa.Column("use_cases", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("pricing_model", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("platforms", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("last_viewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_tools_name", "tools", ["name"])
    op.create_index("ix_tools_status", "tools", ["status"])
    op.create_table(
        "tool_tags",
        sa.Column(
            "tool_id", sa.Integer(), sa.ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column(
            "tag_id", sa.Integer(), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
        ),
    )
    op.execute("PRAGMA foreign_keys = ON")
    op.execute("PRAGMA journal_mode = WAL")
    op.execute(
        """
        CREATE VIRTUAL TABLE tools_fts USING fts5(
            name, aliases, summary, why_saved, use_cases, notes,
            content='tools', content_rowid='id', tokenize='trigram'
        )
        """
    )
    op.execute(
        """
        CREATE TRIGGER tools_ai AFTER INSERT ON tools BEGIN
            INSERT INTO tools_fts(rowid, name, aliases, summary, why_saved, use_cases, notes)
            VALUES (new.id, new.name, new.aliases, new.summary, new.why_saved, new.use_cases, new.notes);
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER tools_ad AFTER DELETE ON tools BEGIN
            INSERT INTO tools_fts(tools_fts, rowid, name, aliases, summary, why_saved, use_cases, notes)
            VALUES ('delete', old.id, old.name, old.aliases, old.summary, old.why_saved, old.use_cases, old.notes);
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER tools_au AFTER UPDATE ON tools BEGIN
            INSERT INTO tools_fts(tools_fts, rowid, name, aliases, summary, why_saved, use_cases, notes)
            VALUES ('delete', old.id, old.name, old.aliases, old.summary, old.why_saved, old.use_cases, old.notes);
            INSERT INTO tools_fts(rowid, name, aliases, summary, why_saved, use_cases, notes)
            VALUES (new.id, new.name, new.aliases, new.summary, new.why_saved, new.use_cases, new.notes);
        END
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS tools_au")
    op.execute("DROP TRIGGER IF EXISTS tools_ad")
    op.execute("DROP TRIGGER IF EXISTS tools_ai")
    op.execute("DROP TABLE IF EXISTS tools_fts")
    op.drop_table("tool_tags")
    op.drop_index("ix_tools_status", table_name="tools")
    op.drop_index("ix_tools_name", table_name="tools")
    op.drop_table("tools")
    op.drop_table("tags")
    op.drop_table("categories")
