from __future__ import annotations

from alembic import op

revision = "0022_d_service_link_candidates"
down_revision = "0021_e1_graph_merges"
branch_labels = None
depends_on = None

NEW_TYPES = "('same_path', 'same_label', 'same_symbol', 'service_http_route', 'service_async_topic', 'service_grpc_method', 'service_graphql_operation', 'service_trpc_route')"
OLD_TYPES = "('same_path', 'same_label', 'same_symbol')"


def upgrade() -> None:
    op.drop_constraint("ck_graph_merge_candidates_type", "graph_merge_reconcile_candidates", type_="check")
    op.create_check_constraint("ck_graph_merge_candidates_type", "graph_merge_reconcile_candidates", f"candidate_type IN {NEW_TYPES}")


def downgrade() -> None:
    op.execute("DELETE FROM graph_merge_reconcile_candidates WHERE candidate_type LIKE 'service_%'")
    op.drop_constraint("ck_graph_merge_candidates_type", "graph_merge_reconcile_candidates", type_="check")
    op.create_check_constraint("ck_graph_merge_candidates_type", "graph_merge_reconcile_candidates", f"candidate_type IN {OLD_TYPES}")
