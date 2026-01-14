# Integrating GCP ADK Agents with AKS A2A Orchestrator

This guide shows how to integrate an agent built with Google's Agent Development Kit (ADK) in GCP with your Azure AKS-based A2A orchestrator.

## Overview

The A2A (Agent-to-Agent) protocol requires two key components:
1. **Agent Discovery**: `GET /.well-known/agent.json` - Returns agent capabilities
2. **Task Execution**: `POST /execute` or similar endpoint to process tasks

## Architecture

```
AKS Orchestrator (Azure) ──HTTP──> GCP Agent (Cloud Run/GKE)
                                    ├── /.well-known/agent.json
                                    └── /execute
```

---

## Step 1: Create A2A Wrapper for Your GCP Agent

### Option A: FastAPI Wrapper (Recommended)

```python
# gcp_agent_wrapper.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

# Import your ADK agent
# from your_adk_agent import process_task

app = FastAPI(title="GCP ADK Agent - A2A Compatible")

class TaskRequest(BaseModel):
    task: str
    user_id: str = "anonymous"
    context: dict = {}

class TaskResponse(BaseModel):
    result: str
    agent: str
    status: str = "completed"

# A2A Discovery Endpoint
@app.get("/.well-known/agent.json")
async def agent_discovery():
    """A2A protocol: Agent discovery endpoint"""
    return {
        "name": "gcp-flight-agent",  # Change to your agent name
        "description": "Flight booking agent running in GCP",
        "version": "1.0.0",
        "capabilities": [
            "flight_search",
            "booking",
            "price_comparison"
        ],
        "endpoints": {
            "execute": "/execute",
            "health": "/health"
        },
        "contact": {
            "location": "GCP Cloud Run",
            "region": os.getenv("GCP_REGION", "us-central1")
        }
    }

# Task Execution Endpoint
@app.post("/execute")
async def execute_task(request: TaskRequest) -> TaskResponse:
    """Execute task using ADK agent"""
    try:
        # Call your ADK agent here
        # result = await process_task(request.task, request.context)
        
        # Example - replace with actual ADK agent call
        result = f"Processed by GCP agent: {request.task}"
        
        return TaskResponse(
            result=result,
            agent="gcp-flight-agent",
            status="completed"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health Check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "gcp-adk-agent"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

### Option B: Flask Wrapper (Alternative)

```python
# gcp_agent_wrapper_flask.py
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/.well-known/agent.json", methods=["GET"])
def agent_discovery():
    return jsonify({
        "name": "gcp-adk-agent",
        "description": "ADK agent in GCP",
        "version": "1.0.0",
        "capabilities": ["your", "capabilities"],
        "endpoints": {
            "execute": "/execute"
        }
    })

