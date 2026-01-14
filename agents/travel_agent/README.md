# Travel Agent 🌍

MAF-based travel planning agent with integrated Currency and Activity MCP tools.

## Overview

The Travel Agent provides comprehensive travel planning capabilities by combining:
- **Currency Tools**: Real-time exchange rates and currency conversion (30+ currencies)
- **Activity Tools**: Itinerary planning, restaurant recommendations, attraction discovery

## Architecture

```
┌─────────────────┐
│  Travel Agent   │ ← ChatAgent (MAF)
│   (FastAPI)     │
└────────┬────────┘
         │
         ├─────────────┐
         │             │
    ┌────▼─────┐  ┌───▼──────┐
    │ Currency │  │ Activity │
    │   MCP    │  │   MCP    │
    │  Tools   │  │  Tools   │
    └──────────┘  └──────────┘
```

## Features

### 1. Travel Planning
- Create multi-day itineraries
- Balance activities, dining, and sightseeing
- Consider budget constraints
- Provide timing and duration estimates

### 2. Currency Exchange
- Real-time exchange rates (via Frankfurter API)
- Convert between 30+ currencies
- Historical rate lookup
- Travel budget calculations

### 3. Restaurant Recommendations
- Filter by budget (budget/moderate/expensive)
- Consider cuisine preferences
- Provide ratings and pricing
- Include operating hours

### 4. Attraction Discovery
- Museums, landmarks, cultural sites
- Activity duration estimates
- Entry fees and pricing
- Best times to visit

## Quick Start

### Local Development

1. **Start MCP Servers** (required dependencies):

```bash
# Terminal 1: Currency MCP
cd mcp_servers/currency_mcp
python server.py

# Terminal 2: Activity MCP
cd mcp_servers/activity_mcp
python server.py
```

2. **Configure Environment**:

```bash
cd agents/travel_agent
cp .env.template .env
# Edit .env with your Azure OpenAI credentials
```

3. **Install Dependencies**:

```bash
# Using uv (recommended)
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

4. **Run the Agent**:

```bash
python main.py
```

The agent will start on `http://localhost:8080`

### Test the Agent

```bash
# Check health
curl http://localhost:8080/health

# Get agent card (A2A protocol)
curl http://localhost:8080/.well-known/agent.json

# Execute a task
curl -X POST http://localhost:8080/task \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Plan a 2-day trip to Paris with a budget of $1000",
    "user_id": "test_user"
  }'
```

## Example Requests

### Travel Planning
```json
{
  "task": "Create a 3-day itinerary for Tokyo with a budget of $1500"
}
```

### Currency Conversion
```json
{
  "task": "How much is 500 USD in EUR?"
}
```

### Restaurant Recommendations
```json
{
  "task": "Recommend affordable restaurants in Rome"
}
```

### Day Trip Planning
```json
{
  "task": "Plan a day trip in Paris starting at 9 AM with a budget of $150"
}
```

## API Endpoints

### POST /task
Execute a travel planning task

**Request**:
```json
{
  "task": "string (required)",
  "user_id": "string (optional)"
}
```

**Response**:
```json
{
  "result": "string",
  "agent": "travel_agent"
}
```

### GET /health
Health check endpoint

### GET /.well-known/agent.json
A2A protocol agent card for discovery

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | Required |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment name | `gpt-4o` |
| `CURRENCY_MCP_URL` | Currency MCP server URL | `http://localhost:8001` |
| `ACTIVITY_MCP_URL` | Activity MCP server URL | `http://localhost:8002` |
| `PORT` | Agent listening port | `8080` |

## Docker Deployment

### Build Image
```bash
docker build -t travel-agent:latest .
```

### Run Container
```bash
docker run -d \
  --name travel-agent \
  -p 8080:8080 \
  -e AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com" \
  -e AZURE_OPENAI_DEPLOYMENT="gpt-4o" \
  -e CURRENCY_MCP_URL="http://currency-mcp:8001" \
  -e ACTIVITY_MCP_URL="http://activity-mcp:8002" \
  travel-agent:latest
```

## Kubernetes Deployment

The agent is designed to run in AKS with:
- **Managed Identity**: For Azure OpenAI authentication
- **Service Discovery**: Connect to MCP servers via K8s services
- **Health Probes**: Kubernetes health checks

Example deployment coming in `k8s/travel-agent-deployment.yaml`

## MCP Tool Integration

The agent uses `MCPStreamableHTTPTool` from MAF to connect to MCP servers:

```python
currency_tool = MCPStreamableHTTPTool(
    base_url=CURRENCY_MCP_URL,
    name="currency_tools",
    description="Currency exchange tools..."
)

activity_tool = MCPStreamableHTTPTool(
    base_url=ACTIVITY_MCP_URL,
    name="activity_tools",
    description="Travel activity tools..."
)

travel_agent = ChatAgent(
    tools=[currency_tool, activity_tool],
    instructions="You are a helpful Travel Planning Assistant..."
)
```

## A2A Protocol Support

The agent exposes an **Agent Card** at `/.well-known/agent.json` for discovery by:
- Orchestrator agent
- Other agents in the system
- External systems using A2A protocol

The card includes:
- Agent capabilities and skills
- Example queries
- Supported locations
- API endpoints
- MCP tool metadata

## Supported Locations

Currently has detailed data for:
- 🇫🇷 **Paris**: 4 attractions, 3 restaurants
- 🇯🇵 **Tokyo**: 4 attractions, 3 restaurants
- 🇮🇹 **Rome**: 4 attractions, 3 restaurants

*Note*: The agent will work for other locations but with limited sample data. The Activity MCP can be extended with more cities.

## Troubleshooting

### Agent fails to start
- Check MCP servers are running on correct ports
- Verify Azure OpenAI credentials in `.env`
- Check network connectivity to MCP servers

### "Agent not initialized" error
- MCP servers must be running before starting the agent
- Check logs for MCP connection errors
- Verify URLs in environment variables

### Currency conversion fails
- Currency MCP needs internet access for Frankfurter API
- Check firewall/proxy settings
- Verify currency codes are supported (see `/get_supported_currencies`)

## Next Steps

After the Travel Agent is running:
1. Create Orchestrator agent to coordinate multiple agents
2. Deploy to AKS with Kubernetes manifests
3. Add more MCP tools for flights, hotels, weather
4. Extend Activity MCP with more cities
5. Integrate with Azure Service Bus for async tasks

## Related Components

- **Currency MCP**: `mcp_servers/currency_mcp/`
- **Activity MCP**: `mcp_servers/activity_mcp/`
- **External Agent Template**: `agents/external_agent/`
- **Orchestrator** (coming): `agents/orchestrator/`
