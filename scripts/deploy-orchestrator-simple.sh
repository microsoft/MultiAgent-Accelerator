#!/bin/bash

# Deploy Orchestrator to AKS
# Uses the same managed identity as other agents (multiagent-dev-identity)

set -e

echo "=============================================="
echo "🚀 Deploying Orchestrator to AKS"
echo "=============================================="
echo ""

# Get values
ACR_NAME=$(az acr list --resource-group multiagent-dev-rg --query "[0].name" -o tsv)
SERVICEBUS_NAME=$(az servicebus namespace list --resource-group multiagent-dev-rg --query "[0].name" -o tsv)
SERVICEBUS_NAMESPACE="${SERVICEBUS_NAME}.servicebus.windows.net"
TENANT_ID=$(az account show --query tenantId -o tsv)
CLIENT_ID="9b9ed5f3-a788-425d-ba4f-7f65017856f5"  # multiagent-dev-identity

echo "📋 Configuration:"
echo "   ACR: $ACR_NAME"
echo "   Service Bus: $SERVICEBUS_NAMESPACE"
echo "   Client ID: $CLIENT_ID"
echo "   Tenant ID: $TENANT_ID"
echo ""

# Deploy orchestrator
echo "📦 Deploying orchestrator..."
cat k8s/orchestrator-deployment.yaml | \
  sed "s/\${ACR_NAME}/$ACR_NAME/g" | \
  sed "s/\${SERVICEBUS_NAMESPACE}/$SERVICEBUS_NAMESPACE/g" | \
  sed "s/\${WORKLOAD_IDENTITY_CLIENT_ID}/$CLIENT_ID/g" | \
  sed "s/\${AZURE_TENANT_ID}/$TENANT_ID/g" | \
  kubectl apply -f -

echo ""
echo "✅ Orchestrator deployed!"
echo ""
echo "📊 Checking status..."
kubectl get pods -n multiagent -l app=orchestrator
echo ""
echo "🔍 Get external IP (may take a few minutes):"
echo "   kubectl get svc orchestrator-service -n multiagent"
echo ""
echo "📝 View logs:"
echo "   kubectl logs -n multiagent -l app=orchestrator --tail=50 -f"
