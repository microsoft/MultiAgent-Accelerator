#!/bin/bash

set -euo pipefail

RG_NAME="${1:?resource group is required}"
SERVICEBUS_NAME="${2:?service bus namespace is required}"
QUEUE_NAME="${3:-agent-responses}"

if ! az servicebus queue show \
    --namespace-name "$SERVICEBUS_NAME" \
    --resource-group "$RG_NAME" \
    --name "$QUEUE_NAME" >/dev/null 2>&1; then
    exit 0
fi

REQUIRES_SESSION=$(az servicebus queue show \
    --namespace-name "$SERVICEBUS_NAME" \
    --resource-group "$RG_NAME" \
    --name "$QUEUE_NAME" \
    --query requiresSession -o tsv)

if [ "$REQUIRES_SESSION" != "true" ]; then
    echo "❌ Service Bus queue '$QUEUE_NAME' exists without sessions enabled."
    echo "   Async response isolation requires a session-enabled '$QUEUE_NAME' queue."
    echo "   Drain or back up pending responses, delete the queue, then recreate it with:"
    echo "   az servicebus queue delete --namespace-name '$SERVICEBUS_NAME' --resource-group '$RG_NAME' --name '$QUEUE_NAME'"
    echo "   az servicebus queue create --namespace-name '$SERVICEBUS_NAME' --resource-group '$RG_NAME' --name '$QUEUE_NAME' --requires-session true"
    exit 1
fi

echo "✅ Service Bus queue '$QUEUE_NAME' has sessions enabled"
