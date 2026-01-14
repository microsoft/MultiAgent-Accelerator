# Agents - Microsoft Agent Framework Implementation

This directory contains all agents built with **Microsoft Agent Framework (MAF)**.

## 🎯 Agents Overview

### 1. **Orchestrator** (`orchestrator/`)
**Main coordinator** that receives tasks and delegates to specialist agents.

**Key Features:**
- Receives messages from **Azure Service Bus**
- Discovers agents via **A2A Protocol** (AgentCard)
- Delegates tasks based on agent capabilities
- Supports external A2A-compliant agents

**Technologies:**
- `agent_framework.a2a.A2AAgent`
- `a2a.client.A2ACardResolver`
- Azure Service Bus with Managed Identity

**Endpoints:**
- Service Bus Queue: `orchestrator-queue` (input)
- Service Bus Queue: `agent-responses` (output)

---

### 2. **Travel Agent** (`travel_agent/`)
**Specialist agent** for travel planning with currency and activity tools.

**Key Features:**
- Currency conversion via Frankfurter API
- Trip planning and recommendations
- Itinerary creation
- Uses MCP servers for tools

**Technologies:**
- `agent_framework.ChatAgent`
- `agent_framework.azure.AzureAIAgentClient`
- `agent_framework.MCPStreamableHTTPTool`

**Tools (MCP Servers):**
- Currency MCP (port 8001)
- Activity MCP (port 8002)

**Endpoints:**
- HTTP: `http://travel-agent:8000`
- AgentCard: `http://travel-agent:8000/.well-known/agent.json`

---

### 3. **External Agent** (`external_agent/`)
**Placeholder/guide** for integrating external A2A-compliant agents.

**Key Features:**
- Documentation for connecting external agents
- AgentCard template
- Integration examples
- Deployment guide

**Purpose:**
- Connect third-party A2A agents
- Integrate enterprise agents
- Extend orchestrator capabilities

**Resources:**
- See `external_agent/README.md` for detailed integration guide

---

## 🔧 Development Guide

### Adding a New Agent

1. **Create directory structure:**
```bash
mkdir -p agents/my_agent/.well-known
cd agents/my_agent
```

2. **Create `main.py`:**
```python
from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential

async def main():
    async with (
        DefaultAzureCredential() as credential,
        ChatAgent(
            chat_client=AzureAIAgentClient(async_credential=credential),
            name="MyAgent",
            instructions="You are a helpful assistant...",
        ) as agent,
    ):
        result = await agent.run("Hello!")
        print(result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

3. **Create `requirements.txt`:**
```
agent-framework>=1.0.0b251108
azure-identity>=1.26.0
python-dotenv>=1.2.1
```

4. **Create `Dockerfile`:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

5. **Create AgentCard (`.well-known/agent.json`):**
```json
{
  "name": "MyAgent",
  "description": "Description of capabilities",
  "url": "http://my-agent:8000/",
  "version": "1.0.0",
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text"],
  "capabilities": {
    "streaming": true
  },
  "skills": [
    {
      "id": "my_skill",
      "name": "My Skill",
      "description": "What this agent can do",
      "tags": ["tag1", "tag2"]
    }
  ]
}
```

---

## 🧪 Local Testing

### Test Individual Agent

```bash
cd agents/travel_agent
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export AZURE_OPENAI_ENDPOINT="https://multiagent-dev-openai.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"

python main.py
```

### Test with Docker

```bash
cd agents/travel_agent
docker build -t travel-agent:local .
docker run -p 8000:8000 \
  -e AZURE_OPENAI_ENDPOINT="..." \
  travel-agent:local
```

---

## 🔐 Authentication

All agents use **Azure Managed Identity**:

```python
from azure.identity.aio import DefaultAzureCredential

# For local development (uses Azure CLI credentials)
credential = DefaultAzureCredential()

# For AKS deployment (uses workload identity)
# Automatically configured via pod annotations
```

---

## 🚀 Deployment

### Build and Push

```bash
# Build all agents
./scripts/build-and-push.sh

# Or build individual agent
cd agents/travel_agent
docker build -t multiagentdevacr.azurecr.io/travel-agent:latest .
docker push multiagentdevacr.azurecr.io/travel-agent:latest
```

### Deploy to AKS

```bash
# Deploy all agents
kubectl apply -f k8s/

# Or deploy individual agent
kubectl apply -f k8s/travel-agent-deployment.yaml
```

---

## 📊 Monitoring

### View Logs

```bash
# Orchestrator logs
kubectl logs -f deployment/orchestrator -n multiagent

# Travel Agent logs
kubectl logs -f deployment/travel-agent -n multiagent
```

### Check Health

```bash
# Check if AgentCard is accessible
curl http://travel-agent:8000/.well-known/agent.json

# Check pod status
kubectl get pods -n multiagent
```

---

## 🔍 Debugging

### Common Issues

**1. Authentication errors:**
```bash
# Check managed identity assignment
az aks show -n multiagent-dev-aks -g multiagent-dev-rg \
  --query "identityProfile.kubeletidentity.clientId"

# Verify role assignments
az role assignment list --assignee <kubelet-identity-id>
```

**2. MCP connection errors:**
```bash
# Check if MCP servers are running
kubectl get svc -n multiagent | grep mcp

# Test connectivity from agent pod
kubectl exec -it <agent-pod> -- curl http://currency-mcp:8001/health
```

**3. Service Bus errors:**
```bash
# Check Service Bus connection
az servicebus namespace show -n multiagent-dev-servicebus -g multiagent-dev-rg

# Test queue access
az servicebus queue show -n orchestrator-queue \
  --namespace-name multiagent-dev-servicebus -g multiagent-dev-rg
```

---

## 📚 Resources

- [MAF Documentation](https://github.com/microsoft/agent-framework)
- [A2A Protocol Spec](https://a2a-protocol.org/latest/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Azure AI Foundry](https://learn.microsoft.com/azure/ai-foundry/)

---

**Questions?** Check `_archived/Examples/` for reference implementations.
