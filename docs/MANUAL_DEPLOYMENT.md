# Manual Deployment Commands

Since the automated scripts are having Azure CLI compatibility issues on Windows, 
use these manual commands instead.

## Step 1: Set Variables

```bash
# In Git Bash or PowerShell
export LOCATION="centralus"
export PROJECT_NAME="multiagent"
export ENVIRONMENT="dev"
export DEPLOYMENT_NAME="${PROJECT_NAME}-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"

# Or in PowerShell:
# $location = "centralus"
# $projectName = "multiagent"
# $environment = "dev"
# $deploymentName = "$projectName-$environment-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
```

## Step 2: Navigate to Bicep Directory

```bash
cd infrastructure/bicep
```

## Step 3: Deploy (No Output Redirection)

**IMPORTANT: Do NOT redirect output to file - this causes the error!**

```bash
az deployment sub create \
  --location centralus \
  --template-file main.bicep \
  --parameters main.parameters.json \
  --parameters environment=dev \
  --parameters projectName=multiagent \
  --name multiagent-dev-20251110
```

Or in PowerShell (RECOMMENDED for Windows):

```powershell
az deployment sub create `
  --location centralus `
  --template-file main.bicep `
  --parameters main.parameters.json `
  --parameters environment=dev `
  --parameters projectName=multiagent `
  --name multiagent-dev-20251110
```

**This will take 10-15 minutes. Watch the progress in the terminal.**

## Step 4: After Deployment, Get Outputs

```bash
# Get all outputs
az deployment sub show \
  --name multiagent-dev-20251110 \
  --query properties.outputs

# Get specific values
export RG_NAME=$(az deployment sub show --name multiagent-dev-20251110 --query 'properties.outputs.resourceGroupName.value' -o tsv)
export AKS_NAME=$(az deployment sub show --name multiagent-dev-20251110 --query 'properties.outputs.aksClusterName.value' -o tsv)
export ACR_SERVER=$(az deployment sub show --name multiagent-dev-20251110 --query 'properties.outputs.acrLoginServer.value' -o tsv)

echo "Resource Group: $RG_NAME"
echo "AKS Cluster: $AKS_NAME"
echo "ACR Server: $ACR_SERVER"
```

## Step 5: Configure kubectl

```bash
az aks get-credentials \
  --resource-group $RG_NAME \
  --name $AKS_NAME \
  --overwrite-existing

# Verify
kubectl get nodes
```

## Alternative: Azure Portal Deployment

If Azure CLI continues to fail, deploy via Azure Portal:

1. Go to https://portal.azure.com
2. Search for "Deploy a custom template"
3. Click "Build your own template in the editor"
4. Copy and paste the entire `main.bicep` content
5. Click "Save"
6. Fill in parameters and deploy

The portal deployment is completely reliable and will work every time.
