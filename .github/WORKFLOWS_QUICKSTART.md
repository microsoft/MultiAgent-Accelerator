# GitHub Actions Workflows - Quick Start

## Available Workflows

### 1. Deploy Infrastructure (`deploy-infrastructure.yml`)
**Purpose**: Deploy Azure infrastructure using Bicep templates

**Triggers**:
- 🔄 **Automatic**: Push to `main` branch (only if Bicep files changed)
- 🚀 **Manual**: Workflow dispatch for staging/production

**What it does**:
- Validates Bicep templates
- Creates resource group (if needed)
- Deploys infrastructure to Azure
- Connects to AKS cluster
- Outputs deployment details

### 2. PR Validation (`pr-validation.yml`)
**Purpose**: Validate code changes in pull requests

**Triggers**:
- 🔍 **Automatic**: Pull request to `main` branch

**What it does**:
- Lints Bicep files
- Lints Python code (Black, Flake8)
- Runs Python tests
- Security scan with Trivy

### 3. Build and Deploy (`build-and-deploy.yml`)
**Purpose**: Build Docker images and deploy to AKS

**Triggers**:
- 🔄 **Automatic**: Push to `main` branch (when application code changes)
- 🚀 **Manual**: Workflow dispatch

**What it does**:
- Builds Docker images
- Pushes to Azure Container Registry
- Deploys to AKS cluster
- Updates Kubernetes deployments

## Quick Setup (5 minutes)

### Step 1: Create Service Principal
```bash
# Create service principal with Contributor role
az ad sp create-for-rbac \
  --name "github-actions-multiagent" \
  --role Contributor \
  --scopes /subscriptions/38f95434-aef9-4dc4-97e9-cb69f25825f0 \
  --sdk-auth
```

**Save the output!** You'll need the `clientId` for the next step.

### Step 1.1: Add User Access Administrator Role
```powershell
# Replace with your clientId from Step 1
az role assignment create `
  --assignee YOUR_CLIENT_ID_HERE `
  --role "User Access Administrator" `
  --scope "/subscriptions/38f95434-aef9-4dc4-97e9-cb69f25825f0"
```

**Required roles:**
- ✅ **Contributor** - Creates resources
- ✅ **User Access Administrator** - Assigns roles between resources

### Step 2: Add GitHub Secrets
Go to: **Settings** → **Secrets and variables** → **Actions**

Add these 3 secrets:
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID` 
- `AZURE_SUBSCRIPTION_ID`

### Step 3: Create Environments
Go to: **Settings** → **Environments**

Create:
- `development` (no restrictions)
- `staging` (optional: require reviews)
- `production` (require reviews + wait timer)

### Step 4: Test It!
```bash
git add .github/
git commit -m "Configure GitHub Actions"
git push origin main
```

Go to **Actions** tab to see it run! 🎉

## Common Use Cases

### Deploy Development Infrastructure
```bash
# Just push changes to main
git add infrastructure/bicep/
git commit -m "Update AKS node count"
git push origin main
```

### Deploy to Staging/Production
1. Go to **Actions** tab
2. Select **Deploy Infrastructure**
3. Click **Run workflow**
4. Choose environment: `staging` or `prod`
5. Click **Run workflow** button

### Test Before Deploying
```bash
# Create a pull request
git checkout -b feature/my-changes
git add .
git commit -m "My changes"
git push origin feature/my-changes

# Create PR in GitHub - validation runs automatically
```

### Build and Deploy Application
```bash
# Push application code changes
git add src/
git commit -m "Add new agent feature"
git push origin main

# Build workflow runs automatically
```

## Workflow Status

Check workflow status:
- ✅ **Success**: Green checkmark
- ❌ **Failed**: Red X (click to see logs)
- 🟡 **Running**: Yellow dot
- ⏸️ **Waiting**: Awaiting approval

## What Gets Deployed

### Infrastructure Resources
| Resource | Name Pattern | Location |
|----------|-------------|----------|
| Resource Group | `multiagent-{env}-rg` | Central US |
| AKS Cluster | `multiagent-{env}-aks` | Central US |
| Container Registry | `acrma{env}{random}` | Central US |
| Service Bus | `multiagent-{env}-servicebus` | Central US |
| Key Vault | `multiagent-{env}-kv` | Central US |
| App Insights | `multiagent-{env}-appinsights` | Central US |
| AI Hub | `multiagent-{env}-aihub` | East US |
| OpenAI | `multiagent-{env}-openai` | East US |

### Application Components (Future)
- MCP Servers
- Agent Orchestrator
- Specialist Agents
- Web UI
- Message Queue Workers

## Troubleshooting

### "Context access might be invalid" warnings
**Solution**: These are just warnings about missing secrets - add them in Step 2 above.

### "Resource group not found"
**Solution**: The workflow creates it automatically. If it fails, create manually:
```bash
az group create --name multiagent-dev-rg --location centralus
```

### "Deployment failed - quota exceeded"
**Solution**: Check your subscription quotas:
```bash
az vm list-usage --location centralus -o table
```

### "ACR deployment failed"
**Solution**: Your subscription only supports Basic SKU (already configured correctly).

### "Cannot find Bicep file"
**Solution**: Ensure you're using `main-rg.bicep` (not `main.bicep` which was removed).

## Next Steps

After infrastructure is deployed:

1. **Connect to AKS**:
   ```bash
   az aks get-credentials --resource-group multiagent-dev-rg --name multiagent-dev-aks
   kubectl get nodes
   ```

2. **Login to ACR**:
   ```bash
   az acr login --name $(az acr list -g multiagent-dev-rg --query "[0].name" -o tsv)
   ```

3. **Get OpenAI Keys**:
   ```bash
   az cognitiveservices account keys list \
     --resource-group multiagent-dev-rg \
     --name multiagent-dev-openai
   ```

4. **Store Secrets**:
   ```bash
   ./scripts/store-secrets.sh
   ```

## Tips

💡 **Pro Tip**: Use branch protection rules to require PR validation before merging to `main`

💡 **Pro Tip**: Enable environment protection rules for production to require manual approval

💡 **Pro Tip**: Check the Actions tab regularly to see deployment history and logs

💡 **Pro Tip**: Use workflow dispatch for manual deployments without code changes

## Full Documentation

- 📖 [Complete GitHub Actions Setup Guide](.github/GITHUB_ACTIONS_SETUP.md)
- 📖 [Portal Deployment Guide](../infrastructure/PORTAL_DEPLOYMENT.md) (fallback method)
- 📖 [Infrastructure Documentation](../docs/INFRASTRUCTURE_DEPLOYMENT.md)
