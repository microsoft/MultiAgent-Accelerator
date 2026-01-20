# Multi-Agent System with Microsoft Agent Framework on AKS or ACA

[![Deploy MCP Services to AKS](https://github.com/darkanita/MultiAgent-AKS-MAF/actions/workflows/deploy-mcp-to-aks.yml/badge.svg)](https://github.com/darkanita/MultiAgent-AKS-MAF/actions/workflows/deploy-mcp-to-aks.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready multi-agent orchestration system built with **Microsoft Agent Framework (MAF)**, **Agent-to-Agent (A2A) Protocol**, **Model Context Protocol (MCP)**, and **Azure Kubernetes Service (AKS) or Azure Container Apps (ACA)**.

## 🏗️ Architecture

```
                        ┌─────────────────────┐
                        │   Streamlit UI      │
                        │   (LoadBalancer)    │
                        └──────────┬──────────┘
                                   │
                                   │ HTTP
                                   │
                        ┌──────────▼──────────┐
                        │   Orchestrator      │
                        │   (LoadBalancer)    │
                        │   AKS (2 replicas)  │
                        └──────────┬──────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
         A2A Simple │   A2A Simple │   A2A SDK    │ A2A SDK
                    │              │   (JSON-RPC) │ (JSON-RPC)
         ┌──────────▼─────┐ ┌─────▼──────┐ ┌────▼─────┐ ┌────▼─────┐
         │ Travel Agent   │ │ Streamlit  │ │ Burger   │ │ Pizza    │
         │ (AKS or ACA)   │ │(AKS or ACA)│ │ Agent    │ │ Agent    │
         │ LoadBalancer   │ │            │ │ (GCP)    │ │ (GCP)    │
         └────────┬───────┘ └────────────┘ └──────────┘ └──────────┘
                  │
          MCP StreamableHTTP
                  │
         ┌────────┴────────┐
         │                 │
  ┌──────▼───────┐  ┌─────▼────────┐
  │ Currency MCP │  │ Activity MCP │
  │ (AKS or ACA) │  │ (AKS or ACA) │
  │ Port 8001    │  │ Port 8002    │
  └──────────────┘  └──────────────┘
```

### Components

- **Streamlit UI** (AKS or ACA): User interface for multi-agent interaction
- **Orchestrator** (AKS or ACA): Routes tasks to appropriate agents using A2A protocol
- **Travel Agent** (AKS or ACA): Handles travel planning, currency conversion, restaurant recommendations
- **Burger Agent** (GCP Cloud Run): Processes burger orders - [Source Code](https://github.com/alphinside/purchasing-concierge-intro-a2a-codelab-starter)
- **Pizza Agent** (GCP Cloud Run): Processes pizza orders - [Source Code](https://github.com/alphinside/purchasing-concierge-intro-a2a-codelab-starter)
- **Currency MCP** (AKS or ACA): Real-time exchange rates via Frankfurter API
- **Activity MCP** (AKS or ACA): Travel itinerary and activity planning

### Protocol Support

The orchestrator implements **dual protocol support**:

1. **A2A Simple Format** (Travel Agent):
   ```json
   {"task": "...", "user_id": "..."}
   ```

2. **A2A SDK JSON-RPC Format** (GCP Agents - Burger & Pizza):
   ```json
   {
     "id": "msg-123",
     "params": {
       "message": {
         "role": "user",
         "parts": [{"type": "text", "text": "..."}]
       }
     }
   }
   ```

## 📁 Project Structure

```
MultiAgent-AKS-MAF/
├── agents/                      # MAF-based agents
│   ├── orchestrator/           # Main orchestrator (A2A + Service Bus)
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── travel_agent/           # Travel planning agent
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .well-known/
│   │       └── agent.json      # AgentCard for A2A discovery
│   │
│   └── external_agent/         # External A2A agent integration
│       ├── README.md          # Integration guide
│       └── .well-known/
│           └── agent.json     # AgentCard template
│
├── mcp_servers/                # Model Context Protocol servers
│   ├── currency_mcp/          # Currency exchange tools
│   │   ├── server.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── activity_mcp/          # Activity planning tools
│       ├── server.py
│       ├── requirements.txt
│       └── Dockerfile
│
├── infrastructure/             # Azure infrastructure (Bicep)
│   └── bicep/
│       ├── main-rg.bicep      # Main resource group deployment
│       └── modules/           # Individual Azure resources
│
├── k8s/                       # Kubernetes manifests
│   ├── orchestrator-deployment.yaml
│   ├── travel-agent-deployment.yaml
│   ├── currency-mcp-deployment.yaml
│   └── activity-mcp-deployment.yaml
│
├── scripts/                   # Deployment scripts
│   ├── deploy-infrastructure.sh
│   ├── build-and-push.sh
│   └── deploy-to-aks.sh
│
└── _archived/                 # Old code (for reference)
```

## 🚀 Key Technologies

- **Microsoft Agent Framework (MAF)**: Agent orchestration and communication
- **Azure AI Foundry**: GPT-4o, GPT-4o-mini models
- **A2A Protocol**: Agent-to-Agent communication standard (Simple + SDK formats)
- **MCP (Model Context Protocol)**: Tool/plugin architecture
- **Azure Service Bus**: Message queue for external communication
- **Azure Kubernetes Service (AKS) or Azure Container Apps (ACA)**: Container orchestration
- **Google Cloud Run**: Serverless container hosting (for food ordering agents)
- **Azure Managed Identity**: Secure authentication

## ✨ Features

### Orchestrator
- ✅ Discovers agents via **A2A AgentCard** resolution
- ✅ **Dual Protocol Support**: A2A Simple + A2A SDK (JSON-RPC 2.0)
- ✅ Multi-cloud agent integration (AKS + GCP Cloud Run)
- ✅ Routes tasks based on keywords and agent capabilities
- ✅ Supports external A2A-compliant agents

### Travel Agent (AKS or ACA)
- ✅ Built with **ChatAgent** from MAF
- ✅ Uses **MCP tools** for currency and activity planning
- ✅ Exposes **AgentCard** at `/.well-known/agent.json`
- ✅ Supports **Azure Managed Identity**
- ✅ Real-time currency conversion (30+ currencies)
- ✅ Restaurant recommendations
- ✅ Multi-day itinerary planning

### Food Ordering Agents (GCP Cloud Run)
- ✅ **Burger Agent**: Processes burger orders using A2A SDK format
- ✅ **Pizza Agent**: Processes pizza orders using A2A SDK format
- ✅ Source: [Purchasing Concierge A2A Codelab](https://github.com/alphinside/purchasing-concierge-intro-a2a-codelab-starter)
- ✅ Deployed on Google Cloud Run
- ✅ Integrated via A2A JSON-RPC 2.0 protocol

### Streamlit Web UI (AKS or ACA)
- ✅ User-friendly interface for multi-agent interaction
- ✅ Quick test buttons for common tasks
- ✅ Contextual follow-up questions
- ✅ Clean response formatting with expandable raw JSON
- ✅ Support for all agent types (travel, burger, pizza)

### MCP Servers (AKS or ACA)
- ✅ **Currency MCP**: Exchange rates via Frankfurter API
- ✅ **Activity MCP**: Trip planning, recommendations

## 🔧 Prerequisites

- Azure subscription
- Azure CLI (`az`)
- kubectl
- Docker
- Python 3.11+

## 📦 Quick Start

### 1. Deploy Infrastructure

```bash
# Login to Azure
az login

# Deploy infrastructure
./scripts/deploy-infrastructure.sh
```

This creates:
- Azure OpenAI (with gpt-4o, gpt-4o-mini, gpt-35-turbo)
- Azure Service Bus
- Azure Key Vault
- AKS Cluster with Workload Identity
- Azure Container Registry

### 2. Deploy to AKS

#### Option A: GitHub Actions (Recommended) 🚀

See [GitHub Actions Deployment Guide](docs/GITHUB_ACTIONS_DEPLOYMENT.md) for automated CI/CD setup.

Quick setup:
```bash
# Create service principal with federated credentials
# See .github/DEPLOYMENT_QUICKSTART.md for complete script

# Add GitHub Secrets (Settings → Secrets):
# - AZURE_CLIENT_ID
# - AZURE_TENANT_ID  
# - AZURE_SUBSCRIPTION_ID

# Push to main branch → auto-deploys!
git push origin main
```

#### Option B: Manual Deployment

```bash
# Build and deploy all services
./scripts/deploy-to-aks.sh
```

This will:
- Build Docker images for all 3 services
- Push to Azure Container Registry
- Deploy to AKS with Workload Identity
- Configure session affinity for MCP servers
- Wait for pods and get external IP

## 🧪 Testing

### Test the Complete System

**Via Streamlit UI** (Recommended):
```
Open browser: http://<STREAMLIT_UI_IP>

Quick Test Buttons:
- 🍔 Order Burgers → Routes to Burger Agent (GCP)
- 🍕 Order Pizza → Routes to Pizza Agent (GCP)
- 💱 Convert Currency → Routes to Travel Agent (AKS)
- ✈️ Plan Trip → Routes to Travel Agent (AKS)
```

### Test Orchestrator Directly

Get the orchestrator IP: `kubectl get svc orchestrator-service -n multiagent`

```bash
# Travel Agent - Currency conversion
curl -X POST http://<ORCHESTRATOR_IP>/task \
  -H "Content-Type: application/json" \
  -d '{"task": "Convert 100 USD to EUR", "user_id": "test"}'

# Travel Agent - Trip planning
curl -X POST http://<ORCHESTRATOR_IP>/task \
  -H "Content-Type: application/json" \
  -d '{"task": "Plan a 3-day trip to Paris", "user_id": "test"}'

# Burger Agent (GCP)
curl -X POST http://<ORCHESTRATOR_IP>/task \
  -H "Content-Type: application/json" \
  -d '{"task": "I want 2 classic cheeseburgers", "user_id": "test"}'

# Pizza Agent (GCP)
curl -X POST http://<ORCHESTRATOR_IP>/task \
  -H "Content-Type: application/json" \
  -d '{"task": "Order 1 pepperoni pizza", "user_id": "test"}'

# Check discovered agents
curl http://<ORCHESTRATOR_IP>/agents
```

### Test Locally

```bash
# Start Currency MCP
cd mcp_servers/currency_mcp
python server.py

# Test in another terminal
curl http://localhost:8001/health
```

### Test Travel Agent

```bash
cd agents/travel_agent
python main.py

# Query the agent
curl -X POST http://localhost:8080/task \
  -H "Content-Type: application/json" \
  -d '{"task": "Convert 500 USD to EUR", "user_id": "local-test"}'
```

### Test Orchestrator Agent Discovery

```bash
cd agents/orchestrator
# Set environment variable with agent endpoints
export AGENT_ENDPOINTS="http://travel-agent-service,https://burger-agent-286879789617.us-central1.run.app,https://pizza-agent-286879789617.us-central1.run.app"
python main.py

# Check discovered agents
curl http://localhost:8000/agents
```

## 🔐 Security

- **Managed Identity**: All Azure resources use managed identities
- **RBAC**: Service Bus and Key Vault use role-based access
- **No API Keys**: Credentials stored in Key Vault
- **Network Isolation**: Private endpoints for Azure services

## 📊 Monitoring

- **Application Insights**: Telemetry and logging
- **Azure Monitor**: Infrastructure metrics
- **Service Bus Metrics**: Message queue monitoring

## 🛠️ Development

### Adding a New Agent

1. Create agent directory: `agents/my_agent/`
2. Implement using MAF `ChatAgent`
3. Create `agent.json` AgentCard
4. Build Docker image
5. Create K8s deployment manifest

### Adding MCP Tools

1. Create MCP server: `mcp_servers/my_tools/`
2. Implement tools following MCP spec
3. Register with Travel Agent
4. Deploy to AKS

## 📚 Resources

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [A2A Protocol](https://a2a-protocol.org/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Azure AI Foundry](https://learn.microsoft.com/azure/ai-foundry/)
- [GCP Food Ordering Agents (Burger & Pizza)](https://github.com/alphinside/purchasing-concierge-intro-a2a-codelab-starter)

## 🎯 Live Demo

Get the service IPs using:
```bash
kubectl get svc -n multiagent
```

Services:
- **Streamlit UI**: `streamlit-service` (LoadBalancer)
- **Orchestrator**: `orchestrator-service` (LoadBalancer)
- **Travel Agent**: `travel-agent-service` (LoadBalancer)
- **Burger Agent (GCP)**: External Cloud Run service
- **Pizza Agent (GCP)**: External Cloud Run service

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## 🙏 Acknowledgments

- **Microsoft Agent Framework Team** - Multi-agent orchestration framework
- **A2A Protocol Contributors** - Agent-to-Agent communication standard
- **Model Context Protocol** - Tool integration standard
- **Frankfurter API** - Free currency exchange data
- **[alphinside/purchasing-concierge-intro-a2a-codelab-starter](https://github.com/alphinside/purchasing-concierge-intro-a2a-codelab-starter)** - GCP food ordering agents

---

**Built with ❤️ using Microsoft Agent Framework + A2A Protocol**



