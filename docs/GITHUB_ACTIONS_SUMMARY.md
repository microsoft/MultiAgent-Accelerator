# GitHub Actions CI/CD for MCP Services - Summary

## 📦 What Was Created

### 1. GitHub Actions Workflow
**File**: `.github/workflows/deploy-mcp-to-aks.yml`

A complete CI/CD pipeline that:
- ✅ Authenticates to Azure using OIDC (secure, no stored credentials)
- ✅ Auto-discovers Azure resources (ACR, AKS, OpenAI)
- ✅ Builds 3 Docker images (currency-mcp, activity-mcp, travel-agent)
- ✅ Pushes images to Azure Container Registry with git SHA tags
- ✅ Deploys to AKS with proper variable substitution
- ✅ Waits for pods to be ready
- ✅ Tests deployment automatically
- ✅ Provides detailed deployment summary

### 2. Documentation

**Complete Setup Guide**: `docs/GITHUB_ACTIONS_DEPLOYMENT.md`
- Step-by-step service principal setup
- Federated credential configuration
- GitHub secrets setup
- Troubleshooting guide
- Security best practices

**Quick Reference**: `.github/DEPLOYMENT_QUICKSTART.md`
- Copy-paste commands for 5-minute setup
- Essential troubleshooting
- Quick testing guide

### 3. Updated README
- Added workflow status badge
- Documented GitHub Actions deployment option
- Updated deployment section

## 🚀 How It Works

### Trigger Conditions

The workflow runs when:

1. **Automatic (Push to Main)**:
   - Changes to `mcp_servers/**`
   - Changes to `agents/travel_agent/**`
   - Changes to `k8s/**`
   - Changes to workflow file itself

2. **Manual (Workflow Dispatch)**:
   - Via GitHub Actions UI
   - Select environment (dev/staging/prod)

### Deployment Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Code Push to Main Branch                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. GitHub Actions Triggered                                │
│    - Checkout code                                          │
│    - Login to Azure (OIDC)                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Build Phase                                              │
│    - Build currency-mcp:SHA & :latest                       │
│    - Build activity-mcp:SHA & :latest                       │
│    - Build travel-agent:SHA & :latest                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Push Phase                                               │
│    - Push all images to ACR                                 │
│    - Tagged with git SHA for rollback capability            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Deploy Phase                                             │
│    - Get AKS credentials                                    │
│    - Get Workload Identity config                           │
│    - Apply namespace & service account                      │
│    - Deploy currency-mcp (with session affinity)            │
│    - Deploy activity-mcp (with session affinity)            │
│    - Deploy travel-agent (with Workload Identity)           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Verification Phase                                       │
│    - Wait for pods to be ready (5 min timeout)              │
│    - Confirm internal services and pod status               │
│    - Require authenticated ingress or port-forward access   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Success Summary                                          │
│    - Deployed image tags                                    │
│    - External IP address                                    │
│    - Resource information                                   │
└─────────────────────────────────────────────────────────────┘
```

## 🔐 Security Features

### Workload Identity Federation (OIDC)

**No stored secrets!** Uses federated credentials instead:

```yaml
permissions:
  id-token: write  # Request OIDC token
  contents: read   # Read repository

# Login without client secret
- uses: azure/login@v2
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

### Least Privilege

Service Principal has:
- ✅ Contributor role ONLY on the resource group (not subscription)
- ✅ AcrPush role for pushing images
- ✅ Federated credential scoped to specific repo and branch

### AKS Security

Pods use:
- ✅ Azure Workload Identity (no secrets in pods)
- ✅ Managed Identity for Azure OpenAI access
- ✅ Session affinity for stateful MCP connections

## 📊 What Gets Deployed

### Images
```
acrmadev2jhf6weu.azurecr.io/
├── currency-mcp:latest
├── currency-mcp:<git-sha>
├── activity-mcp:latest
├── activity-mcp:<git-sha>
├── travel-agent:latest
└── travel-agent:<git-sha>
```

### Kubernetes Resources
```
namespace/multiagent
├── ServiceAccount: multiagent-sa (with Workload Identity)
├── Deployments:
│   ├── currency-mcp (2 replicas)
│   ├── activity-mcp (2 replicas)
│   └── travel-agent (2 replicas)
└── Services:
    ├── currency-mcp-service (ClusterIP + Session Affinity)
    ├── activity-mcp-service (ClusterIP + Session Affinity)
    └── travel-agent-service (ClusterIP)
```

