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
kubectl apply -f k8s/streamlit-ui-deployment.yaml

# Wait for deployment
echo "⏳ Waiting for deployment to complete..."
kubectl rollout status deployment/streamlit-ui -n multiagent --timeout=120s

# Get external IP
echo ""
echo "✅ Streamlit UI deployed successfully!"
echo ""
echo "🌐 Getting external IP address..."
echo "   (This may take a few minutes for LoadBalancer to provision)"
echo ""

# Wait for external IP
for i in {1..30}; do
    EXTERNAL_IP=$(kubectl get svc streamlit-ui-service -n multiagent -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
    if [ -n "$EXTERNAL_IP" ]; then
        echo "✅ Streamlit UI is available at: http://${EXTERNAL_IP}"
        echo ""
        echo "📝 You can now:"
        echo "   1. Open http://${EXTERNAL_IP} in your browser"
        echo "   2. View discovered agents"
        echo "   3. Submit tasks (sync/async)"
        echo "   4. Monitor your multi-agent system"
        break
    fi
    echo "   Waiting for external IP... (attempt $i/30)"
    sleep 5
done

if [ -z "$EXTERNAL_IP" ]; then
    echo "⚠️  External IP not yet assigned. Check status with:"
    echo "   kubectl get svc streamlit-ui-service -n multiagent"
fi

echo ""
echo "📊 View logs with:"
echo "   kubectl logs -n multiagent -l app=streamlit-ui -f"