@app.route("/execute", methods=["POST"])
def execute_task():
    data = request.json
    task = data.get("task", "")
    
    # Call your ADK agent
    result = f"Processed: {task}"
    
    return jsonify({
        "result": result,
        "agent": "gcp-adk-agent",
        "status": "completed"
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
```

---

## Step 2: Deploy to GCP

### Option A: Deploy to Cloud Run (Serverless - Recommended)

1. **Create Dockerfile**:

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run expects PORT environment variable
ENV PORT=8080

CMD ["python", "gcp_agent_wrapper.py"]
```

2. **requirements.txt**:

```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
# Add your ADK dependencies here
```

3. **Deploy to Cloud Run**:

```bash
# Set your GCP project
export GCP_PROJECT_ID="your-gcp-project"
export SERVICE_NAME="adk-agent"
export REGION="us-central1"

# Build and deploy
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --project=$GCP_PROJECT_ID

# Get the service URL
gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --format='value(status.url)'
```

### Option B: Deploy to GKE (Kubernetes)

1. **Build and push Docker image**:

```bash
export GCP_PROJECT_ID="your-gcp-project"
export IMAGE="gcr.io/$GCP_PROJECT_ID/adk-agent:latest"

# Build
docker build -t $IMAGE .

# Push to Google Container Registry
docker push $IMAGE
```

2. **Create Kubernetes deployment**:

```yaml
# gcp-agent-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gcp-adk-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: gcp-adk-agent
  template:
    metadata:
      labels:
        app: gcp-adk-agent
    spec:
      containers:
      - name: agent
        image: gcr.io/YOUR_PROJECT/adk-agent:latest
        ports:
        - containerPort: 8080
        env:
        - name: PORT
          value: "8080"
---
apiVersion: v1
kind: Service
metadata:
  name: gcp-adk-agent-service
spec:
  type: LoadBalancer
  selector:
    app: gcp-adk-agent
  ports:
  - port: 80
    targetPort: 8080
```

3. **Deploy**:

```bash
kubectl apply -f gcp-agent-deployment.yaml

# Get external IP
kubectl get service gcp-adk-agent-service
```

---

## Step 3: Configure AKS Orchestrator to Discover GCP Agent

### Method 1: Environment Variable (Simple)

Update your orchestrator deployment in AKS:

```yaml
# k8s/orchestrator-deployment.yaml
env:
- name: AGENT_ENDPOINTS
  value: "http://travel-agent-service/.well-known/agent.json,https://your-gcp-agent-url.run.app/.well-known/agent.json"
```

Then redeploy:

```bash
kubectl apply -f k8s/orchestrator-deployment.yaml
kubectl rollout restart deployment/orchestrator -n multiagent
```

### Method 2: ConfigMap (Better for Multiple Agents)

```yaml
# k8s/agent-registry-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: agent-registry
  namespace: multiagent
data:
  agents.json: |
    {
      "agents": [
        {
          "name": "travel-agent",
          "url": "http://travel-agent-service/.well-known/agent.json",
          "location": "aks"
        },
        {
          "name": "gcp-flight-agent",
          "url": "https://your-gcp-agent-url.run.app/.well-known/agent.json",
          "location": "gcp"
        }
      ]
    }
```

Update orchestrator to read from ConfigMap:

```python
# In agents/orchestrator/main.py
import json
import os

def load_agent_endpoints():
    """Load agent endpoints from environment or config file"""
    # Try config file first (from ConfigMap)
    config_file = os.getenv("AGENT_CONFIG_FILE", "/config/agents.json")
    if os.path.exists(config_file):
        with open(config_file) as f:
            config = json.load(f)
            return [agent["url"] for agent in config["agents"]]
    
    # Fallback to environment variable
    endpoints = os.getenv("AGENT_ENDPOINTS", "").split(",")
    return [e.strip() for e in endpoints if e.strip()]
```

Mount ConfigMap in deployment:

```yaml
# k8s/orchestrator-deployment.yaml
spec:
  template:
    spec:
      containers:
      - name: orchestrator
        volumeMounts:
        - name: agent-config
          mountPath: /config
          readOnly: true
        env:
        - name: AGENT_CONFIG_FILE
          value: "/config/agents.json"
      volumes:
      - name: agent-config
        configMap:
          name: agent-registry
```

---

## Step 4: Test Cross-Cloud Integration

### Test GCP Agent Discovery

```bash
# Test from your local machine
curl https://your-gcp-agent-url.run.app/.well-known/agent.json

# Should return:
# {
#   "name": "gcp-flight-agent",
#   "description": "...",
#   "capabilities": [...],
#   ...
# }
```

### Test Task Execution

```bash
curl -X POST https://your-gcp-agent-url.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Find flights from NYC to LAX",
    "user_id": "test-user"
  }'
```

### Test via Orchestrator

```bash
# Get orchestrator external IP
kubectl get svc orchestrator-service -n multiagent

# Send task to orchestrator (it will route to GCP agent if matched)
curl -X POST http://ORCHESTRATOR_IP/task \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Find flights from NYC to LAX"
  }'
```

### Check Orchestrator Discovered GCP Agent

```bash
# List all discovered agents
curl http://ORCHESTRATOR_IP/agents

# Should show both AKS and GCP agents
```

---

## Security Considerations

### 1. Authentication Between Clouds

**Option A: API Keys**

```python
# In GCP agent
@app.post("/execute")
async def execute_task(request: TaskRequest, api_key: str = Header(None)):
    if api_key != os.getenv("EXPECTED_API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    # ... process task
```

```python
# In AKS orchestrator
headers = {
    "X-API-Key": os.getenv("GCP_AGENT_API_KEY")
}
response = await client.post(agent_url, json=payload, headers=headers)
```

**Option B: OAuth 2.0 / OIDC**

```python
# Use Google Cloud IAM for authentication
from google.auth.transport.requests import Request
from google.oauth2 import id_token

@app.post("/execute")
async def execute_task(request: TaskRequest, authorization: str = Header(None)):
    try:
        # Verify token
        token = authorization.replace("Bearer ", "")
        id_info = id_token.verify_oauth2_token(
            token, 
            Request(), 
            os.getenv("EXPECTED_AUDIENCE")
        )
        # Token is valid
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 2. Network Security

**Option 1: Public Internet with HTTPS** (Simplest)
- Use Cloud Run with HTTPS (auto-provisioned)
- Use API keys or OAuth tokens

**Option 2: VPN Connection**
- Set up VPN between Azure and GCP
- Use private IPs

**Option 3: Cloud Interconnect** (Enterprise)
- Dedicated connection between Azure and GCP
- Higher bandwidth, lower latency

### 3. Restrict Access

**GCP Cloud Run - Allow only from Azure**:

```bash
# Get your AKS cluster's NAT Gateway IP
kubectl get svc -n kube-system

# In GCP, use Cloud Armor or VPC Service Controls
gcloud compute security-policies create azure-only \
  --description "Allow only from Azure AKS"

gcloud compute security-policies rules create 1000 \
  --security-policy azure-only \
  --src-ip-ranges "YOUR_AZURE_NAT_IP/32" \
  --action allow
```

---

## Example: Complete Integration

### GCP Agent (Cloud Run)

```python
# gcp_flight_agent.py
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import os

app = FastAPI()

class TaskRequest(BaseModel):
    task: str
    user_id: str = "anonymous"

@app.get("/.well-known/agent.json")
async def discovery():
    return {
        "name": "gcp-flight-agent",
        "description": "Flight search and booking agent in GCP",
        "version": "1.0.0",
        "capabilities": ["flight_search", "price_comparison", "booking"],
        "keywords": ["flight", "airplane", "travel", "booking"],
        "endpoints": {"execute": "/execute"}
    }

@app.post("/execute")
async def execute(
    request: TaskRequest,
    x_api_key: str = Header(None, alias="X-API-Key")
):
    # Verify API key
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401)
    
    # Your ADK agent logic here
    result = f"Found 5 flights from NYC to LAX for {request.user_id}"
    
    return {
        "result": result,
        "agent": "gcp-flight-agent",
        "status": "completed"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### AKS Orchestrator Update

```python
# In agents/orchestrator/main.py
import httpx

async def call_agent(agent_url: str, task: str, api_key: str = None):
    """Call agent with optional API key"""
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            agent_url,
            json={"task": task},
            headers=headers,
            timeout=30.0
        )
        return response.json()

# Load API keys from secrets
GCP_AGENT_API_KEY = os.getenv("GCP_AGENT_API_KEY")

# When calling GCP agent
result = await call_agent(
    gcp_agent_url, 
    task, 
    api_key=GCP_AGENT_API_KEY
)
```

---

## Deployment Checklist

- [ ] Wrap ADK agent with A2A protocol endpoints
- [ ] Deploy to GCP (Cloud Run or GKE)
- [ ] Get public HTTPS URL
- [ ] Test discovery endpoint: `GET /.well-known/agent.json`
- [ ] Test execute endpoint: `POST /execute`
- [ ] Store GCP agent URL in AKS ConfigMap or environment variable
- [ ] Update orchestrator to include GCP agent
- [ ] (Optional) Set up API key authentication
- [ ] (Optional) Configure Cloud Armor for IP filtering
- [ ] Redeploy orchestrator in AKS
- [ ] Test end-to-end: orchestrator → GCP agent

---

## Benefits of This Approach

✅ **Cloud-Agnostic**: A2A protocol works across any cloud  
✅ **Simple Integration**: Just HTTP endpoints  
✅ **Scalable**: Use Cloud Run auto-scaling  
✅ **Discoverable**: Orchestrator automatically finds capabilities  
✅ **Flexible**: Easy to add more agents from any cloud  

## Next Steps

1. **Multi-Cloud Monitoring**: Use Azure Monitor + Google Cloud Operations
2. **Fallback Strategy**: If GCP agent is down, route to backup
3. **Load Balancing**: Deploy GCP agent in multiple regions
4. **Caching**: Cache agent discovery responses to reduce latency
