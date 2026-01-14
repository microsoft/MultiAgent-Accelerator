# Azure Portal Deployment Guide

## ✅ Working Deployment Method

Due to Azure CLI issues on Windows with subscription-level deployments, **Azure Portal template upload** is the recommended deployment method.

## Prerequisites

1. Azure subscription: `38f95434-aef9-4dc4-97e9-cb69f25825f0`
2. Resource group created: `multiagent-dev-rg` (Central US)

## Deployment Steps

### 1. Regenerate ARM Template (if modified)

If you make changes to any Bicep files, regenerate the ARM JSON:

```bash
cd infrastructure/bicep
az bicep build --file main-rg.bicep --outfile main-rg.json
```

### 2. Deploy via Azure Portal

1. Navigate to: https://portal.azure.com/#create/Microsoft.Template
2. Click **"Build your own template in the editor"**
3. Click **"Load file"**
4. Select: `infrastructure/bicep/main-rg.json`
5. Click **"Save"**
6. Select resource group: `multiagent-dev-rg`
7. Set parameters:
   - **environment**: `dev`
   - **projectName**: `multiagent`
   - **location**: Auto-filled from resource group (Central US)
8. Click **"Review + create"**
9. Click **"Create"**

## Deployed Resources

### Central US Region
- **AKS Cluster**: `multiagent-dev-aks` (K8s 1.31.2, 3 nodes, D4s_v3)
- **Container Registry**: `acrmadev[unique]` (Basic SKU)
- **Service Bus**: `multiagent-dev-servicebus` (Standard, 2 queues, 1 topic)
- **Key Vault**: `multiagent-dev-kv`
- **App Insights**: `multiagent-dev-appinsights`
- **Log Analytics**: `multiagent-dev-logs`, `multiagent-dev-logs-ai`

### East US Region
- **AI Hub**: `multiagent-dev-aihub`
- **AI Project**: `multiagent-dev-aiproject`
- **OpenAI Service**: `multiagent-dev-openai`
  - GPT-4o (2024-08-06)
  - GPT-4o-mini (2024-07-18)
  - GPT-3.5-turbo (0125)
- **Storage Account**: `multiagentdevaistorage`

## Key Configuration Details

### ACR Configuration (Working)
- **API Version**: `2019-05-01` (stable, not preview)
- **SKU**: Basic (only supported SKU in this subscription)
- **Admin User**: Disabled
- **Naming**: `acrmadev[8-char-unique-suffix]`
- **Location**: Central US

### Regional Split
- **Compute/Infrastructure**: Central US (AKS, ACR, Service Bus, etc.)
- **AI Services**: East US (required for GPT-4o-mini model availability)

## Troubleshooting

### If ACR deployment fails
- Verify name uniqueness: `az acr check-name --name <name>`
- Check you don't exceed ACR quota (current: 2 ACRs)
- Basic SKU is the only supported tier in this subscription

### If OpenAI deployment fails
- GPT-4o-mini requires East US region
- Check model version availability
- Verify quota in East US region

## Next Steps After Deployment

1. **Connect to AKS**:
   ```bash
   az aks get-credentials --resource-group multiagent-dev-rg --name multiagent-dev-aks
   ```

2. **Get ACR login server**:
   ```bash
   az acr list --resource-group multiagent-dev-rg --query "[].loginServer" -o tsv
   ```

3. **Get OpenAI endpoint**:
   ```bash
   az cognitiveservices account show --name multiagent-dev-openai --resource-group multiagent-dev-rg --query properties.endpoint -o tsv
   ```

4. **Store secrets in Key Vault** (use the `scripts/store-secrets.sh` script)
