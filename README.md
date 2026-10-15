# Dataset Integrity Analyzer (DIA) 2.0

DIA 2.0 is an enterprise-grade full-stack platform for auditing image-classification datasets before model training. It seamlessly integrates a modern React Web Studio frontend with a high-performance Python FastAPI backend, PostgreSQL database, and asynchronous audit worker pipeline.

Accepting ZIP uploads containing class folders or CSV/JSONL manifests, DIA performs deep audits across 6 core integrity dimensions, stores reproducible analysis runs, and presents machine-readable evidence alongside interactive 3D visualizations and layperson-friendly ELI5 explanations.

---

## What It Audits & Delivers

- **6 Core Integrity Dimensions**:
  1. **Balance & Representation**: Class skew, group representation, operator-provided targets, confidence intervals, and split skew.
  2. **Image Quality & Defect Scan**: Blur, brightness, contrast, noise, resolution, aspect ratio, and corrupt files.
  3. **Near-Duplicates & Train/Test Leakage**: Perceptual hashing (pHash) and exact duplicate detection, highlighting cross-split contamination.
  4. **Visual Diversity & 3D Clusters**: High-dimensional embedding projections (PCA/Three.js) revealing visual clusters and isolated visual outliers.
  5. **Label Integrity & Suspected Mislabels**: Cross-validated label-disagreement signals identifying noisy annotations.
  6. **Unified Health Scoring & What-If Simulator**: Holistic 0–100 readiness scoring with live scenario simulation to test the score impact of proposed data cleanups.
- **Dual Audience Telemetry**: Instant toggle between **Layman / Simple Mode** (ELI5 plain-English summaries, intuitive health gauges, and non-tech translations) and **Engineering Mode** (lossless metrics, p-values, logits, and Hamming distances).
- **1-Click Compliance Exports**: Standalone executive HTML reports, Gebru et al. Datasheets for Datasets (Markdown/JSON), and CSV remediation manifests.

---

## Live Web Studio & Local Development

### 1. Run Everything Locally (Unified Mode)

#### Backend Setup
```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1 | Linux/macOS: source .venv/bin/activate
pip install -r requirements-v2.txt
alembic upgrade head
```

#### Frontend Setup & Build
```bash
cd frontend
npm install
npm run build
cd ..
```

#### Launch DIA
```bash
python -m uvicorn dia.api.main:app --port 8000
# In a second terminal (for async audit jobs):
python -m dia.worker
```

Open `http://localhost:8000` in your browser. The FastAPI backend automatically serves the integrated React Web Studio!

---

## Docker Compose Quickstart

For local container testing or single-server deployment:

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Launch PostgreSQL, API, and Worker containers
docker compose up --build
```

- **Web Studio**: `http://localhost:8000`
- **Interactive OpenAPI Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

---

## AWS Cloud Deployment

DIA 2.0 is fully **AWS Ready** with multiple zero-friction deployment pathways:

| Deployment Path | Description | Documentation |
| :--- | :--- | :--- |
| **AWS EC2 (1-Command Script)** | Production setup on Amazon Linux 2023 or Ubuntu with Docker, automated SSL, and systemd auto-restart. | [AWS Deployment Guide](docs/AWS_DEPLOYMENT_GUIDE.md#3-option-a-automated-amazon-ec2-deployment-recommended) |
| **AWS ECS Fargate + RDS + EFS** | Enterprise serverless architecture with CloudFormation (`aws/cloudformation.yaml`), Application Load Balancer, and encrypted shared storage. | [AWS Deployment Guide](docs/AWS_DEPLOYMENT_GUIDE.md#4-option-b-enterprise-serverless-aws-ecs-fargate--rds--efs) |
| **AWS App Runner** | Managed single-container serverless deployment. | [AWS Deployment Guide](docs/AWS_DEPLOYMENT_GUIDE.md) |
| **Amazon S3 Storage Sync** | Automated dataset backup and disaster recovery utility (`aws/s3-sync.sh`). | [AWS Deployment Guide](docs/AWS_DEPLOYMENT_GUIDE.md#6-s3-dataset-sync--disaster-recovery) |

---

## Testing & Quality Assurance

Run the comprehensive test suite (39 backend integrity tests):

```bash
pytest -q
```

To run end-to-end smoke tests using included sample datasets, follow the [Testing Guide](docs/TESTING_GUIDE.md).
