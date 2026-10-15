"""
DIA 2.0 Database Models — SQLAlchemy ORM definitions.

Tracks: datasets, samples, attributes, analysis runs, metrics, and findings.
"""

import uuid
import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, Index, create_engine
from sqlalchemy.orm import relationship, declarative_base, sessionmaker

Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Dataset(Base):
    """A user-uploaded dataset."""
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    layout = Column(String, default="folder_per_class")  # folder_per_class | manifest
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    sample_count = Column(Integer, default=0)
    class_count = Column(Integer, default=0)
    classes = Column(JSON, default=list)  # list of class names
    storage_path = Column(String, nullable=False)  # path to extracted dataset
    zip_path = Column(String, nullable=True)  # original upload path
    status = Column(String, default="uploaded", nullable=False)  # uploaded | ingested | error

    samples = relationship("Sample", back_populates="dataset", cascade="all, delete-orphan")
    runs = relationship("AnalysisRun", back_populates="dataset", cascade="all, delete-orphan")


class Sample(Base):
    """A single image in a dataset."""
    __tablename__ = "samples"

    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_id = Column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    sample_ref = Column(String, nullable=False)  # stable relative path
    file_path = Column(String, nullable=False)  # absolute path on disk
    ground_truth_class = Column(String, nullable=True)
    split = Column(String, default="unspecified")
    content_sha256 = Column(String, nullable=True)

    # Metadata / attributes (from manifest or inferred)
    attributes = Column(JSON, default=dict)  # user-supplied attributes
    inferred_attributes = Column(JSON, default=dict)  # opt-in model suggestions

    # Quality metrics (filled by analyzers)
    quality_blur = Column(Float, nullable=True)
    quality_brightness = Column(Float, nullable=True)
    quality_contrast = Column(Float, nullable=True)
    quality_resolution = Column(Integer, nullable=True)
    quality_aspect_ratio = Column(Float, nullable=True)
    flag_blurred = Column(Boolean, default=False)
    flag_underexposed = Column(Boolean, default=False)
    flag_overexposed = Column(Boolean, default=False)
    flag_low_contrast = Column(Boolean, default=False)

    # Duplicate detection
    phash = Column(String, nullable=True)
    duplicate_group = Column(Integer, nullable=True)

    # Diversity
    cluster_id = Column(Integer, nullable=True)

    # Label integrity
    label_issue_prob = Column(Float, default=0.0)
    flag_suspected_mislabel = Column(Boolean, default=False)
    predicted_class = Column(String, nullable=True)

    # Embedding reference
    embedding_index = Column(Integer, nullable=True)

    # Status
    is_valid = Column(Boolean, default=True)
    error_message = Column(String, nullable=True)

    dataset = relationship("Dataset", back_populates="samples")

    __table_args__ = (
        Index("ix_samples_dataset", "dataset_id"),
        Index("ix_samples_class", "ground_truth_class"),
        Index("ix_samples_dataset_ref", "dataset_id", "sample_ref", unique=True),
    )


class AnalysisRun(Base):
    """A single audit execution against a dataset."""
    __tablename__ = "analysis_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_id = Column(String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="queued")  # queued | running | completed | failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Configuration
    config = Column(JSON, default=dict)  # fairness targets and analysis options
    analyzer_versions = Column(JSON, default=dict)

    # Results
    report = Column(JSON, nullable=True)  # full JSON report
    metrics = Column(JSON, nullable=True)  # dimension scores, overall score
    findings = Column(JSON, nullable=True)  # flagged samples, recommendations

    # Metadata
    embeddings_path = Column(String, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    dataset = relationship("Dataset", back_populates="runs")

    __table_args__ = (
        Index("ix_runs_dataset", "dataset_id"),
        Index("ix_runs_status", "status"),
    )


class JobQueue(Base):
    """Database-backed job queue for audit runs."""
    __tablename__ = "job_queue"

    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, unique=True)
    status = Column(String, default="pending")  # pending | processing | done | failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    picked_at = Column(DateTime, nullable=True)
    lease_expires_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    worker_id = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_job_status", "status"),
    )


def get_engine(database_url: str):
    """Create a SQLAlchemy engine."""
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(database_url, connect_args=connect_args, echo=False)


def get_session_factory(engine):
    """Create a session factory."""
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db(database_url: str):
    """Initialize the database, creating all tables."""
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)
    return engine
