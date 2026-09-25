# Streamlit Web UI

A modern web interface for the Multi-Agent Orchestrator system built with Streamlit.

## Features

- 🤖 **Agent Discovery**: View all discovered agents and their skills
- 📝 **Task Submission**: Submit tasks in sync or async mode
- 🎯 **Smart Routing**: See which agent is automatically selected for your task
- 📊 **Real-time Monitoring**: Track task execution and responses
- 🌐 **Multi-Cloud Support**: Works with agents on AKS, GCP, and other platforms

## Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   cd web_ui
   pip install -r requirements.txt
   ```

2. **Configure orchestrator URL:**
   Set your orchestrator URL and shared API key:
   ```bash
   export ORCHESTRATOR_URL="http://localhost:8000"
   export MULTIAGENT_API_KEY="<shared-api-key>"
   ```

3. **Run locally:**
   ```bash
   streamlit run streamlit_app.py
   ```

4. **Open browser:**
   Navigate to http://localhost:8501

### Deploy to AKS

1. **Build and deploy:**
   ```bash
   bash scripts/deploy-streamlit-ui.sh
   ```

2. **Access the UI:**
   The Kubernetes service is internal by default. Use `kubectl port-forward` for development, or publish the UI through an authenticated ingress, Azure Application Gateway, or API Management.

3. **Manual deployment:**
   ```bash
   # Build and push image
   docker build -t acrmadev2jhf6weu.azurecr.io/streamlit-ui:latest web_ui/
   docker push acrmadev2jhf6weu.azurecr.io/streamlit-ui:latest
   
   # Deploy to Kubernetes
   kubectl apply -f k8s/streamlit-ui-deployment.yaml
   
   # Development access
   kubectl port-forward -n multiagent service/streamlit-ui-service 8501:80
   ```

## Usage

### Dashboard
- View all discovered agents
- See agent skills and capabilities
- Check agent metadata (discovery URL, base URL)

### Submit Task
- Enter task description
- Choose sync or async execution
- Optionally specify preferred agent
- View immediate responses (sync) or task IDs (async)

### Example Tasks

**For Travel Agent:**
- "Convert 100 USD to EUR"
- "Find restaurants in Tokyo"
- "Plan a 3-day trip to Paris"
- "Find tourist attractions in New York"

**For Illustration Agent:**
- "Create an illustration of a soccer stadium at sunset"
- "Generate an image of a futuristic stadium"
- "Illustrate a packed stadium during a game"

## Configuration

### Environment Variables

- `ORCHESTRATOR_URL`: URL of the orchestrator service (default: http://4.150.144.45)
- `MULTIAGENT_API_KEY` or `API_KEY`: shared API key sent to the orchestrator.

### Kubernetes Configuration

The deployment creates:
- **Deployment**: `streamlit-ui` with 1 replica
- **Service**: `streamlit-ui-service` (ClusterIP type)
- **Resource Limits**: 256Mi-512Mi memory, 100m-500m CPU
- **Health Checks**: Liveness and readiness probes on `/_stcore/health`

## Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────┐
│  Streamlit UI   │
│  (Port 8501)    │
└────────┬────────┘
         │ HTTP
         ▼
┌──────────────────┐      ┌──────────────┐
│  Orchestrator    │─────▶│ Travel Agent │
│  (Port 8000)     │      └──────────────┘
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ Illustration     │
│ Agent (GCP)      │
└──────────────────┘
```

## Troubleshooting

### UI not accessible
```bash
# Check pod status
kubectl get pods -n multiagent -l app=streamlit-ui

# Check logs
kubectl logs -n multiagent -l app=streamlit-ui

# Check service
kubectl get svc streamlit-ui-service -n multiagent
```

### Can't connect to orchestrator
1. Verify orchestrator is running:
   ```bash
   kubectl get pods -n multiagent -l app=orchestrator
   ```

2. Check orchestrator service:
   ```bash
   kubectl get svc orchestrator-service -n multiagent
   ```

3. Update `ORCHESTRATOR_URL` in the deployment or secrets

### Streamlit errors
```bash
# Restart deployment
kubectl rollout restart deployment/streamlit-ui -n multiagent

# Check health
kubectl port-forward -n multiagent service/streamlit-ui-service 8501:80
curl http://localhost:8501/_stcore/health
```

## Future Enhancements

- [ ] Real-time task monitoring with WebSocket
- [ ] Async response viewer integrated in UI
- [ ] Task history and analytics
- [ ] Agent performance metrics
- [ ] Custom agent configuration
- [ ] Multi-user support with authentication

## Development

### Project Structure
```
web_ui/
├── streamlit_app.py       # Main Streamlit application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container image definition
└── .streamlit/
    ├── config.toml       # Streamlit configuration
    └── secrets.toml      # Secrets (not in git)
```

### Adding New Features

1. Edit `streamlit_app.py`
2. Test locally with `streamlit run streamlit_app.py`
3. Rebuild and redeploy:
   ```bash
   bash scripts/deploy-streamlit-ui.sh
   ```

## License

Part of the Multi-Agent AKS MAF project.
