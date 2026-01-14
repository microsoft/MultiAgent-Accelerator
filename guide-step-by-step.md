# 🚀 Infrastructure Deployment Guide

Deploy the Multi-Agent System infrastructure to Azure using `deploy-infrastructure.sh`.

---

## 📋 Prerequisites

| Tool | Installation |
|------|--------------|
| Azure CLI | [Install Guide](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) |
| Git Bash / WSL | For running shell scripts on Windows |

---

## Step 1: Login to Azure

```bash
az login --use-device-code
```

Verify your login:
```bash
az account show --query "{Name:name, SubscriptionId:id}" -o table
```

---

## Step 2: Navigate to Project Directory

```bash
cd /c/Users/alopezmoreno/Downloads/Kubecon/MultiAgent-Demo
```

---

## Step 3: Run the Deployment Script

### Basic Usage
```bash
multiagent-demo-rg
```

**Example:**
```bash
./scripts/deploy-infrastructure.sh -g multiagent-demo-rg -p multiagentaml01 -c
```

### Script Options

| Flag | Description | Default |
|------|-------------|---------|
| `-g, --resource-group` | Resource group name | **Required** |
| `-e, --environment` | dev, staging, or prod | `dev` |
| `-p, --project-name` | Prefix for resource names | `multiagent` |
| `-l, --location` | Azure region | `centralus` |
| `-c, --create-rg` | Create resource group if it doesn't exist | - |
| `-v, --validate-only` | Validate template without deploying | - |

### More Examples

```bash
# Custom environment and location
./scripts/deploy-infrastructure.sh -g multiagent-prod-rg -p myproject -e prod -l eastus -c

# Validate only (no deployment)
./scripts/deploy-infrastructure.sh -g multiagent-demo-rg -p multiagentaml01 -v
```

---

## Step 4: Wait for Deployment

Deployment takes **10-20 minutes**. The script will display:

1. ✅ Configuration summary
2. ✅ Azure CLI authentication check
3. ✅ Resource group creation (if `-c` flag used)
4. ✅ Template validation
5. ✅ Deployment progress
6. ✅ Key resources created (outputs)

### Resources Created

| Resource | Purpose |
|----------|---------|
| AKS Cluster | Kubernetes for running agents |
| Container Registry (ACR) | Store container images |
| Azure OpenAI | LLM backend |
| Service Bus | Agent-to-Agent messaging |
| Key Vault | Secrets management |
| Application Insights | Monitoring |
| Workload Identity | Secure authentication |

---

## Step 5: Verify Deployment

After successful deployment, the script outputs key resource information:

```
📋 Key Resources Created:
========================
  AKS Cluster:              multiagent-dev-aks
  Container Registry:       multiagentdevacr.azurecr.io
  OpenAI Endpoint:          https://...openai.azure.com/
  Service Bus Namespace:    multiagent-dev-sb
  Key Vault:                multiagent-dev-kv
  Workload Identity ID:     xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

## Step 6: Deploy Agents to Container Apps

### Build and push images
```bash
./scripts/deploy-to-container-apps.sh -g multiagent-demo-rg -p multiagentaml01 -b
```

### Deploy to Container Apps
```bash
./scripts/deploy-to-container-apps.sh -g multiagent-demo-rg -p multiagentaml01 -d
```

### Or do both in one command
```bash
./scripts/deploy-to-container-apps.sh -g multiagent-demo-rg -p multiagentaml01
```

### Container Apps Architecture
```
User → Web UI (public) → Orchestrator (internal) → Travel Agent → MCP Servers
```

| Container App | Ingress | Port |
|---------------|---------|------|
| currency-mcp | internal | 8001 |
| activity-mcp | internal | 8002 |
| travel-agent | internal | 8080 |
| orchestrator | internal | 8000 |
| web-ui | **external** | 8501 |

---

## Step 7: Test the Deployment

### Open Web UI in Browser
```bash
# Get the Web UI URL
WEB_URL=$(az containerapp show -g <resource-group> -n <project-name>-web-ui --query "properties.configuration.ingress.fqdn" -o tsv)
echo "🌐 Open in browser: https://$WEB_URL"
```

### Check Container Apps Status
```bash
# List all apps and their status
az containerapp list -g <resource-group> -o table
```

### View Logs
```bash
# Stream logs from orchestrator
az containerapp logs show -g <resource-group> -n <project-name>-orchestrator --follow

# Stream logs from web-ui
az containerapp logs show -g <resource-group> -n <project-name>-web-ui --follow
```

### Check Replicas
```bash
az containerapp replica list -g <resource-group> -n <project-name>-orchestrator -o table
```

---

## 🔧 Troubleshooting

| Error | Solution |
|-------|----------|
| "Not logged in to Azure CLI" | Run `az login --use-device-code` |
| "Resource provider not registered" | Run `az provider register --namespace <Provider>` |
| "Quota exceeded" | Check Azure Portal → Subscriptions → Usage + quotas |
| Template validation failed | Check Bicep errors in output, verify region availability |

### View deployment errors:
```bash
az deployment group show -g <resource-group> -n <deployment-name> --query 'properties.error'
```

---

## 🧹 Cleanup

Delete all resources when done:

```bash
az group delete --name <resource-group-name> --yes --no-wait
```
