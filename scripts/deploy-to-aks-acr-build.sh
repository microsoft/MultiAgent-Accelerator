#!/bin/bash
set -e

echo "🚀 Starting deployment to AKS (using ACR Build)..."

# Configuration
RESOURCE_GROUP="multiagent-dev-rg"

# Auto-detect resource names
echo "🔍 Detecting Azure resources..."
ACR_NAME=$(az acr list -g $RESOURCE_GROUP --query '[0].name' -o tsv)
AKS_NAME=$(az aks list -g $RESOURCE_GROUP --query '[0].name' -o tsv)
OPENAI_NAME=$(az cognitiveservices account list -g $RESOURCE_GROUP --query "[?kind=='OpenAI'].name" -o tsv)

if [ -z "$ACR_NAME" ] || [ -z "$AKS_NAME" ] || [ -z "$OPENAI_NAME" ]; then
    echo "❌ Error: Could not find required resources in $RESOURCE_GROUP"
    exit 1
fi

echo "📝 Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  ACR: $ACR_NAME"
echo "  AKS: $AKS_NAME"
echo "  OpenAI: $OPENAI_NAME"

# Build and push images using ACR Build
echo ""
echo "🏗️  Building Currency MCP in ACR..."
az acr build \
  --registry $ACR_NAME \
  --image currency-mcp:latest \
  --file mcp_servers/currency_mcp/Dockerfile \
  mcp_servers/currency_mcp

echo ""
echo "🏗️  Building Activity MCP in ACR..."
az acr build \
  --registry $ACR_NAME \
  --image activity-mcp:latest \
  --file mcp_servers/activity_mcp/Dockerfile \
  mcp_servers/activity_mcp

echo ""
echo "🏗️  Building Travel Agent in ACR..."
az acr build \
  --registry $ACR_NAME \
  --image travel-agent:latest \
  --file agents/travel_agent/Dockerfile \
  agents/travel_agent

# Get AKS credentials
echo ""
echo "🔑 Getting AKS credentials..."
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_NAME --overwrite-existing

# Get Workload Identity details
echo ""
echo "🔐 Getting Workload Identity credentials..."
WORKLOAD_IDENTITY_CLIENT_ID=$(az identity show -g $RESOURCE_GROUP -n multiagent-dev-identity --query clientId -o tsv)
AZURE_TENANT_ID=$(az account show --query tenantId -o tsv)

if [ -z "$WORKLOAD_IDENTITY_CLIENT_ID" ]; then
    echo "❌ Error: Could not find Workload Identity. Make sure it was created."
    exit 1
fi

echo "  Client ID: $WORKLOAD_IDENTITY_CLIENT_ID"
echo "  Tenant ID: $AZURE_TENANT_ID"

# Create namespace and service account
echo ""
echo "📦 Creating namespace and service account..."
kubectl apply -f k8s/namespace-and-sa.yaml

"$(dirname "$0")/ensure-api-auth.sh" multiagent

# Deploy Currency MCP
echo ""
echo "🚀 Deploying Currency MCP..."
cat k8s/currency-mcp-deployment.yaml | \
  sed "s/\${ACR_NAME}/$ACR_NAME/g" | \
  kubectl apply -f -

# Deploy Activity MCP
echo ""
echo "🚀 Deploying Activity MCP..."
cat k8s/activity-mcp-deployment.yaml | \
  sed "s/\${ACR_NAME}/$ACR_NAME/g" | \
  kubectl apply -f -

# Deploy Travel Agent
echo ""
echo "🚀 Deploying Travel Agent..."
cat k8s/travel-agent-deployment.yaml | \
  sed "s/\${ACR_NAME}/$ACR_NAME/g" | \
  sed "s/\${OPENAI_NAME}/$OPENAI_NAME/g" | \
  sed "s/\${WORKLOAD_IDENTITY_CLIENT_ID}/$WORKLOAD_IDENTITY_CLIENT_ID/g" | \
  sed "s/\${AZURE_TENANT_ID}/$AZURE_TENANT_ID/g" | \
  kubectl apply -f -

kubectl apply -f k8s/network-policies.yaml

# Wait for pods to be ready
echo ""
echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=currency-mcp -n multiagent --timeout=300s || true
kubectl wait --for=condition=ready pod -l app=activity-mcp -n multiagent --timeout=300s || true
kubectl wait --for=condition=ready pod -l app=travel-agent -n multiagent --timeout=300s || true

# Get pod status
echo ""
echo "📊 Pod Status:"
kubectl get pods -n multiagent

# Get services
echo ""
echo "🌐 Services:"
kubectl get services -n multiagent

# Show secure access instructions
echo ""
echo "🎉 Deployment complete!"
echo ""
echo "🔒 Services are internal ClusterIP services."
echo "Test your Travel Agent:"
echo "  kubectl port-forward -n multiagent svc/travel-agent-service 8080:80"
echo "  API_KEY=\$(kubectl get secret multiagent-api-auth -n multiagent -o jsonpath='{.data.api-key}' | base64 -d)"
echo "  curl -X POST http://localhost:8080/task \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -H \"X-API-Key: \$API_KEY\" \\"
echo "    -H \"X-User-ID: test-user\" \\"
echo "    -d '{\"task\": \"What is the exchange rate from USD to EUR?\"}'"
