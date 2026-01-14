#!/bin/bash
# Deploy Multi-Agent System Infrastructure using Bicep

set -e

# Default values
DEFAULT_ENVIRONMENT="dev"
DEFAULT_PROJECT_NAME="multiagent"
DEFAULT_LOCATION="centralus"

# Script usage
usage() {
    echo "🚀 Deploy Multi-Agent System Infrastructure"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -g, --resource-group RESOURCE_GROUP    Target resource group name (required)"
    echo "  -e, --environment ENVIRONMENT          Environment (dev/staging/prod) [default: $DEFAULT_ENVIRONMENT]"
    echo "  -p, --project-name PROJECT_NAME        Project name prefix [default: $DEFAULT_PROJECT_NAME]"
    echo "  -l, --location LOCATION                Azure region [default: $DEFAULT_LOCATION]"
    echo "  -c, --create-rg                        Create resource group if it doesn't exist"
    echo "  -v, --validate-only                    Only validate the template (don't deploy)"
    echo "  -h, --help                            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -g my-multiagent-rg -c"
    echo "  $0 -g my-multiagent-rg -e prod -p myproject -l eastus"
    echo "  $0 -g my-multiagent-rg -v"
}

# Parse command line arguments
RESOURCE_GROUP=""
ENVIRONMENT="$DEFAULT_ENVIRONMENT"
PROJECT_NAME="$DEFAULT_PROJECT_NAME"
LOCATION="$DEFAULT_LOCATION"
CREATE_RG=false
VALIDATE_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--project-name)
            PROJECT_NAME="$2"
            shift 2
            ;;
        -l|--location)
            LOCATION="$2"
            shift 2
            ;;
        -c|--create-rg)
            CREATE_RG=true
            shift
            ;;
        -v|--validate-only)
            VALIDATE_ONLY=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$RESOURCE_GROUP" ]]; then
    echo "❌ Error: Resource group name is required"
    echo ""
    usage
    exit 1
fi

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo "❌ Error: Environment must be one of: dev, staging, prod"
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BICEP_DIR="$SCRIPT_DIR/../infrastructure/bicepv3"
BICEP_FILE="$BICEP_DIR/main-rg.bicep"

# Verify bicep file exists
if [[ ! -f "$BICEP_FILE" ]]; then
    echo "❌ Error: Bicep template not found at $BICEP_FILE"
    exit 1
fi

echo "🚀 Multi-Agent System Infrastructure Deployment"
echo "================================================"
echo ""
echo "📝 Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Environment:    $ENVIRONMENT"
echo "  Project Name:   $PROJECT_NAME"
echo "  Location:       $LOCATION"
echo "  Bicep Template: $BICEP_FILE"
echo ""

# Check Azure CLI login
echo "🔐 Checking Azure CLI authentication..."
if ! az account show >/dev/null 2>&1; then
    echo "❌ Error: Not logged in to Azure CLI. Please run 'az login' first."
    exit 1
fi

CURRENT_SUBSCRIPTION=$(az account show --query name -o tsv)
echo "  ✅ Logged in to subscription: $CURRENT_SUBSCRIPTION"

# Check if resource group exists and create if needed
echo ""
echo "📦 Checking resource group..."
if az group show --name "$RESOURCE_GROUP" >/dev/null 2>&1; then
    echo "  ✅ Resource group '$RESOURCE_GROUP' already exists"
else
    echo "  🆕 Resource group '$RESOURCE_GROUP' does not exist. Creating it in '$LOCATION'..."
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
    if [[ $? -eq 0 ]]; then
        echo "  ✅ Resource group created successfully"
    else
        echo "❌ Error: Failed to create resource group '$RESOURCE_GROUP'"
        exit 1
    fi
fi

# Validate the bicep template
echo ""
echo "🔍 Validating Bicep template..."
VALIDATION_OUTPUT=$(az deployment group validate \
    --resource-group "$RESOURCE_GROUP" \
    --template-file "$BICEP_FILE" \
    --parameters \
        environment="$ENVIRONMENT" \
        projectName="$PROJECT_NAME" \
        location="$LOCATION" \
    2>&1)

VALIDATION_EXIT_CODE=$?
if [[ $VALIDATION_EXIT_CODE -ne 0 ]]; then
    echo "❌ Template validation failed:"
    echo "$VALIDATION_OUTPUT"
    exit 1
fi

echo "  ✅ Template validation passed"

