#!/usr/bin/env bash
# ==============================================================================
# DIA 2.0 - Automated EC2 Production Deployment Script
# Supports: Amazon Linux 2023, Amazon Linux 2, Ubuntu 22.04 / 24.04 LTS
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}   Dataset Integrity Analyzer (DIA) 2.0 - EC2 Setup & Launch   ${NC}"
echo -e "${CYAN}================================================================${NC}"

# Check root privileges
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[ERROR] Please run this script as root or with sudo:${NC}"
  echo "  sudo bash $0"
  exit 1
fi

APP_DIR="/opt/dia"
mkdir -p "$APP_DIR"

# 0. Setup Swap for Free Tier instances (e.g. t2.micro / t3.micro with 1GB RAM)
TOTAL_MEM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}' || echo 4000000)
if [ "$TOTAL_MEM_KB" -lt 3000000 ]; then
    if [ ! -f /swapfile ]; then
        echo -e "${YELLOW}==> Detected Free Tier / low-memory instance (< 3GB RAM). Creating 2GB swap to prevent OOM...${NC}"
        fallocate -l 2G /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=2048
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
        echo -e "${GREEN}2GB swap enabled successfully.${NC}"
    fi
fi

# 1. Detect OS & Install Docker
echo -e "\n${YELLOW}==> [1/6] Installing Docker & Docker Compose...${NC}"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_ID=$ID
else
    OS_ID="unknown"
fi

if ! command -v docker &> /dev/null; then
    case "$OS_ID" in
        amzn)
            dnf update -y || yum update -y
            dnf install -y docker git curl || yum install -y docker git curl
            systemctl enable --now docker
            # Install docker compose plugin
            DOCKER_CONFIG=${DOCKER_CONFIG:-/usr/local/lib/docker}
            mkdir -p $DOCKER_CONFIG/cli-plugins
            curl -sSL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m) -o $DOCKER_CONFIG/cli-plugins/docker-compose
            chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
            ;;
        ubuntu|debian)
            apt-get update -y
            apt-get install -y ca-certificates curl gnupg git
            install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/$OS_ID/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes
            chmod a+r /etc/apt/keyrings/docker.gpg
            echo \
              "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$OS_ID \
              $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
              tee /etc/apt/sources.list.d/docker.list > /dev/null
            apt-get update -y
            apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            systemctl enable --now docker
            ;;
        *)
            echo -e "${RED}Unsupported OS: $OS_ID. Please install Docker manually.${NC}"
            exit 1
            ;;
    esac
else
    echo -e "${GREEN}Docker is already installed.${NC}"
fi

# Add default ec2 user to docker group if present
for USER_NAME in ec2-user ubuntu admin; do
    if id "$USER_NAME" &>/dev/null; then
        usermod -aG docker "$USER_NAME" || true
    fi
done

# 2. Sync Repository Files
echo -e "\n${YELLOW}==> [2/6] Preparing application directory at ${APP_DIR}...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "$SCRIPT_DIR" != "$APP_DIR" ]; then
    echo "Syncing latest application files to $APP_DIR..."
    rm -rf "$APP_DIR/dia" "$APP_DIR/frontend" "$APP_DIR/aws" "$APP_DIR/Dockerfile" "$APP_DIR/entrypoint.sh"
    cp -r "$SCRIPT_DIR"/* "$APP_DIR"/
    cp -r "$SCRIPT_DIR"/.env.example "$APP_DIR"/.env.example 2>/dev/null || true
    cp -r "$SCRIPT_DIR"/.dockerignore "$APP_DIR"/.dockerignore 2>/dev/null || true
fi

# Extra safety: remove any leftover orphaned migrations
rm -f "$APP_DIR"/dia/db/migrations/versions/0003_fingerprint_and_ingestion_metadata.py

cd "$APP_DIR"

# 3. Configure Environment Secrets (.env)
echo -e "\n${YELLOW}==> [3/6] Configuring production environment variables...${NC}"
if [ ! -f .env ]; then
    echo "Generating secure passwords for .env..."
    DB_PASS=$(openssl rand -hex 16)
    DIA_PASS=$(openssl rand -hex 12)
    cat > .env << EOF
DIA_SHARED_PASSWORD=${DIA_PASS}
POSTGRES_DB=dia
POSTGRES_USER=dia
POSTGRES_PASSWORD=${DB_PASS}
PORT=8000
DIA_STORAGE_DIR=/data
DIA_CORS_ORIGINS=*
DIA_MAX_SAMPLES=2000
DIA_MAX_UPLOAD_MB=200
DIA_MAX_EXTRACTED_MB=500
EOF
    echo -e "${GREEN}Created new .env with generated secure credentials.${NC}"
else
    echo -e "${GREEN}Existing .env found; preserving current credentials.${NC}"
fi

# Read passwords for display
DIA_STUDIO_PASS=$(grep '^DIA_SHARED_PASSWORD=' .env | cut -d '=' -f2-)

# 4. Configure Systemd Service for Auto-Restart
echo -e "\n${YELLOW}==> [4/6] Creating systemd service for automatic reboot recovery...${NC}"
cat > /etc/systemd/system/dia.service << EOF
[Unit]
Description=Dataset Integrity Analyzer (DIA) 2.0 Stack
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${APP_DIR}
ExecStart=/usr/bin/docker compose up -d --remove-orphans
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=600

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable dia.service

# 5. Build and Launch Containers
echo -e "\n${YELLOW}==> [5/6] Building and launching DIA Docker containers...${NC}"
docker compose down -v 2>/dev/null || docker compose down || true
docker compose build --no-cache api worker
docker compose up -d

# 6. Verify Health
echo -e "\n${YELLOW}==> [6/6] Verifying system health check...${NC}"
ATTEMPTS=0
MAX_ATTEMPTS=30
HEALTHY=false

while [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    if curl -s http://localhost:8000/health | grep -q '"status":"ok"'; then
        HEALTHY=true
        break
    fi
    echo -n "."
    sleep 2
    ATTEMPTS=$((ATTEMPTS+1))
done

echo ""
if [ "$HEALTHY" = true ]; then
    PUBLIC_IP=$(curl -s http://checkip.amazonaws.com || curl -s https://ifconfig.me || echo "<your-ec2-public-ip>")
    echo -e "\n${GREEN}================================================================${NC}"
    echo -e "${GREEN}   DIA 2.0 IS LIVE AND READY ON AWS!                          ${NC}"
    echo -e "${GREEN}================================================================${NC}"
    echo -e "Web Studio URL : ${CYAN}http://${PUBLIC_IP}:8000${NC}"
    echo -e "Health Check   : ${CYAN}http://${PUBLIC_IP}:8000/health${NC}"
    echo -e "Studio Password: ${YELLOW}${DIA_STUDIO_PASS}${NC}"
    echo -e "Install Dir    : ${APP_DIR}"
    echo -e "\nUseful Commands:"
    echo "  - Check logs  : docker compose logs -f"
    echo "  - Stop stack  : systemctl stop dia"
    echo "  - Start stack : systemctl start dia"
    echo "  - Status      : systemctl status dia"
    echo -e "${GREEN}================================================================${NC}"
else
    echo -e "${RED}[WARNING] Health check timed out. Inspecting container logs:${NC}"
    docker compose logs --tail=40
    exit 1
fi
