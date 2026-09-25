#!/bin/bash

set -euo pipefail

NAMESPACE="${1:-multiagent}"
SECRET_NAME="${2:-multiagent-api-auth}"
TEMP_FILES=()

cleanup() {
    for temp_file in "${TEMP_FILES[@]}"; do
        rm -f "$temp_file"
    done
}

trap cleanup EXIT

create_secret() {
    echo "🔐 Creating shared API authentication secret..."
    API_KEY_FILE=$(mktemp)
    TEMP_FILES+=("$API_KEY_FILE")
    chmod 600 "$API_KEY_FILE"
    openssl rand -base64 32 | tr -d '\n' > "$API_KEY_FILE"

    kubectl create secret generic "$SECRET_NAME" \
        -n "$NAMESPACE" \
        --from-file=api-key="$API_KEY_FILE"
}

restart_secret_consumers() {
    for deployment in orchestrator travel-agent streamlit-ui; do
        if kubectl get deployment "$deployment" -n "$NAMESPACE" >/dev/null 2>&1; then
            kubectl rollout restart deployment/"$deployment" -n "$NAMESPACE"
        fi
    done
}

if kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" >/dev/null 2>&1; then
    EXISTING_KEY_FILE=$(mktemp)
    SANITIZED_KEY_FILE=$(mktemp)
    TEMP_FILES+=("$EXISTING_KEY_FILE" "$SANITIZED_KEY_FILE")

    if [ ! -s "$EXISTING_KEY_FILE" ] || ! cmp -s "$EXISTING_KEY_FILE" "$SANITIZED_KEY_FILE"; then
        echo "🔐 Existing shared API authentication secret contains newline characters; rotating it..."
        kubectl delete secret "$SECRET_NAME" -n "$NAMESPACE"
        create_secret
        restart_secret_consumers
        exit 0
    fi

    echo "🔐 Reusing existing shared API authentication secret"
    exit 0
fi

create_secret
