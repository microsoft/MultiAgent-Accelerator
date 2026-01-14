#!/bin/bash
# Deploy Multi-Agent System with MCP Servers to AKS

set -e

echo "🚀 Starting deployment to AKS..."

# Get configuration from infrastructure outputs or environment
RESOURCE_GROUP="${RESOURCE_GROUP:-multiagent-dev-rg}"
ACR_NAME="${ACR_NAME:-$(az acr list -g $RESOURCE_GROUP --query '[0].name' -o tsv)}"
AKS_NAME="${AKS_NAME:-$(az aks list -g $RESOURCE_GROUP --query '[0].name' -o tsv)}"
OPENAI_NAME="${OPENAI_NAME:-$(az cognitiveservices account list -g $RESOURCE_GROUP --query "[?kind=='OpenAI'].name" -o tsv)}"

echo "📝 Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  ACR: $ACR_NAME"
echo "  AKS: $AKS_NAME"
echo "  OpenAI: $OPENAI_NAME"

# Step 1: Login to ACR
echo ""
echo "🔐 Logging in to Azure Container Registry..."
az acr login --name $ACR_NAME

# Step 2: Build and push Docker images
echo ""
echo "🏗️  Building and pushing Docker images..."

# Currency MCP Server
echo "  Building currency-mcp..."
docker build -t $ACR_NAME.azurecr.io/currency-mcp:latest ./mcp_servers/currency_mcp
docker push $ACR_NAME.azurecr.io/currency-mcp:latest

# Activity MCP Server
echo "  Building activity-mcp..."
docker build -t $ACR_NAME.azurecr.io/activity-mcp:latest ./mcp_servers/activity_mcp
docker push $ACR_NAME.azurecr.io/activity-mcp:latest

# Travel Agent
echo "  Building travel-agent..."
docker build -t $ACR_NAME.azurecr.io/travel-agent:latest ./agents/travel_agent
docker push $ACR_NAME.azurecr.io/travel-agent:latest

echo "✅ All images built and pushed successfully"

# Step 3: Get AKS credentials
echo ""
echo "🔑 Getting AKS credentials..."
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_NAME --overwrite-existing

# Step 4: Get Workload Identity details
echo ""
echo "🆔 Getting Workload Identity configuration..."
WORKLOAD_IDENTITY_CLIENT_ID=$(az identity show -g $RESOURCE_GROUP -n multiagent-dev-identity --query clientId -o tsv)
AZURE_TENANT_ID=$(az account show --query tenantId -o tsv)

echo "  Workload Identity Client ID: $WORKLOAD_IDENTITY_CLIENT_ID"
echo "  Azure Tenant ID: $AZURE_TENANT_ID"

# Step 5: Create namespace and service account if not exists
echo ""
echo "📦 Setting up Kubernetes namespace and service account..."
cat k8s/namespace-and-sa.yaml | \
    sed "s/REPLACE_WITH_MANAGED_IDENTITY_CLIENT_ID/$WORKLOAD_IDENTITY_CLIENT_ID/g" | \
    kubectl apply -f -

# Step 6: Deploy services with environment substitution
echo ""
echo "🚢 Deploying services to AKS..."

# Function to deploy with variable substitution
deploy_manifest() {
    local manifest=$1
    echo "  Deploying $manifest..."
    cat $manifest | \
        sed "s/\${ACR_NAME}/$ACR_NAME/g" | \
        sed "s/\${OPENAI_NAME}/$OPENAI_NAME/g" | \
        sed "s/\${WORKLOAD_IDENTITY_CLIENT_ID}/$WORKLOAD_IDENTITY_CLIENT_ID/g" | \
        sed "s/\${AZURE_TENANT_ID}/$AZURE_TENANT_ID/g" | \
        kubectl apply -f -
}

# Deploy MCP servers
deploy_manifest k8s/currency-mcp-deployment.yaml
deploy_manifest k8s/activity-mcp-deployment.yaml

# Deploy Travel Agent
deploy_manifest k8s/travel-agent-deployment.yaml

echo ""
echo "✅ Deployment complete!"

# Step 7: Wait for pods to be ready
echo ""
echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l component=mcp-server -n multiagent --timeout=300s || true
kubectl wait --for=condition=ready pod -l component=agent -n multiagent --timeout=300s || true

# Step 8: Get service information
echo ""
echo "📊 Deployment Status:"
echo ""
kubectl get pods -n multiagent
echo ""
kubectl get services -n multiagent

# Step 9: Get Travel Agent external IP
echo ""
echo "🌐 Getting Travel Agent external IP (this may take a few minutes)..."
EXTERNAL_IP=""
for i in {1..30}; do
    EXTERNAL_IP=$(kubectl get service travel-agent-service -n multiagent -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [ -n "$EXTERNAL_IP" ]; then
        break
    fi
    echo "   Waiting for external IP... ($i/30)"
    sleep 10
done

if [ -n "$EXTERNAL_IP" ]; then
    echo ""
    echo "✅ Travel Agent is accessible at: http://$EXTERNAL_IP"
    echo ""
    echo "Test with:"
    echo "  curl -X POST http://$EXTERNAL_IP/task \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"task\": \"What is the exchange rate from USD to EUR?\"}'"
else
    echo ""
    echo "⚠️  External IP not yet assigned. Check later with:"
    echo "   kubectl get service travel-agent-service -n multiagent"
fi

echo ""
echo "🎉 Deployment script completed!"
