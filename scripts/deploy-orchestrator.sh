#!/bin/bash

# Deploy Orchestrator to AKS
# This script builds, pushes, and deploys the orchestrator with Service Bus integration

set -e

echo "=============================================="
echo "🚀 Deploying Orchestrator to AKS"
echo "=============================================="
echo ""

# Configuration
RG_NAME="multiagent-dev-rg"
AKS_NAME="multiagent-dev-aks"
ACR_NAME=$(az acr list --resource-group $RG_NAME --query "[0].name" -o tsv)
SERVICEBUS_NAME=$(az servicebus namespace list --resource-group $RG_NAME --query "[?contains(name, 'multiagent')].name" -o tsv | head -1)
TENANT_ID=$(az account show --query tenantId -o tsv)

echo "📋 Configuration:"
echo "   Resource Group: $RG_NAME"
echo "   AKS Cluster: $AKS_NAME"
echo "   ACR: $ACR_NAME"
echo "   Service Bus: $SERVICEBUS_NAME"
echo ""

# Get AKS credentials
echo "🔑 Getting AKS credentials..."
az aks get-credentials --resource-group $RG_NAME --name $AKS_NAME --overwrite-existing
echo ""

# Create namespace if it doesn't exist
echo "📦 Creating namespace..."
kubectl create namespace multiagent --dry-run=client -o yaml | kubectl apply -f -
echo ""

# Create or get managed identity for orchestrator
echo "🆔 Setting up Managed Identity..."
IDENTITY_NAME="orchestrator-identity"

if az identity show --name $IDENTITY_NAME --resource-group $RG_NAME &>/dev/null; then
    echo "   ✅ Identity already exists"
else
    echo "   Creating identity..."
    az identity create --name $IDENTITY_NAME --resource-group $RG_NAME --location $(az group show -n $RG_NAME --query location -o tsv)
    sleep 10  # Wait for identity to be ready
fi

IDENTITY_CLIENT_ID=$(az identity show --name $IDENTITY_NAME --resource-group $RG_NAME --query clientId -o tsv)
IDENTITY_RESOURCE_ID=$(az identity show --name $IDENTITY_NAME --resource-group $RG_NAME --query id -o tsv)

echo "   Client ID: $IDENTITY_CLIENT_ID"
echo ""

# Grant Service Bus permissions to the identity
echo "🔐 Granting Service Bus permissions..."
SERVICEBUS_ID=$(az servicebus namespace show --name $SERVICEBUS_NAME --resource-group $RG_NAME --query id -o tsv)

# Check if role assignment exists
if az role assignment list --assignee $IDENTITY_CLIENT_ID --scope $SERVICEBUS_ID --query "[?roleDefinitionName=='Azure Service Bus Data Owner']" -o tsv | grep -q .; then
    echo "   ✅ Role already assigned"
else
    echo "   Assigning Azure Service Bus Data Owner role..."
    az role assignment create \
        --assignee $IDENTITY_CLIENT_ID \
        --role "Azure Service Bus Data Owner" \
        --scope $SERVICEBUS_ID
    echo "   ✅ Role assigned"
fi
echo ""

# Setup federated credential for Workload Identity
echo "🔗 Setting up Workload Identity federation..."
OIDC_ISSUER=$(az aks show --name $AKS_NAME --resource-group $RG_NAME --query oidcIssuerProfile.issuerUrl -o tsv)
FEDERATED_CRED_NAME="orchestrator-federated-credential"

if az identity federated-credential show \
    --name $FEDERATED_CRED_NAME \
    --identity-name $IDENTITY_NAME \
    --resource-group $RG_NAME &>/dev/null; then
    echo "   ✅ Federated credential already exists"
else
    echo "   Creating federated credential..."
    az identity federated-credential create \
        --name $FEDERATED_CRED_NAME \
        --identity-name $IDENTITY_NAME \
        --resource-group $RG_NAME \
        --issuer $OIDC_ISSUER \
        --subject system:serviceaccount:multiagent:orchestrator-sa \
        --audience api://AzureADTokenExchange
    echo "   ✅ Federated credential created"
fi
echo ""

# Build and push Docker image
echo "🐳 Building Docker image..."
docker build -t $ACR_NAME.azurecr.io/orchestrator:latest agents/orchestrator
echo ""

echo "📤 Pushing to ACR..."
docker push $ACR_NAME.azurecr.io/orchestrator:latest
echo ""

# Apply Kubernetes manifests
echo "☸️  Deploying to Kubernetes..."

# Substitute variables in the deployment file
cat k8s/orchestrator-deployment.yaml | \
    sed "s/\${ACR_NAME}/$ACR_NAME/g" | \
    sed "s/\${WORKLOAD_IDENTITY_CLIENT_ID}/$IDENTITY_CLIENT_ID/g" | \
    sed "s/\${AZURE_TENANT_ID}/$TENANT_ID/g" | \
    kubectl apply -f -

echo ""
echo "⏳ Waiting for deployment to be ready..."
kubectl rollout status deployment/orchestrator -n multiagent --timeout=300s
echo ""

echo "=============================================="
echo "✅ Deployment Complete!"
echo "=============================================="
echo ""
echo "📊 Check status:"
echo "   kubectl get pods -n multiagent -l app=orchestrator"
echo "   kubectl logs -n multiagent -l app=orchestrator --tail=50"
echo ""
echo "🧪 Test the orchestrator:"
echo "   kubectl port-forward -n multiagent svc/orchestrator-service 8000:8000"
echo ""
echo "   Then in another terminal:"
echo "   curl -X POST http://localhost:8000/task \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"task\": \"What is 100 USD in EUR?\"}'"
echo ""
echo "📬 Test Service Bus integration:"
echo "   curl -X POST http://localhost:8000/task/async \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"task\": \"Find restaurants in Paris\"}'"
echo ""
echo "=============================================="
