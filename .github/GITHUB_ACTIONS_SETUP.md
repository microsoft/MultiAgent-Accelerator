# GitHub Actions Setup Guide

This guide explains how to configure GitHub Actions for automated deployment of the Multi-Agent AKS infrastructure.

## Prerequisites

- GitHub repository with admin access
- Azure subscription (38f95434-aef9-4dc4-97e9-cb69f25825f0)
- Azure CLI installed locally

## Step 1: Create Azure Service Principal

Create a service principal with the required roles for GitHub Actions to deploy infrastructure:

```bash
# Set your subscription
az account set --subscription 38f95434-aef9-4dc4-97e9-cb69f25825f0

# Create service principal for GitHub Actions with Contributor role
az ad sp create-for-rbac \
  --name "github-actions-multiagent" \
  --role Contributor \
  --scopes /subscriptions/38f95434-aef9-4dc4-97e9-cb69f25825f0 \
  --sdk-auth
```

**IMPORTANT**: Save the output - you'll need it for GitHub secrets!

### Step 1.1: Add User Access Administrator Role

The service principal also needs **User Access Administrator** role to create role assignments (for AKS to access ACR and Key Vault):

```powershell
# Get the client ID from the previous command output
$CLIENT_ID = "YOUR_CLIENT_ID_FROM_ABOVE"

# Add User Access Administrator role
az role assignment create `
  --assignee $CLIENT_ID `
  --role "User Access Administrator" `
  --scope "/subscriptions/38f95434-aef9-4dc4-97e9-cb69f25825f0"
