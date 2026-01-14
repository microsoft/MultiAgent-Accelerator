# Quick Setup: GitHub Actions for AKS Deployment

## One-Time Setup (5 minutes)

### 1. Create Service Principal with Federated Credentials

```bash
# Set your values
SUBSCRIPTION_ID="38f95434-aef9-4dc4-97e9-cb69f25825f0"
RESOURCE_GROUP="multiagent-dev-rg"
GITHUB_ORG="darkanita"
GITHUB_REPO="MultiAgent-AKS-MAF"

# Create service principal
APP_ID=$(az ad sp create-for-rbac \
  --name "github-actions-mcp-deployer" \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
  --query appId -o tsv)

echo "✅ Service Principal Created"
echo "App ID: $APP_ID"

# Create federated credential for GitHub Actions
az ad app federated-credential create \
  --id $APP_ID \
  --parameters "{
    \"name\": \"github-actions-main\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"repo:$GITHUB_ORG/$GITHUB_REPO:ref:refs/heads/main\",
    \"audiences\": [\"api://AzureADTokenExchange\"]
  }"

echo "✅ Federated Credential Created"

# Get values for GitHub Secrets
echo ""
echo "📋 Add these to GitHub Secrets:"
echo "AZURE_CLIENT_ID: $APP_ID"
echo "AZURE_TENANT_ID: $(az account show --query tenantId -o tsv)"
echo "AZURE_SUBSCRIPTION_ID: $SUBSCRIPTION_ID"
```

### 2. Add GitHub Secrets

Go to: `https://github.com/darkanita/MultiAgent-AKS-MAF/settings/secrets/actions`

Add three secrets with the values from step 1.

### 3. Done! 🎉

The workflow is ready. It will auto-deploy on push to main.

---

## Manual Deployment

Go to Actions → "Deploy MCP Services to AKS" → "Run workflow"

---

## Test After Deployment

```bash
# Get external IP
kubectl get service travel-agent-service -n multiagent

# Test
curl -X POST http://EXTERNAL_IP/task \
  -H "Content-Type: application/json" \
  -d '{"task": "What is the exchange rate from USD to EUR?"}'
```

---

## Workflow Triggers

- ✅ Push to `main` branch (auto)
- ✅ Manual via GitHub UI
- ✅ Watches: `mcp_servers/**`, `agents/**`, `k8s/**`

---

## What It Does

1. 🔐 Authenticates to Azure (OIDC)
2. 🏗️ Builds 3 Docker images (currency-mcp, activity-mcp, travel-agent)
3. 📦 Pushes to Azure Container Registry
4. 🚀 Deploys to AKS with variable substitution
5. ⏳ Waits for pods to be ready
6. 🧪 Tests deployment
7. 📊 Provides summary

---

## Troubleshooting

**Login fails?**
```bash
# Verify federated credential
az ad app federated-credential list --id $APP_ID
```

**Permission denied?**
```bash
# Grant ACR push permission
ACR_ID=$(az acr show -g $RESOURCE_GROUP -n $(az acr list -g $RESOURCE_GROUP --query '[0].name' -o tsv) --query id -o tsv)
az role assignment create --assignee $APP_ID --role AcrPush --scope $ACR_ID
```

**Pods not starting?**
```bash
kubectl describe pod -n multiagent -l app=travel-agent
kubectl logs -n multiagent -l app=travel-agent
```
