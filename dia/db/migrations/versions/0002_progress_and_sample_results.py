"""Add durable progress and per-sample metrics for analysis runs."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0002_progress_and_sample_results"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if "analysis_runs" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("analysis_runs")}
        with op.batch_alter_table("analysis_runs") as batch:
            if "progress_percent" not in columns:
                batch.add_column(sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"))
            if "status_message" not in columns:
                batch.add_column(sa.Column("status_message", sa.String(), nullable=False, server_default="Queued"))
    if "sample_results" not in inspector.get_table_names():
        op.create_table(
            "sample_results",
            sa.Column("run_id", sa.String(), nullable=False),
            sa.Column("sample_id", sa.String(), nullable=False),
            sa.Column("metrics", sa.JSON(), nullable=False),
            sa.PrimaryKeyConstraint("run_id", "sample_id", name="pk_sample_results"),
            sa.ForeignKeyConstraint(["run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["sample_id"], ["samples.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_sample_results_sample", "sample_results", ["sample_id"])


def downgrade():
    if "sample_results" in inspect(op.get_bind()).get_table_names():
        op.drop_index("ix_sample_results_sample", table_name="sample_results")
        op.drop_table("sample_results")
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("analysis_runs")}
    with op.batch_alter_table("analysis_runs") as batch:
        if "status_message" in columns:
            batch.drop_column("status_message")
        if "progress_percent" in columns:
            batch.drop_column("progress_percent")
