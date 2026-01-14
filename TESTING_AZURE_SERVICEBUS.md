# Testing Locally with Azure Service Bus

This guide shows how to test the orchestrator locally with Azure Service Bus for async communication.

## Prerequisites

1. **Azure CLI** installed and authenticated
2. **Service Bus Namespace** deployed (from infrastructure deployment)
3. **Python environment** set up with orchestrator dependencies

## Step 1: Get Service Bus Details

```bash
# Get Service Bus namespace name
az servicebus namespace list \
  --resource-group rg-multiagent-dev \
  --query "[0].name" -o tsv

# Expected output: multiagent-dev-servicebus
```

## Step 2: Grant Yourself Service Bus Permissions

For local testing, grant yourself permissions via Azure Portal (easier than CLI):

### Option A: Azure Portal (Recommended)

1. Open https://portal.azure.com
2. Navigate to your Service Bus namespace (`multiagent-dev-servicebus`)
3. Click "Access control (IAM)" in the left menu
4. Click "+ Add" → "Add role assignment"
5. Select role: **Azure Service Bus Data Owner**
6. Click "Next"
7. Select "User, group, or service principal"
8. Click "+ Select members" and search for your email
9. Click "Select" → "Review + assign"
10. Done! ✅

### Option B: Azure CLI

**If you have access policies enabled**, try this:

```bash
# Refresh your Azure CLI login first
az login

# Grant permission
az role assignment create \
  --assignee $(az ad signed-in-user show --query id -o tsv) \
  --role "Azure Service Bus Data Owner" \
  --scope $(az servicebus namespace show \
    --name multiagent-dev-servicebus \
    --resource-group multiagent-dev-rg \
    --query id -o tsv)
```

**Note**: If you get authentication errors, use the Azure Portal method above instead.

## Step 3: Verify Queues Are Created

The queues should already be created. Verify:

```bash
# Check if queues exist
az servicebus queue list \
  --namespace-name multiagent-dev-servicebus \
  --resource-group multiagent-dev-rg \
  --query "[].name" -o tsv
```

Expected output:
```
agent-tasks
agent-responses
```

✅ If you see both queues, you're good to go!

## Step 4: Configure Orchestrator for Local Testing

Create `.env` file in `agents/orchestrator/`:

```bash
cd agents/orchestrator
cp .env.template .env
```

Edit `.env`:

```bash
# Port
PORT=8000

# Agent endpoints (for local testing, use localhost)
AGENT_ENDPOINTS=http://localhost:8080/.well-known/agent.json

# Service Bus (use your actual namespace)
SERVICEBUS_NAMESPACE=multiagent-dev-servicebus.servicebus.windows.net

# Use Azure CLI credential for local testing
USE_MANAGED_IDENTITY=false
```

## Step 5: Run Components

### Terminal 1: Currency MCP Server

```bash
cd mcp_servers/currency_mcp
../../.venv/Scripts/python.exe server.py
```

Expected output:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### Terminal 2: Activity MCP Server

```bash
cd mcp_servers/activity_mcp
../../.venv/Scripts/python.exe server.py
```

Expected output:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8002
```

### Terminal 3: Travel Agent

```bash
cd agents/travel_agent
../../.venv/Scripts/python.exe main.py
```

Expected output:
```
INFO:     Travel Agent starting on port 8080
INFO:     Successfully connected to Currency MCP at http://localhost:8001
INFO:     Successfully connected to Activity MCP at http://localhost:8002
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### Terminal 4: Orchestrator

```bash
cd agents/orchestrator
../../.venv/Scripts/python.exe main.py
```

Expected output:
```
INFO:     Discovered agent: travel_agent (Travel Planning Agent)
INFO:     Service Bus client initialized for: multiagent-dev-servicebus.servicebus.windows.net
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 6: Test Service Bus Integration

### Test 1: Send Task via Service Bus

```bash
# Test sending a task to Service Bus queue
curl -X POST http://localhost:8000/task/async \
  -H "Content-Type: application/json" \
  -d '{
    "task": "What is the exchange rate from USD to EUR?",
    "user_id": "test-user-001"
  }'
