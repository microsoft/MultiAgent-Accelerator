#!/bin/bash
# View async responses from Service Bus using a Kubernetes Job

set -e

echo "🔍 Deploying response viewer job..."

# Get configuration
SERVICEBUS_NAMESPACE=$(az servicebus namespace list --resource-group multiagent-dev-rg --query "[0].serviceBusEndpoint" -o tsv | sed 's|https://||' | sed 's|:443/||')
WORKLOAD_IDENTITY_CLIENT_ID="9b9ed5f3-a788-425d-ba4f-7f65017856f5"
AZURE_TENANT_ID=$(az account show --query tenantId -o tsv)

echo "Service Bus: $SERVICEBUS_NAMESPACE"
echo "Client ID: $WORKLOAD_IDENTITY_CLIENT_ID"

# Delete previous job if exists
kubectl delete job view-responses -n multiagent 2>/dev/null || true

# Deploy job with variable substitution
cat k8s/response-viewer-job.yaml | \
  sed "s|\${SERVICEBUS_NAMESPACE}|$SERVICEBUS_NAMESPACE|g" | \
  sed "s|\${WORKLOAD_IDENTITY_CLIENT_ID}|$WORKLOAD_IDENTITY_CLIENT_ID|g" | \
  sed "s|\${AZURE_TENANT_ID}|$AZURE_TENANT_ID|g" | \
  kubectl apply -f -

echo ""
echo "⏳ Waiting for job to complete..."
kubectl wait --for=condition=complete --timeout=120s job/view-responses -n multiagent 2>/dev/null || true

echo ""
echo "📋 Job logs:"
echo "================================================================"
kubectl logs -n multiagent job/view-responses --tail=100
echo "================================================================"

echo ""
echo "✅ Done! Check the logs above for the responses."
