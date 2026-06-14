from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_m3_retrieval"
down_revision = "0002_m2_ingestion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "chunk_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resources.id"), nullable=False),
        sa.Column("source_snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("source_snapshots.id"), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chunks.id"), nullable=False, unique=True),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.execute("ALTER TABLE chunk_embeddings ADD COLUMN embedding vector(64) NOT NULL")
    op.create_index("ix_chunk_embeddings_workspace_project", "chunk_embeddings", ["workspace_id", "project_id"])
    op.create_index("ix_chunk_embeddings_snapshot", "chunk_embeddings", ["source_snapshot_id"])
    op.create_index("ix_chunk_embeddings_chunk", "chunk_embeddings", ["chunk_id"])
    op.execute("CREATE INDEX ix_chunk_embeddings_vector ON chunk_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 16)")

    op.create_table(
        "query_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("mode", sa.Text(), nullable=False),
        sa.Column("top_k", sa.Integer(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("hit_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_query_runs_workspace_project", "query_runs", ["workspace_id", "project_id"])

    op.create_table(
        "retrieval_hits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("query_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("query_runs.id"), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resources.id"), nullable=False),
        sa.Column("source_snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("source_snapshots.id"), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chunks.id"), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("lexical_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("vector_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("rerank_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_retrieval_hits_query", "retrieval_hits", ["query_run_id"])
    op.create_index("ix_retrieval_hits_resource", "retrieval_hits", ["resource_id"])

    op.create_table(
        "context_packets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("query_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("query_runs.id"), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_context_packets_query", "context_packets", ["query_run_id"])

    op.create_table(
        "context_packet_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("context_packet_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("context_packets.id"), nullable=False),
        sa.Column("retrieval_hit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("retrieval_hits.id"), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resources.id"), nullable=False),
        sa.Column("source_snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("source_snapshots.id"), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chunks.id"), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("citation", postgresql.JSONB(), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_context_packet_items_packet", "context_packet_items", ["context_packet_id"])


def downgrade() -> None:
    op.drop_index("ix_context_packet_items_packet", table_name="context_packet_items")
    op.drop_table("context_packet_items")
    op.drop_index("ix_context_packets_query", table_name="context_packets")
    op.drop_table("context_packets")
    op.drop_index("ix_retrieval_hits_resource", table_name="retrieval_hits")
    op.drop_index("ix_retrieval_hits_query", table_name="retrieval_hits")
    op.drop_table("retrieval_hits")
    op.drop_index("ix_query_runs_workspace_project", table_name="query_runs")
    op.drop_table("query_runs")
    op.execute("DROP INDEX IF EXISTS ix_chunk_embeddings_vector")
    op.drop_index("ix_chunk_embeddings_chunk", table_name="chunk_embeddings")
    op.drop_index("ix_chunk_embeddings_snapshot", table_name="chunk_embeddings")
    op.drop_index("ix_chunk_embeddings_workspace_project", table_name="chunk_embeddings")
    op.drop_table("chunk_embeddings")