```

Expected response:
```json
{
  "message": "Task queued successfully",
  "message_id": "abc-123-xyz",
  "queue": "agent-tasks"
}
```

### Test 2: Check Service Bus Queue

```bash
# Check messages in queue
az servicebus queue show \
  --namespace-name multiagent-dev-servicebus \
  --resource-group rg-multiagent-dev \
  --name agent-tasks \
  --query "countDetails.activeMessageCount"
```

Expected output: `1` (or more if you sent multiple)

### Test 3: Receive from Service Bus

```bash
# The orchestrator should process messages automatically
# Check orchestrator logs in Terminal 4 for:
# "Processing message from queue: agent-tasks"
# "Task completed: What is the exchange rate..."
```

### Test 4: Verify Response Queue

```bash
# Check response queue
az servicebus queue show \
  --namespace-name multiagent-dev-servicebus \
  --resource-group rg-multiagent-dev \
  --name agent-responses \
  --query "countDetails.activeMessageCount"
```

## Troubleshooting

### Error: "Unauthorized access to Service Bus"

**Solution**: Make sure you granted yourself the "Azure Service Bus Data Owner" role (see Step 2)

```bash
# Verify role assignment
az role assignment list \
  --assignee $(az ad signed-in-user show --query id -o tsv) \
  --scope $(az servicebus namespace show \
    --name multiagent-dev-servicebus \
    --resource-group rg-multiagent-dev \
    --query id -o tsv)
```

### Error: "Service Bus namespace not found"

**Solution**: Deploy infrastructure first:

```bash
./scripts/deploy-infrastructure.sh
```

### Error: "Queue does not exist"

**Solution**: Create queues (see Step 3):

```bash
az servicebus queue create \
  --namespace-name multiagent-dev-servicebus \
  --resource-group rg-multiagent-dev \
  --name agent-tasks
```

### No messages being processed

**Check**:
1. Orchestrator logs show "Service Bus client initialized"
2. Queue has messages: `az servicebus queue show ... --query "countDetails.activeMessageCount"`
3. No errors in orchestrator terminal

## Testing Without Service Bus (HTTP Only)

If you just want to test A2A protocol without Service Bus:

```bash
# Send task directly via HTTP
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task": "What is the exchange rate from USD to EUR?"
  }'
```

This bypasses Service Bus and uses direct HTTP communication.

## Architecture Flow

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │ POST /task/async
       ▼
┌──────────────────┐
│  Orchestrator    │───────┐
│  (localhost:8000)│       │ 1. Send to Queue
└──────────────────┘       │
                           ▼
                    ┌─────────────────┐
                    │ Service Bus     │
                    │ agent-tasks     │
                    └────────┬────────┘
                             │ 2. Receive & Process
┌──────────────────┐         │
│  Orchestrator    │◄────────┘
│  (background)    │
└──────┬───────────┘
       │ 3. Call Agent
       ▼
┌──────────────────┐
│  Travel Agent    │
│  (localhost:8080)│
└──────┬───────────┘
       │ 4. Send Response
       ▼
┌─────────────────┐
│ Service Bus     │
│ agent-responses │
└─────────────────┘
```

## Next Steps

- [ ] Test with multiple concurrent tasks
- [ ] Test error handling (invalid tasks)
- [ ] Test with different agents
- [ ] Monitor Service Bus metrics in Azure Portal
- [ ] Deploy to AKS for production testing

## Related Documentation

- [QUICKSTART_A2A.md](QUICKSTART_A2A.md) - A2A protocol testing (HTTP only)
- [docs/A2A_PROTOCOL.md](docs/A2A_PROTOCOL.md) - A2A protocol specification
- [agents/orchestrator/README.md](agents/orchestrator/README.md) - Orchestrator documentation