# If validate-only mode, exit here
if [[ "$VALIDATE_ONLY" == true ]]; then
    echo ""
    echo "✅ Validation completed successfully. Exiting (validate-only mode)."
    exit 0
fi

# Deploy the infrastructures
echo ""
echo "🚀 Deploying infrastructure..."
echo "  This may take 2-3 minutes..."

DEPLOYMENT_NAME="multiagent-infrastructure-$(date +%Y%m%d-%H%M%S)"

az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file "$BICEP_FILE" \
    --name "$DEPLOYMENT_NAME" \
    --parameters \
        environment="$ENVIRONMENT" \
        projectName="$PROJECT_NAME" \
        location="$LOCATION" \
    --verbose

DEPLOYMENT_EXIT_CODE=$?

if [[ $DEPLOYMENT_EXIT_CODE -eq 0 ]]; then
    echo ""
    echo "✅ Infrastructure deployment completed successfully!"
    echo ""
    
    # Get and display key outputs
    echo "📋 Key Resources Created:"
    echo "========================"
    
    AKS_NAME=$(az deployment group show -g "$RESOURCE_GROUP" -n "$DEPLOYMENT_NAME" --query 'properties.outputs.aksClusterName.value' -o tsv 2>/dev/null || echo "N/A")
    CONTAINER_APP_NAME=$(az deployment group show -g "$RESOURCE_GROUP" -n "$DEPLOYMENT_NAME" --query 'properties.outputs.containerAppName.value' -o tsv 2>/dev/null || echo "N/A")

    ACR_LOGIN_SERVER=$(az deployment group show -g "$RESOURCE_GROUP" -n "$DEPLOYMENT_NAME" --query 'properties.outputs.acrLoginServer.value' -o tsv 2>/dev/null || echo "N/A")
    OPENAI_ENDPOINT=$(az deployment group show -g "$RESOURCE_GROUP" -n "$DEPLOYMENT_NAME" --query 'properties.outputs.openAIEndpoint.value' -o tsv 2>/dev/null || echo "N/A")
    SERVICEBUS_NAMESPACE=$(az deployment group show -g "$RESOURCE_GROUP" -n "$DEPLOYMENT_NAME" --query 'properties.outputs.serviceBusNamespace.value' -o tsv 2>/dev/null || echo "N/A")
    KEYVAULT_NAME=$(az deployment group show -g "$RESOURCE_GROUP" -n "$DEPLOYMENT_NAME" --query 'properties.outputs.keyVaultName.value' -o tsv 2>/dev/null || echo "N/A")
    WORKLOAD_IDENTITY_CLIENT_ID=$(az deployment group show -g "$RESOURCE_GROUP" -n "$DEPLOYMENT_NAME" --query 'properties.outputs.workloadIdentityClientId.value' -o tsv 2>/dev/null || echo "N/A")
    
    echo "  AKS Cluster:              $AKS_NAME"
    echo "  Container App:            $CONTAINER_APP_NAME"
    echo "  Container Registry:       $ACR_LOGIN_SERVER"
    echo "  OpenAI Endpoint:          $OPENAI_ENDPOINT"
    echo "  Service Bus Namespace:    $SERVICEBUS_NAMESPACE"
    echo "  Key Vault:                $KEYVAULT_NAME"
    echo "  Workload Identity ID:     $WORKLOAD_IDENTITY_CLIENT_ID"
    
    echo ""
    echo "🎯 Next Steps:"
    echo "=============="
    echo "1. Deploy agents to Landing Zone:"
    echo ""
    echo "2. Build and push container images:"
    echo "   ./build-and-push.sh -g $RESOURCE_GROUP"
    echo ""
    echo "3. Deploy agents to Azure Container Apps:"
    echo ""
else
    echo ""
    echo "❌ Infrastructure deployment failed with exit code: $DEPLOYMENT_EXIT_CODE"
    echo ""
    echo "🔍 Troubleshooting:"
    echo "==================="
    echo "1. Check the deployment in Azure Portal:"
    echo "   Resource Group: $RESOURCE_GROUP"
    echo "   Deployment: $DEPLOYMENT_NAME"
    echo ""
    echo "2. View deployment logs:"
    echo "   az deployment group show -g $RESOURCE_GROUP -n $DEPLOYMENT_NAME"
    echo ""
    echo "3. Check Azure resource quotas and permissions"
    exit 1
fi