#!/bin/bash
# Add GCP Agent to AKS Orchestrator Discovery

set -e

# Get GCP agent URL from user
read -p "Enter your GCP agent URL (e.g., https://your-service.run.app): " GCP_AGENT_URL

if [ -z "$GCP_AGENT_URL" ]; then
    echo "❌ GCP agent URL is required"
    exit 1
fi

# Ensure URL ends with /.well-known/agent.json
if [[ ! "$GCP_AGENT_URL" == *"/.well-known/agent.json" ]]; then
    GCP_AGENT_URL="$GCP_AGENT_URL/.well-known/agent.json"
fi

echo "🔍 Testing GCP agent discovery..."
if ! curl -sf "$GCP_AGENT_URL" > /dev/null; then
    echo "❌ Cannot reach GCP agent at $GCP_AGENT_URL"
    echo "   Please verify the URL is correct and publicly accessible"
    exit 1
fi

echo "✅ GCP agent is accessible"
echo ""

# Get agent name
AGENT_NAME=$(curl -s "$GCP_AGENT_URL" | jq -r '.name')
echo "Agent Name: $AGENT_NAME"
echo ""

# Get current orchestrator endpoints
echo "📋 Current agent endpoints in orchestrator:"
CURRENT_ENDPOINTS=$(kubectl get deployment orchestrator -n multiagent -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="AGENT_ENDPOINTS")].value}')
echo "$CURRENT_ENDPOINTS"
echo ""

# Add GCP agent to list
if [[ "$CURRENT_ENDPOINTS" == *"$GCP_AGENT_URL"* ]]; then
    echo "⚠️  GCP agent already configured in orchestrator"
    exit 0
fi

NEW_ENDPOINTS="$CURRENT_ENDPOINTS,$GCP_AGENT_URL"

# Update orchestrator
echo "🚀 Updating orchestrator to include GCP agent..."
kubectl set env deployment/orchestrator \
    -n multiagent \
    AGENT_ENDPOINTS="$NEW_ENDPOINTS"

echo ""
echo "⏳ Waiting for orchestrator to restart..."
kubectl rollout status deployment/orchestrator -n multiagent

echo ""
echo "✅ Orchestrator updated successfully!"
echo ""

echo "🧪 To test agent discovery via orchestrator, use a local port-forward:"
echo "   kubectl port-forward -n multiagent svc/orchestrator-service 8000:80"
echo "   API_KEY=\$(kubectl get secret multiagent-api-auth -n multiagent -o jsonpath='{.data.api-key}' | base64 -d)"
echo "   curl -s -H \"X-API-Key: \$API_KEY\" http://localhost:8000/agents | jq ."

echo ""
echo "================================================"
echo "✅ GCP Agent Integration Complete!"
echo "================================================"
echo ""
echo "Test the multi-cloud setup:"
echo ""
echo "  curl -X POST http://localhost:8000/task \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -H \"X-API-Key: \$API_KEY\" \\"
echo "    -H 'X-User-ID: test-user' \\"
echo "    -d '{\"task\": \"YOUR_TASK_HERE\"}'"
echo ""
