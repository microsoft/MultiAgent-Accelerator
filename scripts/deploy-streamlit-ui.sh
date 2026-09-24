#!/bin/bash

# Deploy Streamlit UI to AKS
# This script builds, pushes, and deploys the Streamlit web UI

set -e

echo "🎨 Deploying Streamlit UI to AKS..."

# Get ACR name from environment or use default
ACR_NAME=${ACR_NAME:-"acrmadev2jhf6weu"}
ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"

# Check if logged in to ACR
echo "📋 Checking ACR authentication..."
az acr login --name $ACR_NAME 2>/dev/null || {
    echo "❌ Failed to login to ACR. Please run: az acr login --name $ACR_NAME"
    exit 1
}

# Build Docker image
echo "🔨 Building Streamlit UI Docker image..."
cd "$(dirname "$0")/.."
docker build -t ${ACR_LOGIN_SERVER}/streamlit-ui:latest web_ui/

# Push to ACR
echo "📤 Pushing image to ACR..."
docker push ${ACR_LOGIN_SERVER}/streamlit-ui:latest

# Deploy to AKS
echo "🚀 Deploying to AKS..."
if ! kubectl get secret multiagent-api-auth -n multiagent >/dev/null 2>&1; then
    echo "🔐 Creating shared API authentication secret..."
    API_KEY_FILE=$(mktemp)
    trap 'rm -f "$API_KEY_FILE"' EXIT
    chmod 600 "$API_KEY_FILE"
    openssl rand -base64 32 > "$API_KEY_FILE"
    kubectl create secret generic multiagent-api-auth \
        -n multiagent \
        --from-file=api-key="$API_KEY_FILE"
    rm -f "$API_KEY_FILE"
fi
kubectl apply -f k8s/streamlit-ui-deployment.yaml

# Wait for deployment
echo "⏳ Waiting for deployment to complete..."
kubectl rollout status deployment/streamlit-ui -n multiagent --timeout=120s

echo ""
echo "✅ Streamlit UI deployed successfully!"
echo ""
echo "🔒 Streamlit UI service is internal by default."
echo "   Development access:"
echo "   kubectl port-forward -n multiagent svc/streamlit-ui-service 8501:80"
echo ""
echo "   For production, expose the UI only through authenticated ingress,"
echo "   Azure Application Gateway, or API Management."

echo ""
echo "📊 View logs with:"
echo "   kubectl logs -n multiagent -l app=streamlit-ui -f"
