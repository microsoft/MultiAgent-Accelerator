# Currency MCP Server

Model Context Protocol (MCP) server providing **currency exchange tools** using the **Frankfurter API**.

## 🔧 Tools Provided

### 1. `get_exchange_rate`
Get the current or historical exchange rate between two currencies.

**Parameters:**
- `currency_from` (string): Source currency code (e.g., 'USD')
- `currency_to` (string): Target currency code (e.g., 'EUR')
- `date` (string, optional): Date in YYYY-MM-DD format or 'latest' (default)

**Example:**
```json
{
  "currency_from": "USD",
  "currency_to": "EUR",
  "date": "latest"
}
```

**Response:**
```
Exchange rate on 2025-11-10: 1 USD = 0.9234 EUR
```

---

### 2. `convert_currency`
Convert an amount from one currency to another.

**Parameters:**
- `amount` (number): Amount to convert
- `currency_from` (string): Source currency code
- `currency_to` (string): Target currency code
- `date` (string, optional): Date for historical conversion

**Example:**
```json
{
  "amount": 500,
  "currency_from": "USD",
  "currency_to": "EUR",
  "date": "latest"
}
```

**Response:**
```
Conversion on 2025-11-10:
500.00 USD = 461.70 EUR
Exchange rate: 1 USD = 0.9234 EUR
```

---

### 3. `get_supported_currencies`
Get a list of all supported currency codes.

**Parameters:** None

**Response:**
```
Supported currencies:
  AUD: Australian Dollar
  BGN: Bulgarian Lev
  BRL: Brazilian Real
  CAD: Canadian Dollar
  CHF: Swiss Franc
  CNY: Chinese Renminbi Yuan
  ...
```

---

## 🚀 Usage

### Standalone Testing

**1. Install dependencies:**
```bash
cd mcp_servers/currency_mcp
pip install -r requirements.txt
```

**2. Run the server:**
```bash
python server.py
```

### With Travel Agent

The Travel Agent will connect to this MCP server as a tool:

```python
from agent_framework import ChatAgent, MCPStreamableHTTPTool

async with (
    MCPStreamableHTTPTool(
        name="Currency Tools",
        url="http://currency-mcp:8001"
    ) as currency_tools,
    ChatAgent(
        chat_client=...,
        tools=[currency_tools]
    ) as agent,
):
    result = await agent.run("Convert 500 USD to EUR")
```

---

## 🐳 Docker

**Build:**
```bash
docker build -t currency-mcp:latest .
```

**Run:**
```bash
docker run -p 8001:8001 currency-mcp:latest
```

---

## ☸️ Kubernetes Deployment

See `k8s/currency-mcp-deployment.yaml` for full deployment manifest.

**Deploy:**
```bash
kubectl apply -f k8s/currency-mcp-deployment.yaml
```

**Verify:**
```bash
kubectl get pods -n multiagent | grep currency-mcp
kubectl logs -f deployment/currency-mcp -n multiagent
```

---

## 🧪 Testing Tools

### Manual Test (Python)

```python
import asyncio
import httpx

async def test_exchange_rate():
    # Call the Frankfurter API directly
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.frankfurter.app/latest",
            params={"from": "USD", "to": "EUR"}
        )
        print(response.json())

asyncio.run(test_exchange_rate())
```

### cURL Test

```bash
# Get current USD to EUR rate
curl "https://api.frankfurter.app/latest?from=USD&to=EUR"

# Convert 500 USD to EUR
curl "https://api.frankfurter.app/latest?amount=500&from=USD&to=EUR"

# Get supported currencies
curl "https://api.frankfurter.app/currencies"
```

---

## 📚 API Reference

**Frankfurter API:**
- Docs: https://www.frankfurter.app/docs/
- Base URL: `https://api.frankfurter.app`
- Free, no API key required
- Historical rates from 1999-01-04
- Updates daily around 16:00 CET

**Supported Currencies:**
30+ currencies including USD, EUR, GBP, JPY, CNY, CAD, AUD, CHF, etc.

---

## 🔍 Troubleshooting

### Server not starting
```bash
# Check Python version
python --version  # Should be 3.11+

# Install dependencies
pip install -r requirements.txt

# Run with debug logging
python server.py
```

### API errors
```bash
# Test Frankfurter API directly
curl https://api.frankfurter.app/latest

# Check rate limits (none for Frankfurter)
```

### MCP connection issues
```bash
# Verify MCP stdio interface
python -c "from mcp.server.stdio import stdio_server; print('MCP OK')"
```

---

## 📊 Monitoring

### Logs
```bash
# Local
python server.py

# Kubernetes
kubectl logs -f deployment/currency-mcp -n multiagent
```

### Health
```bash
# Check if running
kubectl get pods -n multiagent | grep currency-mcp
```

---

## 🛠️ Development

### Add New Tool

Edit `server.py` and add to `list_tools()`:

```python
Tool(
    name="my_new_tool",
    description="What it does",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {"type": "string"}
        }
    }
)
```

Then implement the handler in `call_tool()`.

---

**Questions?** See the main README or check MCP documentation at https://modelcontextprotocol.io/