## 🧪 Testing After Deployment

The workflow automatically tests the deployment:

```bash
# Health check
kubectl port-forward -n multiagent service/travel-agent-service 8080:80
API_KEY=$(kubectl get secret multiagent-api-auth -n multiagent -o jsonpath='{.data.api-key}' | base64 -d)
curl http://localhost:8080/health

# Functionality test
curl -X POST http://localhost:8080/task \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -H "X-User-ID: test-user" \
  -d '{"task": "What is the exchange rate from USD to EUR?"}'
```

Expected response:
```json
{
  "result": "The current exchange rate from USD to EUR is 1 USD = 0.8642 EUR.",
  "agent": "travel_agent"
}
```

## 📈 Monitoring Deployment

### Via GitHub Actions UI

1. Go to: `https://github.com/darkanita/MultiAgent-AKS-MAF/actions`
2. Click on latest workflow run
3. View real-time logs for each step

### Via kubectl

```bash
# Watch deployment progress
kubectl get deployments -n multiagent -w

# Check pod status
kubectl get pods -n multiagent

# View logs
kubectl logs -n multiagent -l app=travel-agent --tail=50
```

### Via Azure Portal

1. Go to AKS cluster
2. Workloads → Deployments
3. View deployment status

## 🔄 Rollback Strategy

Since images are tagged with git SHA:

```bash
# List available versions
az acr repository show-tags \
  -n acrmadev2jhf6weu \
  --repository travel-agent \
  --orderby time_desc

# Rollback to specific version
kubectl set image deployment/travel-agent \
  travel-agent=acrmadev2jhf6weu.azurecr.io/travel-agent:<previous-sha> \
  -n multiagent
```

## 🚦 Current Status

✅ **Infrastructure**: Deployed and ready
✅ **Workflow**: Created and configured
✅ **Documentation**: Complete setup guides
✅ **Session Affinity**: Configured for MCP servers
✅ **Workload Identity**: Set up for Azure OpenAI access
✅ **Testing**: Automated tests in pipeline

⏳ **Pending**:
- [ ] Create Azure Service Principal with federated credentials
- [ ] Add GitHub Secrets (AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID)
- [ ] Push changes to trigger first deployment

## 📝 Next Steps

### 1. Set Up GitHub Actions (5 minutes)

```bash
# Run the setup script from DEPLOYMENT_QUICKSTART.md
# This creates the service principal and federated credentials
```

### 2. Add GitHub Secrets

Go to repository settings and add the three required secrets.

### 3. Test Deployment

```bash
# Make a small change to trigger workflow
echo "# Test deployment" >> README.md
git add README.md
git commit -m "test: trigger GitHub Actions deployment"
git push origin main

# Watch the workflow run
# Go to: https://github.com/darkanita/MultiAgent-AKS-MAF/actions
```

### 4. Verify

Once complete, test the deployed service:
```bash
kubectl port-forward -n multiagent service/travel-agent-service 8080:80
API_KEY=$(kubectl get secret multiagent-api-auth -n multiagent -o jsonpath='{.data.api-key}' | base64 -d)
curl -X POST http://localhost:8080/task \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -H "X-User-ID: test-user" \
  -d '{"task": "Convert 100 USD to EUR"}'
```

## 🎯 Benefits

✅ **Automated**: Push to deploy, no manual steps
✅ **Secure**: OIDC authentication, no stored secrets
✅ **Fast**: Complete deployment in ~5 minutes
✅ **Tested**: Automatic verification after deployment
✅ **Traceable**: Git SHA tags for version tracking
✅ **Reliable**: Waits for pods, handles failures gracefully
✅ **Documented**: Complete logs and summaries

## 📚 Additional Resources

- [GitHub Actions Deployment Guide](docs/GITHUB_ACTIONS_DEPLOYMENT.md) - Complete setup
- [Deployment Quickstart](.github/DEPLOYMENT_QUICKSTART.md) - Quick commands
- [AKS Deployment Guide](docs/AKS_DEPLOYMENT.md) - Manual deployment
- [Workflow File](.github/workflows/deploy-mcp-to-aks.yml) - Full workflow code
