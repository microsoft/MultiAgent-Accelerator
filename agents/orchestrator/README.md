# Orchestrator Agent

Multi-agent orchestrator implementing the **Agent-to-Agent (A2A) Protocol** for discovering and coordinating specialized agents.

## 🎯 Purpose

The Orchestrator acts as the entry point for the multi-agent system, handling:

1. **Agent Discovery**: Automatically discovers agents via their `.well-known/agent.json` endpoints
2. **Request Routing**: Routes user requests to the most appropriate specialized agent
3. **Multi-Agent Coordination**: Combines results from multiple agents for complex tasks
4. **Service Bus Integration**: Supports async communication via Azure Service Bus

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Request                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   Orchestrator Agent  │
         │   (A2A Discovery)     │
         └───────────┬───────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Travel Agent │ │ Data Agent   │ │ Code Agent   │
│ (MCP Tools)  │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

## 🚀 Features

### A2A Protocol Implementation

The orchestrator implements the A2A protocol by:

1. **Fetching Agent Cards**: GET `/.well-known/agent.json` from each agent
2. **Parsing Capabilities**: Extracts skills, endpoints, and metadata
3. **Smart Routing**: Matches user requests to agent capabilities
4. **Dynamic Discovery**: Can discover new agents at runtime

### Agent Discovery

Agents are discovered via environment variable configuration:

```env
AGENT_ENDPOINTS=http://travel-agent-service/.well-known/agent.json,http://data-agent-service/.well-known/agent.json
```

The orchestrator:
- Fetches each agent's card on startup
- Parses capabilities and skills
- Builds an internal routing table
- Can re-discover agents via `/discover` endpoint

### Request Routing

When a request comes in, the orchestrator:

1. **Analyzes the task** using keyword matching (or LLM in production)
2. **Selects the best agent** based on skills and capabilities
3. **Calls the agent** via its `/task` endpoint
4. **Returns the result** to the user

### Service Bus Support

For async communication:
- Connects to Azure Service Bus
- Can send/receive messages to/from agent queues
- Supports long-running tasks

## 📋 API Endpoints

### POST /task
Execute a task by routing to appropriate agent

**Request**:
```json
{
  "task": "Plan a 3-day trip to Paris with budget $1000",
  "user_id": "user123",
  "preferred_agent": "travel_agent"  // optional
}
```

**Response**:
```json
{
  "result": "Here's your 3-day Paris itinerary...",
  "agent_used": "travel_agent",
  "orchestrator": "orchestrator"
}
```

### GET /agents
List all discovered agents and their capabilities

**Response**:
```json
{
  "total_agents": 2,
  "agents": [
    {
      "name": "travel_agent",
      "description": "Travel planning with currency and activities",
      "skills": [
        {
          "name": "Travel Planning",
          "description": "Create comprehensive travel itineraries"
        }
      ]
    }
  ]
}
```

### POST /discover
Manually trigger agent discovery

**Response**:
```json
{
  "status": "discovery_complete",
  "agents_found": 2,
  "agents": ["travel_agent", "data_agent"]
}
```

### GET /.well-known/agent.json
Get orchestrator's own agent card

### GET /health
Health check endpoint

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PORT` | Orchestrator listening port | `8000` | No |
| `AGENT_ENDPOINTS` | Comma-separated list of agent card URLs | See below | Yes |
| `SERVICEBUS_NAMESPACE` | Azure Service Bus namespace | - | No |
| `USE_MANAGED_IDENTITY` | Use managed identity (true/false) | `true` | No |

**Default Agent Endpoints**:
```
http://travel-agent-service/.well-known/agent.json
```

### Local Development

Create `.env` file:
```env
PORT=8000
AGENT_ENDPOINTS=http://localhost:8080/.well-known/agent.json
SERVICEBUS_NAMESPACE=multiagent-dev-servicebus.servicebus.windows.net
USE_MANAGED_IDENTITY=false
```

### Kubernetes Deployment

```yaml
env:
- name: AGENT_ENDPOINTS
  value: "http://travel-agent-service/.well-known/agent.json"
- name: SERVICEBUS_NAMESPACE
  value: "multiagent-dev-servicebus.servicebus.windows.net"
- name: USE_MANAGED_IDENTITY
  value: "true"
