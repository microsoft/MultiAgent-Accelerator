# A2A Multi-Agent System - Quick Start Guide

This guide shows you how to run the complete multi-agent system with A2A protocol locally.

## 🎯 What You'll Build

A multi-agent system where:

1. **MCP Servers** provide specialized tools (currency, activities)
2. **Travel Agent** uses MCP tools to plan trips
3. **Orchestrator** discovers agents and routes requests using A2A protocol

```
User → Orchestrator (A2A) → Travel Agent (MCP) → {Currency MCP, Activity MCP}
```

## 📋 Prerequisites

- Python 3.11+
- uv or pip
- 4 terminal windows

## 🚀 Quick Start (5 Minutes)

### Step 1: Setup Environment

```bash
# Clone and navigate to project
cd MultiAgent-AKS-MAF

# Create virtual environment (if not done)
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

### Step 2: Start MCP Servers

**Terminal 1: Currency MCP**
```bash
cd mcp_servers/currency_mcp
pip install -r requirements.txt
python server.py
```

You should see:
```
INFO:currency-mcp:Starting Currency MCP Server in StreamableHTTP mode on port 8001
```

**Terminal 2: Activity MCP**
```bash
cd mcp_servers/activity_mcp
pip install -r requirements.txt
python server.py
```

You should see:
```
INFO:activity-mcp:Starting Activity MCP Server in StreamableHTTP mode on port 8002
```

### Step 3: Start Travel Agent

**Terminal 3: Travel Agent**
```bash
cd agents/travel_agent

# Create .env from template
cp .env.template .env

# Edit .env with your Azure OpenAI credentials
# AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
# AZURE_OPENAI_DEPLOYMENT=gpt-4o

pip install -r requirements.txt
python main.py
```

You should see:
```
INFO:travel_agent:✅ Travel Agent initialized successfully
INFO:uvicorn:Uvicorn running on http://0.0.0.0:8080
```

### Step 4: Start Orchestrator

**Terminal 4: Orchestrator**
```bash
cd agents/orchestrator

# Create .env from template
cp .env.template .env
# Default settings work for local testing

pip install -r requirements.txt
python main.py
```

You should see:
```
INFO:orchestrator:🔍 Starting agent discovery...
INFO:orchestrator:✅ Discovered agent: travel_agent
INFO:orchestrator:   Skills: 4
INFO:orchestrator:✅ Discovery complete. Found 1 agents:
INFO:orchestrator:   - travel_agent
INFO:uvicorn:Uvicorn running on http://0.0.0.0:8000
```

## ✅ Verify Everything Works

### Test 1: Check Orchestrator Health

```bash
curl http://localhost:8000/health
```

Expected:
```json
{
  "status": "healthy",
  "agents_discovered": 1,
  "service_bus_connected": false
}
```

### Test 2: List Discovered Agents

```bash
curl http://localhost:8000/agents
```

You'll see the Travel Agent with its 4 skills (currency, travel, restaurants, attractions).

### Test 3: Execute a Task via Orchestrator

```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{"task": "Convert 500 USD to EUR"}'
```

Expected:
```json
{
  "result": "The current exchange rate is 1 USD = 0.8642 EUR. Therefore, 500 USD = 432.10 EUR.",
  "agent_used": "travel_agent",
  "orchestrator": "orchestrator"
}
```

### Test 4: Travel Planning

```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{"task": "Plan a 2-day trip to Paris"}'
```

You'll get a complete itinerary!

## 🧪 Run Automated Tests

```bash
# Test MCP servers
python tests/test_mcp_servers.py

# Test Travel Agent
python tests/test_travel_agent.py

# Test Orchestrator (A2A)
python tests/test_orchestrator.py
```

## 🔍 Understanding the Flow

### Request Flow

1. **User sends request** to Orchestrator
   ```
   POST http://localhost:8000/task
   {"task": "Convert 500 USD to EUR"}
   ```

2. **Orchestrator discovers agents** (on startup)
   ```
   GET http://travel-agent-service/.well-known/agent.json
   ```

3. **Orchestrator selects best agent** based on task keywords
   ```python
   "convert" + "USD" + "EUR" → selects travel_agent
   ```

4. **Orchestrator calls agent**
   ```
   POST http://localhost:8080/task
   {"task": "Convert 500 USD to EUR", "user_id": "test_user"}
   ```

5. **Travel Agent uses MCP tools**
   ```
   POST http://localhost:8001/mcp  # Currency MCP
   ```

6. **MCP server calls Frankfurter API**
   ```
   GET https://api.frankfurter.app/latest?from=USD&to=EUR&amount=500
   ```

7. **Response flows back**
   ```
   MCP → Travel Agent → Orchestrator → User
   ```

## 📊 Architecture Visualization

```
┌─────────────────────────────────────────────────────────────┐
│                        USER                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   ORCHESTRATOR        │
         │   Port: 8000          │
         │   A2A Discovery       │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   TRAVEL AGENT        │
         │   Port: 8080          │
         │   MCP Client          │
         └───────────┬───────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────┐          ┌──────────────┐
│Currency MCP  │          │Activity MCP  │
│Port: 8001    │          │Port: 8002    │
│Frankfurter API│         │Sample Data   │
└──────────────┘          └──────────────┘
```

## 🎓 What's Happening?

### A2A Protocol

- **Agent Discovery**: Orchestrator fetches `/.well-known/agent.json` from each agent
- **Capability Matching**: Orchestrator reads agent skills and examples
- **Request Routing**: Orchestrator routes based on task keywords
- **Standard Interface**: All agents use `/task` endpoint

### MCP Protocol

- **Tool Discovery**: Travel Agent discovers MCP server tools
- **Tool Calling**: Travel Agent calls MCP tools via StreamableHTTP
- **Session Management**: MCP maintains stateful sessions (hence session affinity in K8s)

## 🐛 Troubleshooting

### "Failed to discover agent"

**Problem**: Orchestrator can't find Travel Agent

**Solution**:
1. Check Travel Agent is running on port 8080
2. Check `.env` in orchestrator has correct endpoint:
   ```env
   AGENT_ENDPOINTS=http://localhost:8080/.well-known/agent.json
   ```

### "Agent not initialized"

**Problem**: Travel Agent can't start

**Solutions**:
1. Check MCP servers are running (ports 8001, 8002)
2. Check Azure OpenAI credentials in Travel Agent `.env`
3. Check you're authenticated: `az login`

### "No agents available"

**Problem**: Orchestrator started but found 0 agents

**Solutions**:
1. Start Travel Agent first
2. Check orchestrator logs for discovery errors
3. Manually trigger discovery: `curl -X POST http://localhost:8000/discover`

## 📚 Next Steps

1. **Add More Agents**: Create a new agent with A2A support
2. **Deploy to AKS**: Use the deployment scripts
3. **Add Service Bus**: Enable async communication
4. **Enhance Routing**: Use LLM for semantic routing

## 🔗 Related Documentation

- [A2A Protocol](../docs/A2A_PROTOCOL.md) - Full protocol specification
- [Orchestrator README](../agents/orchestrator/README.md) - Detailed orchestrator docs
- [Travel Agent README](../agents/travel_agent/README.md) - Travel agent implementation
- [MCP Servers](../mcp_servers/) - MCP server implementations

## 🎉 Success!

If you've made it here, you have:

✅ A working multi-agent system  
✅ A2A protocol for agent discovery  
✅ MCP protocol for tool integration  
✅ Complete travel planning capabilities  

Now you can:
- Add more agents
- Deploy to Azure
- Integrate with your applications
- Build complex multi-agent workflows
