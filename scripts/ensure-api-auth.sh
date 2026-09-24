#!/bin/bash

set -euo pipefail

NAMESPACE="${1:-multiagent}"
SECRET_NAME="${2:-multiagent-api-auth}"

if kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" >/dev/null 2>&1; then
    echo "🔐 Reusing existing shared API authentication secret"
    exit 0
fi

echo "🔐 Creating shared API authentication secret..."
API_KEY_FILE=$(mktemp)
trap 'rm -f "$API_KEY_FILE"' EXIT
chmod 600 "$API_KEY_FILE"
openssl rand -base64 32 > "$API_KEY_FILE"

kubectl create secret generic "$SECRET_NAME" \
    -n "$NAMESPACE" \
    --from-file=api-key="$API_KEY_FILE"
