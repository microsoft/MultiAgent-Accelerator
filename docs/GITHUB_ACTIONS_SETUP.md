# GitHub Actions Setup Guide

This guide explains how to configure GitHub Actions for automated deployment.

## Authentication Method: Workload Identity (Recommended)

GitHub Actions uses Azure Workload Identity Federation for secure, passwordless authentication.

## Setup Steps

### 1. Create Azure AD Application

```bash
# Set your GitHub repository info
GITHUB_ORG="<your-github-org>"
GITHUB_REPO="<your-repo-name>"
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Create Azure AD Application
APP_NAME="multiagent-github-actions"
APP_ID=$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)

echo "Application ID: $APP_ID"
```

### 2. Create Service Principal

```bash
# Create service principal
az ad sp create --id $APP_ID

# Get Object ID
OBJECT_ID=$(az ad sp show --id $APP_ID --query id -o tsv)

echo "Object ID: $OBJECT_ID"
```

### 3. Assign Azure Permissions

```bash
# Assign Contributor role at subscription level
az role assignment create \
  --assignee $APP_ID \
  --role Contributor \
  --scope /subscriptions/$SUBSCRIPTION_ID

# Verify assignment
az role assignment list --assignee $APP_ID --output table
```

### 4. Configure Federated Credentials

Create federated credentials for different branches/environments:

```bash
# Get Tenant ID
TENANT_ID=$(az account show --query tenantId -o tsv)

# Main branch (production)
az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "multiagent-github-main",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:'$GITHUB_ORG'/'$GITHUB_REPO':ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'

# Pull requests
az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "multiagent-github-pr",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:'$GITHUB_ORG'/'$GITHUB_REPO':pull_request",
    "audiences": ["api://AzureADTokenExchange"]
  }'

# Development branch (optional)
az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "multiagent-github-dev",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:'$GITHUB_ORG'/'$GITHUB_REPO':ref:refs/heads/dev",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

### 5. Save Credentials

Save these values - you'll need them for GitHub Secrets:

```bash
echo ""
echo "=== GitHub Secrets Configuration ==="
echo "AZURE_CLIENT_ID: $APP_ID"
echo "AZURE_TENANT_ID: $TENANT_ID"
echo "AZURE_SUBSCRIPTION_ID: $SUBSCRIPTION_ID"
echo ""
```

### 6. Configure GitHub Repository Secrets

Go to your GitHub repository:

1. Navigate to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add the following secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AZURE_CLIENT_ID` | `<APP_ID from above>` | Application (client) ID |
| `AZURE_TENANT_ID` | `<TENANT_ID from above>` | Directory (tenant) ID |
| `AZURE_SUBSCRIPTION_ID` | `<SUBSCRIPTION_ID from above>` | Azure subscription ID |

### 7. Configure Environments (Optional but Recommended)

Create GitHub environments for better control:

1. Go to **Settings** → **Environments**
2. Create environments: `development`, `staging`, `production`
3. Add protection rules (e.g., required reviewers for production)
4. Add environment-specific secrets if needed

## Verify Setup

### Test GitHub Actions Workflow

1. Make a small change to a file
2. Commit and push to main branch:
   ```bash
   git add .
   git commit -m "Test GitHub Actions"
   git push origin main
   ```
3. Go to **Actions** tab in GitHub
4. Watch the workflow run

### Troubleshooting

**Error: "Login failed with Error: ClientAuthError"**
- Verify federated credentials are created correctly
- Check that the subject matches your repository exactly
- Ensure the workflow has `id-token: write` permission

**Error: "Authorization failed"**
- Verify the service principal has Contributor role
- Check that the subscription ID is correct
- Wait a few minutes for role assignments to propagate

**Error: "Resource provider not registered"**
- The workflow will automatically register providers
- Or manually register them (see INFRASTRUCTURE_DEPLOYMENT.md)

## Alternative: Service Principal with Secret

If Workload Identity doesn't work, you can use a service principal with a secret:

```bash
# Create service principal with secret
SP_OUTPUT=$(az ad sp create-for-rbac \
  --name "multiagent-github-actions" \
  --role Contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID \
  --sdk-auth)

echo "$SP_OUTPUT"
```

Then add the entire JSON output as a secret named `AZURE_CREDENTIALS` in GitHub.

**Note:** This method is less secure and not recommended for production.

## Security Best Practices

1. ✅ Use Workload Identity instead of secrets
2. ✅ Use environment protection rules for production
3. ✅ Limit service principal permissions to specific resource groups
4. ✅ Rotate credentials regularly
5. ✅ Enable audit logging for deployments
6. ✅ Use separate service principals for different environments

## Cleanup

To remove the service principal:

```bash
# Delete service principal
az ad sp delete --id $APP_ID

# Delete AD application
az ad app delete --id $APP_ID
```

## Next Steps

After configuring secrets:

1. Push code to trigger workflows
2. Monitor deployments in GitHub Actions
3. Check Azure resources after deployment
4. Review deployment logs

For more information, see:
- [Azure Login Action Documentation](https://github.com/Azure/login)
- [GitHub Actions Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
