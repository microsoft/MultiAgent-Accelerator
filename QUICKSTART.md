# Quick Start Guide

Get the Multi-Agent System running in 15 minutes!

## Prerequisites

- Azure subscription with permissions to create resources
- Azure CLI installed and configured
- kubectl installed
- Git installed

## Step 1: Clone and Setup

```bash
git clone <your-repo-url>
cd MultiAgent-AKS-MAF
```

## Step 2: Deploy Infrastructure

### Option A: Manual Deployment (Quick)

```bash
# Login to Azure
az login

# Run deployment script
chmod +x scripts/deploy-infrastructure.sh
./scripts/deploy-infrastructure.sh

# Store secrets in Key Vault
chmod +x scripts/store-secrets.sh
./scripts/store-secrets.sh
```

### Option B: GitHub Actions (Automated)

1. Fork this repository
2. Configure GitHub Secrets:
   - `AZURE_CLIENT_ID`
   - `AZURE_TENANT_ID`
   - `AZURE_SUBSCRIPTION_ID`
3. Push to main branch - deployment will start automatically

See [INFRASTRUCTURE_DEPLOYMENT.md](docs/INFRASTRUCTURE_DEPLOYMENT.md) for detailed instructions.

## Step 3: Verify Infrastructure

```bash
# Load deployment info
source infrastructure/bicep/deployment-info.env

# Check AKS cluster
kubectl get nodes

# Verify resources
az resource list --resource-group $RESOURCE_GROUP --output table
```

## Step 4: What's Next?

After infrastructure is deployed:

1. **Build Agents** - Implement agent logic in Python
2. **Create MCP Servers** - Define agent capabilities
3. **Build Web UI** - Create the testing interface
4. **Deploy Applications** - Push containers and deploy to AKS

## Infrastructure Created

Your deployment includes:

- ✅ AKS Cluster (3 nodes)
- ✅ Azure Container Registry
- ✅ Azure AI Foundry + OpenAI (GPT-4, GPT-3.5)
- ✅ Azure Service Bus (A2A messaging)
- ✅ Application Insights (monitoring)
- ✅ Key Vault (secrets)
- ✅ Log Analytics (logging)

## Cost Estimate

**Development Environment (~$150-200/month)**
- AKS: ~$70/month (D4s_v3 nodes)
- Azure OpenAI: Pay-per-use (~$0.03/1K tokens)
- Service Bus: ~$10/month (Standard)
- Storage & Monitoring: ~$20/month

**Production Environment (~$500-800/month)**
- Larger AKS cluster with auto-scaling
- Premium tier services
- Enhanced monitoring and backups

## Troubleshooting

### Deployment fails?
```bash
# Check deployment status
az deployment sub show --name <deployment-name>

# View error details
az deployment sub operation list --name <deployment-name>
```

### Can't connect to AKS?
```bash
# Reset credentials
az aks get-credentials \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_CLUSTER \
  --overwrite-existing
```

### Need to clean up?
```bash
# Delete everything
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

## Next Steps

📖 Read the full documentation:
- [Infrastructure Deployment](docs/INFRASTRUCTURE_DEPLOYMENT.md)
- [Architecture Overview](docs/ARCHITECTURE.md) (coming soon)
- [Agent Development](docs/AGENT_DEVELOPMENT.md) (coming soon)

🚀 Start building:
- Implement your first agent
- Create MCP server tools
- Build the web UI

Need help? Check the docs or open an issue!
