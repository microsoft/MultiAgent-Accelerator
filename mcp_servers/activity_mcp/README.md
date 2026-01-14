# Activity MCP Server

Model Context Protocol (MCP) server providing **travel activity planning tools** for itineraries, restaurants, and attractions.

## 🔧 Tools Provided

### 1. `create_itinerary`
Create a detailed day-by-day travel itinerary.

**Parameters:**
- `destination` (string): City name (e.g., 'Paris', 'Tokyo', 'Rome')
- `duration_days` (integer): Number of days
- `budget` (string, optional): 'budget', 'moderate', or 'luxury' (default: 'moderate')
- `interests` (array, optional): List of interests (e.g., ['culture', 'food'])

**Example:**
```json
{
  "destination": "Paris",
  "duration_days": 3,
  "budget": "moderate",
  "interests": ["culture", "food", "history"]
}
```

**Response:**
Returns a formatted itinerary with morning, afternoon, and evening activities for each day.

---

### 2. `suggest_restaurants`
Get restaurant recommendations for a location.

**Parameters:**
- `location` (string): City name
- `cuisine_type` (string, optional): Preferred cuisine
- `budget` (string, optional): 'budget', 'moderate', or 'luxury'

**Example:**
```json
{
  "location": "Tokyo",
  "cuisine_type": "sushi",
  "budget": "moderate"
}
```

---

### 3. `find_attractions`
Find tourist attractions and sightseeing spots.

**Parameters:**
- `location` (string): City name
- `attraction_type` (string, optional): Type filter (e.g., 'museum', 'monument')

**Example:**
```json
{
  "location": "Rome",
  "attraction_type": "historic"
}
```

---

### 4. `plan_day_trip`
Plan a complete day trip with timing and activities.

**Parameters:**
- `destination` (string): Destination city
- `start_time` (string, optional): Start time (default: '09:00')
- `budget` (string, optional): Budget for the day

**Example:**
```json
{
  "destination": "Paris",
  "start_time": "09:00",
  "budget": "$100"
}
```

---

## 📊 Data Coverage

Currently includes data for:
- **Paris** 🇫🇷
- **Tokyo** 🇯🇵
- **Rome** 🇮🇹

### Restaurants per City
- 3+ restaurants with cuisine, price, and ratings

### Attractions per City
- 4+ attractions with type, duration, and pricing

---

## 🚀 Usage

### Standalone Testing

```bash
cd mcp_servers/activity_mcp
pip install -r requirements.txt
python server.py
```

### With Travel Agent

```python
from agent_framework import ChatAgent, MCPStreamableHTTPTool

async with (
    MCPStreamableHTTPTool(
        name="Activity Planning",
        url="http://activity-mcp:8002"
    ) as activity_tools,
    ChatAgent(
        chat_client=...,
        tools=[activity_tools]
    ) as agent,
):
    result = await agent.run("Plan a 3-day trip to Paris")
```

---

## 🐳 Docker

**Build:**
```bash
docker build -t activity-mcp:latest .
```

**Run:**
```bash
docker run -p 8002:8002 activity-mcp:latest
```

---

## ☸️ Kubernetes

**Deploy:**
```bash
kubectl apply -f k8s/activity-mcp-deployment.yaml
```

**Verify:**
```bash
kubectl get pods -n multiagent | grep activity-mcp
kubectl logs -f deployment/activity-mcp -n multiagent
```

---

## 🛠️ Extending the Server

### Add New Cities

Edit `server.py` and add to `restaurant_db` and `attractions_db`:

```python
self.restaurant_db = {
    # ... existing cities ...
    "barcelona": [
        {"name": "El Xampanyet", "cuisine": "Tapas", "price": "€€", "rating": 4.6},
        # ... more restaurants
    ],
}

self.attractions_db = {
    # ... existing cities ...
    "barcelona": [
        {"name": "Sagrada Familia", "type": "Church", "duration": "2-3 hours", "price": "€26"},
        # ... more attractions
    ],
}
```

### Add New Tools

Add to `list_tools()` in `_setup_handlers()`:

```python
Tool(
    name="book_tickets",
    description="Book tickets for attractions",
    inputSchema={
        "type": "object",
        "properties": {
            "attraction": {"type": "string"},
            "date": {"type": "string"},
            "quantity": {"type": "integer"}
        }
    }
)
```

### Connect to Real APIs

Replace sample data with API calls:

```python
import httpx

async def _suggest_restaurants(self, location: str, ...):
    # Call real restaurant API
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/restaurants?location={location}")
        data = response.json()
        # Process and return
```

---

## 🧪 Testing

### Manual Test

```python
import asyncio
from server import ActivityMCPServer

async def test():
    server = ActivityMCPServer()
    
    # Test create_itinerary
    result = await server._create_itinerary(
        destination="Paris",
        duration_days=2,
        budget="moderate",
        interests=["culture", "food"]
    )
    print(result)

asyncio.run(test())
```

---

## 📚 Future Enhancements

- [ ] Connect to Google Places API for real restaurant data
- [ ] Integrate with TripAdvisor for reviews
- [ ] Add weather information
- [ ] Include public transport directions
- [ ] Support for booking integration
- [ ] Multi-language support
- [ ] Price estimates in multiple currencies

---

## 🔍 Troubleshooting

### Server not starting
```bash
pip install -r requirements.txt
python server.py
```

### No data for location
The server currently has sample data for Paris, Tokyo, and Rome. For other cities, it will return a message suggesting online search.

---

**Questions?** See main README or MCP docs at https://modelcontextprotocol.io/
