# Infrastructure Deployment Guide

This guide explains how to deploy the Multi-Agent System infrastructure to Azure using Bicep.

## Prerequisites

1. **Azure CLI** - [Install Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
2. **Azure Subscription** - Active Azure subscription with appropriate permissions
3. **Bicep CLI** - Comes with Azure CLI (or install separately)
4. **GitHub Account** - For CI/CD pipelines

## Azure Setup

### 1. Login to Azure

```bash
az login
az account set --subscription "<your-subscription-id>"
```

### 2. Register Required Resource Providers

```bash
az provider register --namespace Microsoft.ContainerService
az provider register --namespace Microsoft.ContainerRegistry
az provider register --namespace Microsoft.CognitiveServices
az provider register --namespace Microsoft.ServiceBus
az provider register --namespace Microsoft.KeyVault
az provider register --namespace Microsoft.OperationalInsights
az provider register --namespace Microsoft.Insights
az provider register --namespace Microsoft.MachineLearningServices
```

## Manual Deployment

### Deploy Infrastructure

```bash
# Navigate to the infrastructure directory
cd infrastructure/bicep

# Deploy to development environment
az deployment sub create \
  --location eastus \
  --template-file main.bicep \
  --parameters main.parameters.json \
  --parameters environment=dev \
  --name multiagent-dev-deployment

# View deployment outputs
az deployment sub show \
  --name multiagent-dev-deployment \
  --query properties.outputs
```

### Get Deployment Outputs

```bash
# Get Resource Group name
RG_NAME=$(az deployment sub show --name multiagent-dev-deployment --query 'properties.outputs.resourceGroupName.value' -o tsv)

# Get AKS cluster name
AKS_NAME=$(az deployment sub show --name multiagent-dev-deployment --query 'properties.outputs.aksClusterName.value' -o tsv)

# Get ACR login server
ACR_SERVER=$(az deployment sub show --name multiagent-dev-deployment --query 'properties.outputs.acrLoginServer.value' -o tsv)

# Get OpenAI endpoint
OPENAI_ENDPOINT=$(az deployment sub show --name multiagent-dev-deployment --query 'properties.outputs.openAIEndpoint.value' -o tsv)

echo "Resource Group: $RG_NAME"
echo "AKS Cluster: $AKS_NAME"
echo "ACR Server: $ACR_SERVER"
echo "OpenAI Endpoint: $OPENAI_ENDPOINT"
```

### Configure AKS Access

```bash
# Get AKS credentials
az aks get-credentials \
  --resource-group $RG_NAME \
  --name $AKS_NAME \
  --overwrite-existing

# Verify connection
kubectl get nodes
kubectl cluster-info
```

## GitHub Actions Setup (CI/CD)

### 1. Create Azure Service Principal

Create a service principal for GitHub Actions to authenticate with Azure:

```bash
# Set variables
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SP_NAME="multiagent-github-actions"

# Create service principal
az ad sp create-for-rbac \
  --name $SP_NAME \
  --role Contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID \
  --sdk-auth

# This will output JSON - save it for GitHub Secrets
```

**Alternative: Using Workload Identity (Recommended)**

```bash
# Create Azure AD Application
APP_ID=$(az ad app create --display-name "multiagent-github-actions" --query appId -o tsv)

# Create Service Principal
az ad sp create --id $APP_ID

# Assign Contributor role
az role assignment create \
  --assignee $APP_ID \
  --role Contributor \
  --scope /subscriptions/$SUBSCRIPTION_ID

# Configure federated credentials for GitHub Actions
az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "multiagent-github-main",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:<your-github-org>/<your-repo>:ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

### 2. Configure GitHub Secrets

Add the following secrets to your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

- `AZURE_CLIENT_ID` - Application (client) ID from service principal
- `AZURE_TENANT_ID` - Directory (tenant) ID from service principal
- `AZURE_SUBSCRIPTION_ID` - Your Azure subscription ID

### 3. Enable GitHub Actions

The workflows are already configured in `.github/workflows/`:

- **deploy-infrastructure.yml** - Deploys Bicep infrastructure
- **build-and-deploy.yml** - Builds and deploys applications
- **pr-validation.yml** - Validates PRs

Push to `main` branch to trigger automatic deployment.

## Infrastructure Components

### Created Resources

| Resource | Purpose |
|----------|---------|
| **AKS Cluster** | Kubernetes orchestration for agents |
| **Azure Container Registry** | Store container images |
| **Azure AI Hub & Project** | AI Foundry workspace |
| **Azure OpenAI** | GPT-4, GPT-3.5 model deployments |
| **Service Bus** | Agent-to-agent messaging |
| **Key Vault** | Secrets management |
| **Application Insights** | Monitoring and logging |
| **Log Analytics** | Centralized logging |

### Resource Naming Convention

Format: `{projectName}-{environment}-{resourceType}`

Examples:
- `multiagent-dev-aks` - AKS cluster
- `multiagent-dev-rg` - Resource group
- `multiagentdevacr` - Container registry (no hyphens)

## Retrieve Secrets

### Get Azure OpenAI Keys

```bash
OPENAI_NAME=$(az deployment sub show --name multiagent-dev-deployment --query 'properties.outputs.openAIName.value' -o tsv)

az cognitiveservices account keys list \
  --name $OPENAI_NAME \
  --resource-group $RG_NAME
```

### Get Service Bus Connection String

```bash
SB_NAMESPACE=$(az deployment sub show --name multiagent-dev-deployment --query 'properties.outputs.serviceBusNamespace.value' -o tsv)

az servicebus namespace authorization-rule keys list \
  --resource-group $RG_NAME \
  --namespace-name $SB_NAMESPACE \
  --name RootManageSharedAccessKey \
  --query primaryConnectionString -o tsv
```

### Store Secrets in Key Vault

```bash
KV_NAME=$(az deployment sub show --name multiagent-dev-deployment --query 'properties.outputs.keyVaultName.value' -o tsv)

# Store OpenAI key
OPENAI_KEY=$(az cognitiveservices account keys list --name $OPENAI_NAME --resource-group $RG_NAME --query key1 -o tsv)
az keyvault secret set --vault-name $KV_NAME --name "openai-api-key" --value "$OPENAI_KEY"

# Store Service Bus connection string
SB_CONN=$(az servicebus namespace authorization-rule keys list --resource-group $RG_NAME --namespace-name $SB_NAMESPACE --name RootManageSharedAccessKey --query primaryConnectionString -o tsv)
az keyvault secret set --vault-name $KV_NAME --name "servicebus-connection-string" --value "$SB_CONN"

# Store Application Insights connection string
AI_CONN=$(az deployment sub show --name multiagent-dev-deployment --query 'properties.outputs.appInsightsConnectionString.value' -o tsv)
az keyvault secret set --vault-name $KV_NAME --name "appinsights-connection-string" --value "$AI_CONN"
```

## Update and Redeploy

To update infrastructure:

```bash
# Make changes to Bicep files

# Validate changes
az deployment sub validate \
  --location eastus \
  --template-file main.bicep \
  --parameters main.parameters.json

# Deploy changes
az deployment sub create \
  --location eastus \
  --template-file main.bicep \
  --parameters main.parameters.json \
  --name multiagent-dev-update-$(date +%Y%m%d-%H%M%S)
```

## Clean Up

To delete all resources:

```bash
# Delete resource group (this deletes all resources)
az group delete --name multiagent-dev-rg --yes --no-wait

# Or use deployment cleanup
az deployment sub delete --name multiagent-dev-deployment
```

## Troubleshooting

### Deployment Failures

```bash
# View deployment operations
az deployment sub operation list \
  --name multiagent-dev-deployment \
  --query "[?properties.provisioningState=='Failed']"

# View detailed error
az deployment sub show \
  --name multiagent-dev-deployment \
  --query properties.error
```

### AKS Connection Issues

```bash
# Reset AKS credentials
az aks get-credentials \
  --resource-group $RG_NAME \
  --name $AKS_NAME \
  --overwrite-existing \
  --admin

# Check AKS status
az aks show \
  --resource-group $RG_NAME \
  --name $AKS_NAME \
  --query powerState
```

### ACR Access Issues

```bash
# Verify ACR role assignment
az role assignment list \
  --assignee $(az aks show -g $RG_NAME -n $AKS_NAME --query identityProfile.kubeletidentity.objectId -o tsv) \
  --scope $(az acr show -n $ACR_NAME --query id -o tsv)
```

## Next Steps

After infrastructure deployment:

1. **Configure Secrets** - Store API keys in Key Vault
2. **Build Containers** - Build and push agent containers
3. **Deploy Applications** - Deploy agents to AKS
4. **Configure Networking** - Set up ingress for Web UI
5. **Setup Monitoring** - Configure alerts and dashboards

See [APPLICATION_DEPLOYMENT.md](APPLICATION_DEPLOYMENT.md) for application deployment steps.
