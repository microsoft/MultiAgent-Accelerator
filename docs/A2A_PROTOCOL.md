# Agent-to-Agent (A2A) Protocol Implementation

This document describes how the Multi-Agent System implements the **Agent-to-Agent (A2A) Protocol** for agent discovery and communication.

## 📋 Overview

The A2A protocol enables autonomous agents to:

1. **Discover each other** through standardized agent cards
2. **Understand capabilities** via structured metadata
3. **Communicate** using standard HTTP endpoints
4. **Coordinate** on complex multi-agent tasks

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Request                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   Orchestrator        │
         │   - Agent Discovery   │
         │   - Request Routing   │
         │   - Coordination      │
         └───────────┬───────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
    ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│Travel Agent │  │ Data Agent  │  │ Code Agent  │
│             │  │             │  │             │
│ Agent Card  │  │ Agent Card  │  │ Agent Card  │
│ /.well-known│  │ /.well-known│  │ /.well-known│
│ /agent.json │  │ /agent.json │  │ /agent.json │
└─────────────┘  └─────────────┘  └─────────────┘
```

## 🔍 Agent Discovery

### Agent Card Endpoint

Every agent MUST expose a standard discovery endpoint:

```
GET /.well-known/agent.json
```

### Agent Card Format

```json
{
  "name": "agent_name",
  "description": "Brief description of agent's purpose",
  "version": "1.0.0",
  "capabilities": {
    "skills": [
      {
        "id": "skill_id",
        "name": "Human-readable skill name",
        "description": "Detailed description of what this skill does",
        "examples": [
          "Example query 1",
          "Example query 2",
          "Example query 3"
        ]
      }
    ],
    "supported_locations": ["Paris", "Tokyo", "Rome"],  // Optional
    "protocols": ["http", "servicebus"],  // Communication methods
    "mcp_tools": ["tool1", "tool2"]  // Optional: MCP tools available
  },
  "endpoints": {
    "task": {
      "url": "/task",
      "method": "POST",
      "description": "Execute a task",
      "request_schema": {
        "task": "string (required)",
        "user_id": "string (optional)"
      }
    },
    "health": {
      "url": "/health",
      "method": "GET",
      "description": "Health check"
    }
  },
  "protocol": "a2a",
  "contact": {
    "author": "Team Name",
    "repository": "https://github.com/org/repo"
  }
}
```

## 🔄 Discovery Process

### 1. Orchestrator Startup

On startup, the orchestrator:

```python
async def discover_all_agents():
    """Discover all configured agents"""
    for endpoint in AGENT_ENDPOINTS:
        # Fetch agent card
        agent_card = await discover_agent(endpoint)
        
        # Store capabilities
        discovered_agents[agent_card["name"]] = agent_card
```

### 2. Agent Registration

Agents are registered via environment variable:

```env
AGENT_ENDPOINTS=http://travel-agent-service/.well-known/agent.json,http://data-agent-service/.well-known/agent.json
```

### 3. Dynamic Re-Discovery

Agents can be rediscovered at runtime:

```bash
POST /discover
```

This allows:
- Adding new agents without restart
- Updating agent capabilities
- Recovering from agent failures

## 🎯 Request Routing

### Capability Matching

The orchestrator selects agents based on:

1. **Keyword Matching** (current implementation)
2. **Semantic Similarity** (future: using embeddings)
3. **LLM-based Routing** (future: using GPT-4)

### Current Algorithm

```python
def select_best_agent(task: str) -> str:
    task_lower = task.lower()
    
    # Match keywords to agent skills
    for agent_name, agent_card in discovered_agents.items():
        skills = agent_card["capabilities"]["skills"]
        
        for skill in skills:
            if matches_skill(task_lower, skill):
                return agent_name
    
    # Default to first available agent
    return list(discovered_agents.keys())[0]
```

## 📡 Communication Protocol

### Standard Task Endpoint

All agents MUST implement:

```
POST /task
```

**Request**:
```json
{
  "task": "User's natural language request",
  "user_id": "unique_user_identifier"
}
```

**Response**:
```json
{
  "result": "Agent's response as string",
  "agent": "agent_name"
}
```

### Health Endpoint

All agents SHOULD implement:

```
GET /health
```

**Response**:
```json
{
  "status": "healthy"
}
```

## 🌐 Example Implementation

### Travel Agent Card

```json
{
  "name": "travel_agent",
  "description": "Specialized travel planning agent with currency and activity tools",
  "version": "1.0.0",
  "capabilities": {
    "skills": [
      {
        "id": "travel_planning",
        "name": "Travel Planning",
        "description": "Create comprehensive travel itineraries",
        "examples": [
          "Plan a 3-day trip to Paris",
          "Create an itinerary for Tokyo"
        ]
      },
      {
        "id": "currency_exchange",
        "name": "Currency Exchange",
        "description": "Real-time exchange rates and conversion",
        "examples": [
          "What's the exchange rate from USD to EUR?",
          "Convert 500 USD to JPY"
        ]
      }
    ],
    "mcp_tools": ["currency_tools", "activity_tools"]
  },
  "endpoints": {
    "task": {
      "url": "/task",
      "method": "POST"
    }
  }
}
```

### Orchestrator Usage

```python
# 1. User request
task = "Plan a 2-day trip to Paris with 500 USD budget"

