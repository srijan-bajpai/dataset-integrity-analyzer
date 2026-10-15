#!/usr/bin/env bash
# ==============================================================================
# DIA 2.0 - S3 Backup & Restore Utility for Dataset Storage
# ==============================================================================

set -euo pipefail

ACTION="${1:-backup}"
S3_BUCKET="${2:-${DIA_S3_BUCKET:-}}"
DATA_DIR="${DIA_STORAGE_DIR:-/data}"

if [ -z "$S3_BUCKET" ]; then
    echo "Usage: $0 [backup|restore] <s3-bucket-name-or-uri>"
    echo "Example: $0 backup my-dia-dataset-bucket"
    exit 1
fi

# Clean up s3:// prefix if provided
S3_URI="s3://${S3_BUCKET#s3://}"

case "$ACTION" in
    backup)
        echo "==> Backing up DIA storage ($DATA_DIR) to $S3_URI/dia-storage/..."
        aws s3 sync "$DATA_DIR" "$S3_URI/dia-storage/" --delete --exclude "*.tmp"
        echo "==> Backup completed successfully."
        ;;

    restore)
        echo "==> Restoring DIA storage from $S3_URI/dia-storage/ to $DATA_DIR..."
        mkdir -p "$DATA_DIR"
        aws s3 sync "$S3_URI/dia-storage/" "$DATA_DIR"
        echo "==> Restore completed successfully."
        ;;

    *)
        echo "Unknown action: $ACTION. Use 'backup' or 'restore'."
        exit 1
        ;;
esac
