"""Persist dataset fingerprints and filename-derived/sample anomaly metadata."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0003_fingerprint_and_ingestion_metadata"
down_revision = "0002_progress_and_sample_results"
branch_labels = None
depends_on = None


def upgrade():
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "datasets" in tables:
        columns = {column["name"] for column in inspector.get_columns("datasets")}
        with op.batch_alter_table("datasets") as batch:
            if "fingerprint" not in columns:
                batch.add_column(sa.Column("fingerprint", sa.String(), nullable=True))
        if "fingerprint" not in columns:
            op.create_index("ix_datasets_fingerprint", "datasets", ["fingerprint"], unique=False)
    if "samples" in tables:
        columns = {column["name"] for column in inspector.get_columns("samples")}
        if "inferred_attributes" not in columns:
            with op.batch_alter_table("samples") as batch:
                batch.add_column(sa.Column("inferred_attributes", sa.JSON(), nullable=True))
        if "anomaly_flags" not in columns:
            with op.batch_alter_table("samples") as batch:
                batch.add_column(sa.Column("anomaly_flags", sa.JSON(), nullable=True))


def downgrade():
    inspector = inspect(op.get_bind())
    if "datasets" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("datasets")}
        if "fingerprint" in columns:
            op.drop_index("ix_datasets_fingerprint", table_name="datasets")
            with op.batch_alter_table("datasets") as batch:
                batch.drop_column("fingerprint")
    if "samples" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("samples")}
        with op.batch_alter_table("samples") as batch:
            if "anomaly_flags" in columns:
                batch.drop_column("anomaly_flags")
            if "inferred_attributes" in columns:
                batch.drop_column("inferred_attributes")