```

## 🧪 Testing

### Start Orchestrator Locally

1. **Start specialized agents first**:
```bash
# Terminal 1: Currency MCP
cd mcp_servers/currency_mcp && python server.py

# Terminal 2: Activity MCP
cd mcp_servers/activity_mcp && python server.py

# Terminal 3: Travel Agent
cd agents/travel_agent && python main.py
```

2. **Start Orchestrator**:
```bash
cd agents/orchestrator
pip install -r requirements.txt
python main.py
```

### Test Agent Discovery

```bash
# Check discovered agents
curl http://localhost:8000/agents

# Trigger re-discovery
curl -X POST http://localhost:8000/discover
```

### Test Request Routing

```bash
# Currency task (should route to travel_agent)
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{"task": "Convert 500 USD to EUR"}'

# Travel task (should route to travel_agent)
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{"task": "Plan a 2-day trip to Paris"}'

# Restaurant task (should route to travel_agent)
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{"task": "Recommend restaurants in Tokyo"}'
```

## 🐳 Docker

**Build**:
```bash
docker build -t orchestrator:latest .
```

**Run**:
```bash
docker run -d \
  --name orchestrator \
  -p 8000:8000 \
  -e AGENT_ENDPOINTS="http://travel-agent-service/.well-known/agent.json" \
  -e SERVICEBUS_NAMESPACE="multiagent-dev-servicebus.servicebus.windows.net" \
  orchestrator:latest
```

## ☸️ Kubernetes

Deploy to AKS:
```bash
kubectl apply -f k8s/orchestrator-deployment.yaml
```

The orchestrator will:
- Use Workload Identity for Azure authentication
- Discover agents via Kubernetes service names
- Connect to Service Bus for async tasks

## 🔍 How It Works

### 1. Startup & Discovery

On startup, the orchestrator:

```python
# Fetch agent cards
for endpoint in AGENT_ENDPOINTS:
    agent_card = await discover_agent(endpoint)
    discovered_agents[agent_card["name"]] = agent_card
```

### 2. Request Processing

When a request arrives:

```python
# 1. Select best agent
selected_agent = select_best_agent(task)

# 2. Call the agent
result = await call_agent(selected_agent, task, user_id)

# 3. Return result
return {"result": result, "agent_used": selected_agent}
```

### 3. Agent Selection

Agent selection uses keyword matching:

```python
if "currency" in task_lower:
    return "travel_agent"  # Has currency tools via MCP

if "restaurant" in task_lower or "trip" in task_lower:
    return "travel_agent"  # Has activity tools via MCP
```

**Production Enhancement**: Use an LLM for semantic routing or build a classifier.

## 📚 A2A Protocol

The orchestrator implements A2A by:

1. **Agent Card Discovery**: Fetches `.well-known/agent.json`
2. **Capability Matching**: Parses skills and examples
3. **Dynamic Routing**: Routes based on capabilities
4. **Standard Endpoints**: Uses `/task` for execution

### Agent Card Format

Each agent exposes:
```json
{
  "name": "agent_name",
  "description": "...",
  "capabilities": {
    "skills": [
      {
        "id": "skill_id",
        "name": "Skill Name",
        "description": "...",
        "examples": ["example 1", "example 2"]
      }
    ]
  },
  "endpoints": {
    "task": {"url": "/task", "method": "POST"}
  }
}
```

## 🔮 Future Enhancements

- [ ] **LLM-based Routing**: Use GPT to select best agent semantically
- [ ] **Multi-Agent Workflows**: Chain multiple agents for complex tasks
- [ ] **Caching**: Cache agent responses for common queries
- [ ] **Load Balancing**: Distribute across multiple instances of same agent
- [ ] **Service Bus Queues**: Full async task processing
- [ ] **Agent Health Monitoring**: Track agent availability and performance
- [ ] **Circuit Breaker**: Handle agent failures gracefully

## 📖 Related Documentation

- [A2A Protocol Specification](../docs/A2A_PROTOCOL.md) (to be created)
- [Travel Agent README](../travel_agent/README.md)
- [Service Bus Integration](../../docs/SERVICEBUS_INTEGRATION.md) (to be created)

## 🤝 Contributing

To add a new agent to the system:

1. Implement `.well-known/agent.json` in your agent
2. Add agent endpoint to `AGENT_ENDPOINTS` environment variable
3. Ensure agent has `/task` endpoint
4. Deploy and test discovery