# 2. Agent selection
selected_agent = select_best_agent(task)
# Result: "travel_agent" (matches "trip" keyword)

# 3. Agent call
result = await call_agent(selected_agent, task, user_id)

# 4. Return to user
return {"result": result, "agent_used": selected_agent}
```

## 🔧 Integration Examples

### Adding a New Agent

**Step 1**: Implement agent card endpoint

```python
@app.get("/.well-known/agent.json")
async def agent_card():
    return {
        "name": "my_agent",
        "description": "My specialized agent",
        "capabilities": {
            "skills": [
                {
                    "id": "my_skill",
                    "name": "My Skill",
                    "description": "What I can do",
                    "examples": ["Example 1", "Example 2"]
                }
            ]
        },
        "endpoints": {
            "task": {"url": "/task", "method": "POST"}
        }
    }
```

**Step 2**: Implement task endpoint

```python
@app.post("/task")
async def execute_task(request: TaskRequest):
    # Process the task
    result = process(request.task)
    
    return {
        "result": result,
        "agent": "my_agent"
    }
```

**Step 3**: Add to orchestrator

```env
AGENT_ENDPOINTS=http://my-agent-service/.well-known/agent.json
```

**Step 4**: Deploy and test

```bash
# Deploy agent
kubectl apply -f my-agent-deployment.yaml

# Trigger discovery
curl -X POST http://orchestrator/discover

# Test routing
curl -X POST http://orchestrator/task \
  -d '{"task": "Something my agent can do"}'
```

## 🚀 Deployment

### Local Testing

```bash
# 1. Start agents
python agents/travel_agent/main.py

# 2. Start orchestrator
cd agents/orchestrator
python main.py

# 3. Test discovery
curl http://localhost:8000/agents
```

### Kubernetes Deployment

```yaml
# Orchestrator config
env:
- name: AGENT_ENDPOINTS
  value: "http://travel-agent-service/.well-known/agent.json,http://data-agent-service/.well-known/agent.json"
```

Agents discover each other via Kubernetes service names.

## 📊 Benefits of A2A Protocol

✅ **Loose Coupling**: Agents don't need to know about each other's internals  
✅ **Dynamic Discovery**: Add/remove agents without code changes  
✅ **Standardization**: Common interface for all agents  
✅ **Extensibility**: Easy to add new agents and capabilities  
✅ **Debugging**: Clear visibility into agent capabilities  
✅ **Testing**: Can test agents independently  

## 🔮 Future Enhancements

### Advanced Routing

Use LLM for semantic matching:

```python
async def select_best_agent_llm(task: str) -> str:
    """Use GPT to select best agent based on capabilities"""
    
    # Build prompt with all agent capabilities
    prompt = f"Task: {task}\n\nAvailable agents:\n"
    for name, card in discovered_agents.items():
        prompt += f"- {name}: {card['description']}\n"
        for skill in card['capabilities']['skills']:
            prompt += f"  * {skill['name']}: {skill['description']}\n"
    
    prompt += "\nWhich agent should handle this task?"
    
    # Call LLM
    response = await llm.generate(prompt)
    return response.agent_name
```

### Multi-Agent Workflows

Chain multiple agents:

```python
async def execute_complex_task(task: str):
    """Execute task requiring multiple agents"""
    
    # 1. Travel Agent: Plan trip
    itinerary = await call_agent("travel_agent", 
        "Create 2-day Paris itinerary")
    
    # 2. Data Agent: Check weather
    weather = await call_agent("data_agent",
        "Get Paris weather forecast")
    
    # 3. Code Agent: Generate calendar events
    calendar = await call_agent("code_agent",
        f"Create calendar events for: {itinerary}")
    
    # 4. Combine results
    return combine(itinerary, weather, calendar)
```

### Service Bus Integration

Async communication:

```python
async def send_task_to_queue(agent_name: str, task: str):
    """Send task to agent's queue for async processing"""
    
    queue_name = f"{agent_name}-queue"
    
    async with service_bus_client.get_sender(queue_name) as sender:
        message = ServiceBusMessage(
            body=json.dumps({"task": task}),
            content_type="application/json"
        )
        await sender.send_messages(message)
```

## 📚 References

- [Travel Agent Implementation](../agents/travel_agent/main.py)
- [Orchestrator Implementation](../agents/orchestrator/main.py)
- [A2A vs MCP Comparison](./A2A_VS_MCP.md)

## 🤝 Contributing

To extend the A2A protocol:

1. **Document new capabilities**: Update agent card format
2. **Implement in orchestrator**: Add routing logic
3. **Test discovery**: Ensure agents are found correctly
4. **Deploy**: Update Kubernetes configs