```

**Why both roles are needed:**
- **Contributor**: Creates Azure resources (AKS, ACR, Key Vault, etc.)
- **User Access Administrator**: Assigns roles between resources (AKS → ACR pull access, AKS → Key Vault access)

This will output JSON like:
```json
{
  "clientId": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
  "clientSecret": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "subscriptionId": "38f95434-aef9-4dc4-97e9-cb69f25825f0",
  "tenantId": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

**IMPORTANT**: Save this output - you'll need it for GitHub secrets!

## Step 2: Configure Federated Identity (Recommended for Production)

For better security, configure workload identity federation instead of using client secrets:

```bash
# Get your GitHub repo details
REPO_OWNER="your-github-username"
REPO_NAME="MultiAgent-AKS-MAF"

# Get the service principal object ID
APP_ID=$(az ad sp list --display-name "github-actions-multiagent" --query "[0].appId" -o tsv)
OBJECT_ID=$(az ad app show --id $APP_ID --query id -o tsv)

# Create federated credential for main branch
az ad app federated-credential create \
  --id $OBJECT_ID \
  --parameters '{
    "name": "github-main",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:'$REPO_OWNER'/'$REPO_NAME':ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'

# Create federated credential for pull requests
az ad app federated-credential create \
  --id $OBJECT_ID \
  --parameters '{
    "name": "github-pr",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:'$REPO_OWNER'/'$REPO_NAME':pull_request",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

## Step 3: Add GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

| Secret Name | Value | Where to Find |
|------------|-------|---------------|
| `AZURE_CLIENT_ID` | The `clientId` from service principal output | From Step 1 JSON output |
| `AZURE_TENANT_ID` | The `tenantId` from service principal output | From Step 1 JSON output |
| `AZURE_SUBSCRIPTION_ID` | `38f95434-aef9-4dc4-97e9-cb69f25825f0` | Your Azure subscription ID |
| `AZURE_CLIENT_SECRET` | The `clientSecret` from service principal output (only if NOT using federated identity) | From Step 1 JSON output |

## Step 4: Configure GitHub Environments

### Create Environments

1. Go to repository Settings → Environments
2. Click "New environment"
3. Create three environments:
   - `development`
   - `staging`
   - `production`

### Configure Protection Rules (Recommended)

For **production** environment:
- ✅ Required reviewers: Add team members who must approve production deployments
- ✅ Wait timer: 5 minutes (gives time to cancel if needed)
- ✅ Deployment branches: Only `main` branch

For **staging** environment:
- ✅ Deployment branches: Only `main` and `release/*` branches

For **development** environment:
- No restrictions needed (automatic deployment)

## Step 5: Verify Workflow Configuration

The workflow is configured to use **resource group-scoped deployments** which work reliably:

- ✅ Uses `main-rg.bicep` (not subscription-scoped template)
- ✅ Deploys to Central US (matching your infrastructure location)
- ✅ Creates resource groups before deployment
- ✅ Uses workload identity federation for secure authentication

## How to Use

### Automatic Deployment (Development)

Push changes to `main` branch that modify Bicep files:
```bash
git add infrastructure/bicep/
git commit -m "Update infrastructure configuration"
git push origin main
```

The workflow will automatically:
1. Validate Bicep templates
2. Deploy to development environment
3. Connect to AKS cluster
4. Verify deployment

### Manual Deployment (Staging/Production)

1. Go to Actions tab in GitHub
2. Select "Deploy Infrastructure" workflow
3. Click "Run workflow"
4. Choose environment (staging or prod)
5. Click "Run workflow"

### Pull Request Validation

When you create a pull request with Bicep changes:
1. Templates are automatically validated
2. No deployment happens
3. Validation results appear in PR checks

## Deployed Resources

The workflow will deploy to these resource groups:

| Environment | Resource Group | Location | Notes |
|------------|---------------|----------|-------|
| Development | `multiagent-dev-rg` | Central US | Auto-deploys on push to main |
| Staging | `multiagent-staging-rg` | Central US | Manual deployment only |
| Production | `multiagent-prod-rg` | Central US | Manual deployment with approvals |

## Infrastructure Components

Each deployment creates:

### Central US Resources
- AKS cluster (Kubernetes 1.31.2)
- Azure Container Registry (Basic SKU)
- Service Bus namespace with queues/topics
- Key Vault
- Application Insights
- Log Analytics workspaces (2)

### East US Resources
- Azure AI Foundry (AI Hub + Project)
- Azure OpenAI (GPT-4o, GPT-4o-mini, GPT-3.5-turbo)
- Storage Account for AI services

## Monitoring Deployments

### View Deployment Status
- GitHub Actions tab shows real-time progress
- Deployment summary shows created resources
- AKS connection is automatically verified

### Check Deployment Outputs
After successful deployment, the workflow outputs:
- Resource group name
- AKS cluster name
- ACR login server
- AI Foundry endpoint
- OpenAI endpoint
- Service Bus namespace
- Key Vault name

### Troubleshooting

**Validation fails:**
```bash
# Test locally
az bicep build --file infrastructure/bicep/main-rg.bicep
```

**Deployment fails with quota errors:**
- Check Azure quota limits in your subscription
- Run validation before deployment
- Review PORTAL_DEPLOYMENT.md for quota requirements

**Authentication fails:**
- Verify GitHub secrets are correct
- Check service principal has Contributor role
- Ensure federated credentials match your repo

**ACR deployment fails:**
- Subscription only supports Basic SKU
- Ensure API version is 2019-05-01
- Check for existing ACR naming conflicts

## Next Steps

After infrastructure is deployed via GitHub Actions:

1. **Connect to AKS**: `az aks get-credentials --resource-group multiagent-dev-rg --name multiagent-dev-aks`
2. **Build application containers**: Use the `build-and-deploy.yml` workflow
3. **Store secrets in Key Vault**: Run `./scripts/store-secrets.sh`
4. **Deploy applications**: Push application code to trigger build pipeline

## Security Best Practices

✅ **Use workload identity federation** (no secrets in GitHub)
✅ **Limit service principal scope** to specific resource groups
✅ **Enable environment protection rules** for production
✅ **Rotate credentials regularly** (if using client secrets)
✅ **Review deployment logs** for sensitive information
✅ **Use managed identities** for Azure resource access

## Resources

- [GitHub Actions for Azure](https://github.com/Azure/actions)
- [Workload Identity Federation](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-azure)
- [Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [Portal Deployment Guide](../infrastructure/PORTAL_DEPLOYMENT.md) (fallback method)
