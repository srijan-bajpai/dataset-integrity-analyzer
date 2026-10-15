"""
DIA 2.0 Database Models — SQLAlchemy ORM definitions.

Tracks: datasets, samples, attributes, analysis runs, metrics, and findings.
"""

import uuid
import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, Index, create_engine
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy import event
from sqlalchemy.orm import relationship, declarative_base, sessionmaker

Base = declarative_base()


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Dataset(Base):
    """A user-uploaded dataset."""
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    layout = Column(String, default="folder_per_class")  # folder_per_class | manifest
    fingerprint = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
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
    anomaly_flags = Column(JSON, default=list)

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
    analysis_results = relationship("SampleResult", back_populates="sample", cascade="all, delete-orphan")

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
    progress_percent = Column(Integer, default=0, nullable=False)
    status_message = Column(String, default="Queued", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
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
    jobs = relationship("JobQueue", back_populates="run", cascade="all, delete-orphan")
    sample_results = relationship("SampleResult", back_populates="run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_runs_dataset", "dataset_id"),
        Index("ix_runs_status", "status"),
    )


class JobQueue(Base):
    """Database-backed job queue for audit runs."""
    __tablename__ = "job_queue"

    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, unique=True)
    run = relationship("AnalysisRun", back_populates="jobs")
    status = Column(String, default="pending")  # pending | processing | done | failed
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    picked_at = Column(DateTime, nullable=True)
    lease_expires_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    worker_id = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_job_status", "status"),
    )


class SampleResult(Base):
    """Versioned per-sample measurements for a particular analysis run."""
    __tablename__ = "sample_results"

    run_id = Column(String, ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False)
    sample_id = Column(String, ForeignKey("samples.id", ondelete="CASCADE"), nullable=False)
    metrics = Column(JSON, default=dict, nullable=False)

    run = relationship("AnalysisRun", back_populates="sample_results")
    sample = relationship("Sample", back_populates="analysis_results")

    __table_args__ = (
        PrimaryKeyConstraint("run_id", "sample_id", name="pk_sample_results"),
        Index("ix_sample_results_sample", "sample_id"),
    )


def get_engine(database_url: str):
    """Create a SQLAlchemy engine."""
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    engine = create_engine(database_url, connect_args=connect_args, echo=False, pool_pre_ping=True)
    if database_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _enable_sqlite_foreign_keys(connection, _record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    return engine


def get_session_factory(engine):
    """Create a session factory."""
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db(database_url: str):
    """Initialize the database, creating all tables."""
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)
    return engine
