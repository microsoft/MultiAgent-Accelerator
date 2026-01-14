#!/bin/bash
# Build and push container images to Azure Container Registry

set -e

# Configuration
RESOURCE_GROUP="multiagent-github-test-rg"
ACR_NAME="acrmadev4xfffmgy"
IMAGE_TAG="${1:-latest}"

echo "========================================="
echo "Building and Pushing Multi-Agent Images"
echo "========================================="
echo "Resource Group: $RESOURCE_GROUP"
echo "ACR Name: $ACR_NAME"
echo "Image Tag: $IMAGE_TAG"
echo ""

# Login to ACR
echo "Logging in to ACR..."
az acr login --name $ACR_NAME

# Build and push orchestrator
echo ""
echo "Building orchestrator..."
cd agents/orchestrator
docker build -t $ACR_NAME.azurecr.io/orchestrator:$IMAGE_TAG .
docker push $ACR_NAME.azurecr.io/orchestrator:$IMAGE_TAG
cd ../..

# Build and push data-agent
echo ""
echo "Building data-agent..."
cd agents/data_agent
docker build -t $ACR_NAME.azurecr.io/data-agent:$IMAGE_TAG .
docker push $ACR_NAME.azurecr.io/data-agent:$IMAGE_TAG
cd ../..

echo ""
echo "========================================="
echo "✅ All images built and pushed successfully!"
echo "========================================="
echo ""
echo "Images:"
echo "  - $ACR_NAME.azurecr.io/orchestrator:$IMAGE_TAG"
echo "  - $ACR_NAME.azurecr.io/data-agent:$IMAGE_TAG"
echo ""
echo "Next steps:"
echo "  1. Create Service Bus queues:"
echo "     az servicebus queue create --namespace-name multiagent-test-dev-servicebus --name data-agent-queue --resource-group $RESOURCE_GROUP"
echo ""
echo "  2. Deploy to Kubernetes:"
echo "     kubectl apply -f k8s/"
echo ""
