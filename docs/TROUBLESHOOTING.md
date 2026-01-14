# Troubleshooting Azure CLI Connection Issues

If you're getting **"Connection aborted" or "Connection reset"** errors, try these solutions:

## Quick Fixes

### 1. Clear Azure CLI Cache and Re-login
```bash
az account clear
az login
az account set --subscription "<your-subscription-id>"
```

### 2. Use Windows CMD Instead of Git Bash
The `.cmd` script is more stable on Windows:
```cmd
scripts\deploy-infrastructure.cmd
```

### 3. Update Azure CLI
```bash
az upgrade
```

### 4. Manual Deployment (Most Reliable)

Open **PowerShell** or **Command Prompt** and run:

```powershell
# Set variables
$location = "centralus"
$environment = "dev"
$projectName = "multiagent"
$deploymentName = "$projectName-$environment-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

# Navigate to bicep directory
cd infrastructure\bicep

# Deploy
az deployment sub create `
  --location $location `
  --template-file main.bicep `
  --parameters main.parameters.json `
  --parameters environment=$environment `
  --parameters projectName=$projectName `
  --name $deploymentName
```

### 5. Deploy from Azure Portal

If CLI continues to fail:

1. Go to [Azure Portal](https://portal.azure.com)
2. Search for **"Deploy a custom template"**
3. Click **"Build your own template in the editor"**
4. Copy the contents of `infrastructure/bicep/main.bicep`
5. Click **"Save"**
6. Fill in parameters:
   - Subscription: Your subscription
   - Location: centralus
   - Environment: dev
   - Project Name: multiagent
7. Click **"Review + create"** then **"Create"**

## Common Causes

### Network/Firewall Issues
- **Corporate VPN/Proxy**: Azure CLI may be blocked
- **Antivirus/Firewall**: Temporarily disable and retry
- **DNS Issues**: Try changing DNS to 8.8.8.8 or 1.1.1.1

### Azure CLI Issues
- **Old version**: Run `az upgrade`
- **Corrupted cache**: Run `az account clear`
- **Python conflicts**: Azure CLI uses Python - check for conflicts

### Azure Subscription Issues
- **Insufficient permissions**: Need Contributor or Owner role
- **Resource provider not registered**: The deployment will register them automatically
- **Quota limits**: Check if you have enough quota for AKS

## Test Your Connection

```bash
# Test 1: Can you reach Azure?
az account show

# Test 2: Can you list resource groups?
az group list

# Test 3: Can you create a simple resource group?
az group create --name test-rg --location centralus
az group delete --name test-rg --yes --no-wait
```

If all tests pass but deployment still fails, the issue is likely with:
- The Bicep template (check for errors)
- Resource provider registration (usually auto-fixed)
- Quota limits (request increase)

## Alternative: Use Azure Cloud Shell

Azure Cloud Shell always works (no local CLI issues):

1. Go to [shell.azure.com](https://shell.azure.com)
2. Choose **Bash**
3. Upload your Bicep files
4. Run the deployment:
   ```bash
   cd ~
   mkdir multiagent && cd multiagent
   # Upload files here
   
   az deployment sub create \
     --location centralus \
     --template-file main.bicep \
     --parameters main.parameters.json \
     --parameters environment=dev \
     --parameters projectName=multiagent \
     --name multiagent-dev-$(date +%Y%m%d-%H%M%S)
   ```

## Get Help

If none of these work:
1. Check [Azure Status](https://status.azure.com/)
2. Post error details to [Azure CLI GitHub](https://github.com/Azure/azure-cli/issues)
3. Contact Azure Support
