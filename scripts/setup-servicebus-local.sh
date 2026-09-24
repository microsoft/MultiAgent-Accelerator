#!/bin/bash

# Quick Start Script for Testing Orchestrator with Service Bus Locally
# This script helps set up and test the complete multi-agent system with Azure Service Bus

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=============================================="
echo "🚀 Multi-Agent System with Service Bus Setup"
echo "=============================================="
echo ""

# Check if Azure CLI is logged in
echo "🔐 Checking Azure CLI authentication..."
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure CLI"
    echo "   Please run: az login"
    exit 1
fi
echo "✅ Azure CLI authenticated"
echo ""

# Get Service Bus namespace
echo "📋 Getting Service Bus namespace..."
SERVICEBUS_NAME=$(az servicebus namespace list --query "[?contains(name, 'multiagent')].name" -o tsv | head -1)

if [ -z "$SERVICEBUS_NAME" ]; then
    echo "❌ Service Bus namespace not found"
    echo "   Please deploy infrastructure first: ./scripts/deploy-infrastructure.sh"
    exit 1
fi

echo "✅ Found Service Bus: $SERVICEBUS_NAME"
SERVICEBUS_NAMESPACE="${SERVICEBUS_NAME}.servicebus.windows.net"
echo ""

# Get Resource Group
RG_NAME=$(az servicebus namespace list --query "[?name=='$SERVICEBUS_NAME'].resourceGroup" -o tsv)
echo "✅ Resource Group: $RG_NAME"
echo ""

# Grant current user permissions
echo "🔑 Granting Service Bus permissions..."
USER_ID=$(az ad signed-in-user show --query id -o tsv)
SERVICEBUS_ID=$(az servicebus namespace show --name "$SERVICEBUS_NAME" --resource-group "$RG_NAME" --query id -o tsv)

# Check if role assignment already exists
EXISTING_ROLE=$(az role assignment list --assignee "$USER_ID" --scope "$SERVICEBUS_ID" --query "[?roleDefinitionName=='Azure Service Bus Data Owner'].roleDefinitionName" -o tsv)

if [ -z "$EXISTING_ROLE" ]; then
    echo "   Creating role assignment..."
    az role assignment create \
        --assignee "$USER_ID" \
        --role "Azure Service Bus Data Owner" \
        --scope "$SERVICEBUS_ID" \
        --output none
    echo "   ✅ Role assigned"
else
    echo "   ✅ Role already assigned"
fi
echo ""

# Create queues if they don't exist
echo "📬 Setting up Service Bus queues..."

for QUEUE in "agent-tasks" "agent-responses"; do
    if az servicebus queue show --namespace-name "$SERVICEBUS_NAME" --resource-group "$RG_NAME" --name "$QUEUE" &> /dev/null; then
        echo "   ✅ Queue '$QUEUE' already exists"
        if [ "$QUEUE" = "agent-responses" ]; then
            REQUIRES_SESSION=$(az servicebus queue show \
                --namespace-name "$SERVICEBUS_NAME" \
                --resource-group "$RG_NAME" \
                --name "$QUEUE" \
                --query requiresSession -o tsv)
            if [ "$REQUIRES_SESSION" != "true" ]; then
                echo "   ❌ Queue 'agent-responses' must have sessions enabled for user-isolated responses."
                echo "      Drain or back up pending responses, delete the queue, then recreate it with:"
                echo "      az servicebus queue delete --namespace-name '$SERVICEBUS_NAME' --resource-group '$RG_NAME' --name agent-responses"
                echo "      az servicebus queue create --namespace-name '$SERVICEBUS_NAME' --resource-group '$RG_NAME' --name agent-responses --requires-session true"
                exit 1
            fi
        fi
    else
        echo "   Creating queue '$QUEUE'..."
        if [ "$QUEUE" = "agent-responses" ]; then
            az servicebus queue create \
                --namespace-name "$SERVICEBUS_NAME" \
                --resource-group "$RG_NAME" \
                --name "$QUEUE" \
                --requires-session true \
                --output none
        else
            az servicebus queue create \
                --namespace-name "$SERVICEBUS_NAME" \
                --resource-group "$RG_NAME" \
                --name "$QUEUE" \
                --output none
        fi
        echo "   ✅ Queue '$QUEUE' created"
    fi
done
echo ""

# Update orchestrator .env file
echo "⚙️  Configuring orchestrator..."
cat > "$PROJECT_ROOT/agents/orchestrator/.env" << EOF
# Orchestrator Configuration for Local Testing
PORT=8000
AGENT_ENDPOINTS=http://localhost:8080/.well-known/agent.json
SERVICEBUS_NAMESPACE=$SERVICEBUS_NAMESPACE
USE_MANAGED_IDENTITY=false
EOF
echo "✅ Configuration updated"
echo ""

echo "=============================================="
echo "✅ Setup Complete!"
echo "=============================================="
echo ""
echo "📝 Next Steps:"
echo ""
echo "1️⃣  Start the MCP servers (in separate terminals):"
echo "   Terminal 1: cd mcp_servers/currency_mcp && ../../.venv/Scripts/python.exe server.py"
echo "   Terminal 2: cd mcp_servers/activity_mcp && ../../.venv/Scripts/python.exe server.py"
echo ""
echo "2️⃣  Start the Travel Agent:"
echo "   Terminal 3: cd agents/travel_agent && ../../.venv/Scripts/python.exe main.py"
echo ""
echo "3️⃣  Start the Orchestrator:"
echo "   Terminal 4: cd agents/orchestrator && ../../.venv/Scripts/python.exe main.py"
echo ""
echo "4️⃣  Test Service Bus integration:"
echo ""
echo "   # Send task to Service Bus queue"
echo "   .venv/Scripts/python.exe tests/test_servicebus.py send --task \"What is 100 USD in EUR?\""
echo ""
echo "   # The orchestrator will automatically process it from the queue"
echo "   # Check orchestrator terminal for processing logs"
echo ""
echo "   # Receive response from queue"
echo "   .venv/Scripts/python.exe tests/test_servicebus.py receive"
echo ""
echo "   # Or run full end-to-end test"
echo "   .venv/Scripts/python.exe tests/test_servicebus.py test"
echo ""
echo "5️⃣  Or test with direct HTTP (no Service Bus):"
echo "   curl -X POST http://localhost:8000/task \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"task\": \"What is 100 USD in EUR?\"}'"
echo ""
echo "6️⃣  Test async endpoint (with Service Bus):"
echo "   curl -X POST http://localhost:8000/task/async \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"task\": \"Find restaurants in Tokyo\", \"user_id\": \"user-123\"}'"
echo ""
echo "=============================================="
echo "📚 Documentation:"
echo "   - TESTING_AZURE_SERVICEBUS.md - Service Bus testing guide"
echo "   - QUICKSTART_A2A.md - A2A protocol quick start"
echo "   - agents/orchestrator/README.md - Orchestrator documentation"
echo "=============================================="
