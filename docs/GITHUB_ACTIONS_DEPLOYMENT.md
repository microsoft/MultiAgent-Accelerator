# GitHub Actions Setup for AKS Deployment

This guide walks you through setting up GitHub Actions to automatically deploy the MCP services to AKS.

## Prerequisites

- Azure subscription
- GitHub repository with the code
- AKS cluster and ACR already deployed
- Azure CLI installed locally

## Step 1: Create Azure Service Principal with Federated Credentials

Azure recommends using **Workload Identity Federation (OIDC)** instead of storing credentials. This is more secure and doesn't require secret rotation.

### 1.1 Create the Service Principal

```bash
# Set variables
SUBSCRIPTION_ID="38f95434-aef9-4dc4-97e9-cb69f25825f0"
RESOURCE_GROUP="multiagent-dev-rg"
GITHUB_ORG="darkanita"  # Your GitHub username or organization
GITHUB_REPO="MultiAgent-AKS-MAF"

# Create service principal
APP_NAME="github-actions-mcp-deployer"

az ad sp create-for-rbac \
  --name $APP_NAME \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth

# Save the output - you'll need the clientId and tenantId
```

**Save the output!** You'll see something like:
```json
{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "...",
  "subscriptionId": "38f95434-aef9-4dc4-97e9-cb69f25825f0",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "..."
}
```

### 1.2 Create Federated Credentials

```bash
# Get the Application (Client) ID
APP_ID=$(az ad sp list --display-name $APP_NAME --query '[0].appId' -o tsv)

echo "Application ID: $APP_ID"

# Create federated credential for main branch
az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "github-actions-main",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:'"$GITHUB_ORG/$GITHUB_REPO"':ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'

echo "✅ Federated credential created for main branch"
```

### 1.3 Grant Additional Permissions (if needed)

```bash
# Get the Service Principal Object ID
SP_OBJECT_ID=$(az ad sp list --display-name $APP_NAME --query '[0].id' -o tsv)

# Grant AcrPush role for ACR
ACR_ID=$(az acr show -g $RESOURCE_GROUP -n $(az acr list -g $RESOURCE_GROUP --query '[0].name' -o tsv) --query id -o tsv)

az role assignment create \
  --assignee $SP_OBJECT_ID \
  --role AcrPush \
  --scope $ACR_ID

echo "✅ AcrPush role assigned"
```

## Step 2: Configure GitHub Secrets

Go to your GitHub repository: `https://github.com/$GITHUB_ORG/$GITHUB_REPO/settings/secrets/actions`

### Add Repository Secrets

Click "New repository secret" and add these three secrets:

1. **AZURE_CLIENT_ID**
   - Value: The `clientId` from step 1.1 output

2. **AZURE_TENANT_ID**
   - Value: The `tenantId` from step 1.1 output

3. **AZURE_SUBSCRIPTION_ID**
   - Value: `38f95434-aef9-4dc4-97e9-cb69f25825f0`

### Verify Secrets

You should see all three secrets listed:
- ✅ AZURE_CLIENT_ID
- ✅ AZURE_TENANT_ID
- ✅ AZURE_SUBSCRIPTION_ID

## Step 3: Test the Workflow

### Option 1: Push to Main Branch

Any push to the `main` branch that changes these paths will trigger deployment:
- `mcp_servers/**`
- `agents/travel_agent/**`
- `k8s/**`
- `.github/workflows/deploy-mcp-to-aks.yml`

```bash
git add .
git commit -m "feat: update MCP services"
git push origin main
```

### Option 2: Manual Trigger

1. Go to: `https://github.com/$GITHUB_ORG/$GITHUB_REPO/actions`
2. Click "Deploy MCP Services to AKS" workflow
3. Click "Run workflow"
4. Select environment (dev/staging/prod)
5. Click "Run workflow"

## Step 4: Monitor Deployment

### Via GitHub Actions UI

1. Go to the Actions tab
2. Click on the running workflow
3. Watch the logs in real-time

### Via Azure Portal

1. Go to your AKS cluster in Azure Portal
2. Navigate to "Workloads" → "Deployments"
3. Check the status of:
   - currency-mcp
   - activity-mcp
   - travel-agent

### Via kubectl (Local)

```bash
# Get AKS credentials
az aks get-credentials \
  --resource-group multiagent-dev-rg \
  --name multiagent-dev-aks

# Watch deployments
kubectl get deployments -n multiagent -w

# Check pods
kubectl get pods -n multiagent

# Get external IP
kubectl get service travel-agent-service -n multiagent
```

## Step 5: Verify Deployment

Once the workflow completes, test the deployed service:

```bash
# Get the external IP
EXTERNAL_IP=$(kubectl get service travel-agent-service -n multiagent -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test health
curl http://$EXTERNAL_IP/health

# Test functionality
curl -X POST http://$EXTERNAL_IP/task \
  -H "Content-Type: application/json" \
  -d '{"task": "What is the exchange rate from USD to EUR?"}'
```

## Workflow Features

### 🚀 Automated Build & Push
- Builds Docker images for all 3 services
- Tags with both git SHA and `latest`
- Pushes to Azure Container Registry

### 🔐 Secure Authentication
- Uses OIDC (no stored secrets)
- Workload Identity for AKS pods
- Automatic credential refresh

### 📊 Deployment Verification
- Waits for pods to be ready
- Tests health endpoint
- Tests functionality
- Provides deployment summary

### 🎯 Smart Triggers
- Only deploys when relevant files change
- Manual trigger option for on-demand deployments
- Environment selection (dev/staging/prod)

## Troubleshooting

### Error: "Login failed"

Check that your federated credentials are correct:
```bash
az ad app federated-credential list --id $APP_ID
```

Verify the subject matches: `repo:OWNER/REPO:ref:refs/heads/main`

### Error: "Permission denied"

Ensure the service principal has contributor role:
```bash
az role assignment list --assignee $APP_ID --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP
```

### Error: "Image pull failed"

Ensure AKS has access to ACR:
```bash
AKS_NAME=$(az aks list -g $RESOURCE_GROUP --query '[0].name' -o tsv)
ACR_NAME=$(az acr list -g $RESOURCE_GROUP --query '[0].name' -o tsv)

az aks update -n $AKS_NAME -g $RESOURCE_GROUP --attach-acr $ACR_NAME
```

### Pods stuck in "Pending"

Check events:
```bash
kubectl describe pod -n multiagent -l app=travel-agent
```

### External IP not assigned

Check service status:
```bash
kubectl get service travel-agent-service -n multiagent
kubectl describe service travel-agent-service -n multiagent
```

## Security Best Practices

✅ **Use OIDC** instead of long-lived credentials
✅ **Least privilege** - service principal only has access to the resource group
✅ **Federated credentials** - scoped to specific repo and branch
✅ **No secrets in code** - all sensitive data in GitHub Secrets
✅ **Workload Identity** - AKS pods use managed identity for Azure OpenAI

## Next Steps

1. Set up staging environment with separate federated credential
2. Add approval gates for production deployments
3. Implement blue-green deployment strategy
4. Add automated testing after deployment
5. Set up monitoring and alerts

## Cleanup

If you need to remove the setup:

```bash
# Delete federated credential
az ad app federated-credential delete --id $APP_ID --federated-credential-id github-actions-main

# Delete service principal
az ad sp delete --id $APP_ID

# Remove GitHub secrets (via UI)
# Go to Settings → Secrets and variables → Actions → Delete each secret
```
