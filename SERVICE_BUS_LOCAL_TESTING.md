# ✅ Yes! You Can Test Locally with Azure Service Bus

## Quick Answer

**YES!** You can test the orchestrator locally with Azure Service Bus. Here's what I've set up for you:

## What's Been Configured

### ✅ Service Bus Queues Created
- `agent-tasks` - for incoming tasks
- `agent-responses` - for results

### ✅ Orchestrator Enhanced
Added Service Bus functionality to `agents/orchestrator/main.py`:
- **POST /task/async** - Send task to Service Bus queue
- **Background processor** - Automatically processes messages from queue
- **Auto-response** - Sends results to response queue

### ✅ Test Script Created
`tests/test_servicebus.py` - Complete testing tool

### ✅ Configuration Ready
`agents/orchestrator/.env` - Pre-configured for local testing

## 🚀 How to Test (3 Simple Steps)

### Step 1: Grant Yourself Permissions

**Via Azure Portal** (easiest):
1. Go to https://portal.azure.com
2. Find `multiagent-dev-servicebus`
3. Click "Access control (IAM)"
4. Add role assignment: **Azure Service Bus Data Owner**
5. Select yourself
6. Save

### Step 2: Start All Components

```bash
# Terminal 1: Currency MCP
cd mcp_servers/currency_mcp && ../../.venv/Scripts/python.exe server.py

# Terminal 2: Activity MCP  
cd mcp_servers/activity_mcp && ../../.venv/Scripts/python.exe server.py

# Terminal 3: Travel Agent
cd agents/travel_agent && ../../.venv/Scripts/python.exe main.py

# Terminal 4: Orchestrator (with Service Bus!)
cd agents/orchestrator && ../../.venv/Scripts/python.exe main.py
```

### Step 3: Test Service Bus Integration

```bash
# Send task to Service Bus (async)
curl -X POST http://localhost:8000/task/async \
  -H "Content-Type: application/json" \
  -d '{"task": "What is 100 USD in EUR?", "user_id": "test-123"}'

# Watch the orchestrator terminal - it will automatically:
# 1. Pick up the message from the queue
# 2. Route it to the Travel Agent
# 3. Get the response
# 4. Send response to the response queue
```

## 🎯 What Happens Under the Hood

```
┌──────────┐
│   User   │
└────┬─────┘
     │ POST /task/async
     ▼
┌────────────────┐
│ Orchestrator   │──► Sends to Service Bus queue "agent-tasks"
└────────────────┘
     │
     │ (background processor)
     ▼
┌────────────────┐
│ Orchestrator   │──► Receives from queue
│  (background)  │──► Calls Travel Agent
│                │──► Sends result to "agent-responses"
└────────────────┘
```

## 📊 Monitor Queue Activity

```bash
# Check active messages in task queue
az servicebus queue show \
  --namespace-name multiagent-dev-servicebus \
  --resource-group multiagent-dev-rg \
  --name agent-tasks \
  --query "countDetails.activeMessageCount"

# Check response queue
az servicebus queue show \
  --namespace-name multiagent-dev-servicebus \
  --resource-group multiagent-dev-rg \
  --name agent-responses \
  --query "countDetails.activeMessageCount"
```

## 🧪 Advanced Testing

### Use the Test Script

```bash
# Send a task
.venv/Scripts/python.exe tests/test_servicebus.py send --task "Find restaurants in Paris"

# Receive response (waits up to 30 seconds)
.venv/Scripts/python.exe tests/test_servicebus.py receive

# Run full end-to-end test
.venv/Scripts/python.exe tests/test_servicebus.py test
```

## 🆚 HTTP vs Service Bus

### Synchronous (HTTP) - Use /task
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{"task": "What is 100 USD in EUR?"}'
```
- ⚡ Immediate response
- 🔗 Direct connection required
- ⏱️ Waits for completion

### Asynchronous (Service Bus) - Use /task/async
```bash
curl -X POST http://localhost:8000/task/async \
  -H "Content-Type: application/json" \
  -d '{"task": "What is 100 USD in EUR?"}'
```
- 📬 Returns message ID immediately
- 🔄 Processes in background
- 📊 Scalable for many requests
- 💪 Resilient to failures

## ✅ What You Get

- **Real Azure Service Bus** - Not a mock, actual cloud queues
- **Async Processing** - Background worker automatically processes tasks
- **Queue Monitoring** - See messages in Azure Portal
- **Full Integration** - Same code that runs in production (AKS)
- **Local Development** - Test without deploying to Kubernetes

## 📚 Documentation

- **TESTING_AZURE_SERVICEBUS.md** - Detailed setup guide
- **agents/orchestrator/README.md** - Orchestrator documentation
- **tests/test_servicebus.py** - Test script source code

## 🎓 Why This Is Powerful

1. **Production Parity** - Same Service Bus used in AKS deployment
2. **Async Patterns** - Learn cloud-native async communication
3. **Scalability** - Queue-based processing scales easily
4. **Reliability** - Messages aren't lost if agent crashes
5. **Monitoring** - Azure Portal shows queue metrics

## 🚨 Troubleshooting

### "Unauthorized" Error
→ Grant yourself "Azure Service Bus Data Owner" role (see Step 1)

### Orchestrator says "Service Bus not available"
→ Check `.env` file has `SERVICEBUS_NAMESPACE=multiagent-dev-servicebus.servicebus.windows.net`

### No messages processed
→ Check orchestrator logs show "Queue processor started"

### Want HTTP only (no Service Bus)?
→ Just use `POST /task` instead of `POST /task/async`

---

**Bottom Line**: Yes, you can test locally with Azure Service Bus! It's fully integrated and ready to use. 🎉
