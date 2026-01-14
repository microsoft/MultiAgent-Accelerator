#!/bin/bash
# Deploy Multi-Agent System to Azure Container Apps

set -e

# Default values
DEFAULT_ENVIRONMENT="dev"

# Script usage
usage() {
    echo "🚀 Deploy Multi-Agent System to Azure Container Apps"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -g, --resource-group RESOURCE_GROUP    Target resource group name (required)"
    echo "  -p, --project-name PROJECT_NAME        Project name prefix (required)"
    echo "  -e, --environment ENVIRONMENT          Environment (dev/staging/prod) [default: $DEFAULT_ENVIRONMENT]"
    echo "  -b, --build-only                       Only build and push images (don't deploy)"
    echo "  -d, --deploy-only                      Only deploy (skip building images)"
    echo "  -h, --help                             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -g multiagent-demo-rg -p multiagentaml01"
    echo "  $0 -g multiagent-demo-rg -p multiagentaml01 -e prod"
    echo "  $0 -g multiagent-demo-rg -p multiagentaml01 -b"
}

# Parse command line arguments
RESOURCE_GROUP=""
PROJECT_NAME=""
ENVIRONMENT="$DEFAULT_ENVIRONMENT"
BUILD_ONLY=false
DEPLOY_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -p|--project-name)
            PROJECT_NAME="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -b|--build-only)
            BUILD_ONLY=true
            shift
            ;;
        -d|--deploy-only)
            DEPLOY_ONLY=true
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
    usage
    exit 1
fi

if [[ -z "$PROJECT_NAME" ]]; then
    echo "❌ Error: Project name is required"
    usage
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."

echo "🚀 Multi-Agent System - Container Apps Deployment"
echo "=================================================="
echo ""

# Check Azure CLI login
echo "🔐 Checking Azure CLI authentication..."
if ! az account show >/dev/null 2>&1; then
    echo "❌ Error: Not logged in to Azure CLI. Please run 'az login' first."
    exit 1
fi
echo "  ✅ Logged in to Azure"

# Get resource names from the resource group
echo ""
echo "📝 Discovering resources..."

ACR_NAME=$(az acr list -g "$RESOURCE_GROUP" --query '[0].name' -o tsv 2>/dev/null)
if [[ -z "$ACR_NAME" ]]; then
    echo "❌ Error: No ACR found in resource group $RESOURCE_GROUP"
    exit 1
fi
ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"

CONTAINER_ENV_NAME=$(az containerapp env list -g "$RESOURCE_GROUP" --query '[0].name' -o tsv 2>/dev/null)
if [[ -z "$CONTAINER_ENV_NAME" ]]; then
    echo "❌ Error: No Container Apps Environment found in resource group $RESOURCE_GROUP"
    exit 1
fi

OPENAI_NAME=$(az cognitiveservices account list -g "$RESOURCE_GROUP" --query "[?kind=='OpenAI'].name | [0]" -o tsv 2>/dev/null)
OPENAI_ENDPOINT=$(az cognitiveservices account show -g "$RESOURCE_GROUP" -n "$OPENAI_NAME" --query "properties.endpoint" -o tsv 2>/dev/null)

# Get OpenAI deployment name (first available deployment)
OPENAI_DEPLOYMENT=$(az cognitiveservices account deployment list -g "$RESOURCE_GROUP" -n "$OPENAI_NAME" --query "[0].name" -o tsv 2>/dev/null)

SERVICEBUS_NAMESPACE=$(az servicebus namespace list -g "$RESOURCE_GROUP" --query '[0].name' -o tsv 2>/dev/null)

# Get resource IDs for role assignments
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SERVICEBUS_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ServiceBus/namespaces/$SERVICEBUS_NAMESPACE"
OPENAI_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/$OPENAI_NAME"

# Role Definition IDs (these are constant across Azure)
SERVICEBUS_ROLE_ID="090c5cfd-751d-490a-894a-3ce6f1109419"  # Azure Service Bus Data Owner
OPENAI_ROLE_ID="5e0bd9bd-7b93-4f28-af87-19fc36ad61bd"      # Cognitive Services OpenAI User

echo ""
echo "📋 Configuration:"
echo "  Resource Group:              $RESOURCE_GROUP"
echo "  Project Name:                $PROJECT_NAME"
echo "  Environment:                 $ENVIRONMENT"
echo "  ACR:                         $ACR_LOGIN_SERVER"
echo "  Container Apps Environment:  $CONTAINER_ENV_NAME"
echo "  OpenAI:                      $OPENAI_NAME"
echo "  OpenAI Endpoint:             $OPENAI_ENDPOINT"
echo "  OpenAI Deployment:           $OPENAI_DEPLOYMENT"
echo "  Service Bus:                 $SERVICEBUS_NAMESPACE"
echo ""

# ============================================
# BUILD AND PUSH IMAGES
# ============================================
if [[ "$DEPLOY_ONLY" != true ]]; then
    echo "🏗️  Building and pushing Docker images to ACR..."
    echo ""

    # Login to ACR
    echo "🔐 Logging in to ACR..."
    az acr login --name "$ACR_NAME"

    # Build and push Currency MCP Server
    echo ""
    echo "📦 Building currency-mcp..."
    docker build -t "$ACR_LOGIN_SERVER/currency-mcp:latest" "$PROJECT_ROOT/mcp_servers/currency_mcp"
    docker push "$ACR_LOGIN_SERVER/currency-mcp:latest"
    echo "  ✅ currency-mcp pushed"

    # Build and push Activity MCP Server
    echo ""
    echo "📦 Building activity-mcp..."
    docker build -t "$ACR_LOGIN_SERVER/activity-mcp:latest" "$PROJECT_ROOT/mcp_servers/activity_mcp"
    docker push "$ACR_LOGIN_SERVER/activity-mcp:latest"
    echo "  ✅ activity-mcp pushed"

    # Build and push Travel Agent
    echo ""
    echo "📦 Building travel-agent..."
    docker build -t "$ACR_LOGIN_SERVER/travel-agent:latest" "$PROJECT_ROOT/agents/travel_agent"
    docker push "$ACR_LOGIN_SERVER/travel-agent:latest"
    echo "  ✅ travel-agent pushed"

    # Build and push Orchestrator
    echo ""
    echo "📦 Building orchestrator..."
    docker build -t "$ACR_LOGIN_SERVER/orchestrator:latest" "$PROJECT_ROOT/agents/orchestrator"
    docker push "$ACR_LOGIN_SERVER/orchestrator:latest"
    echo "  ✅ orchestrator pushed"

    # Build and push Web UI
    echo ""
    echo "📦 Building web-ui..."
    docker build -t "$ACR_LOGIN_SERVER/web-ui:latest" "$PROJECT_ROOT/web_ui"
    docker push "$ACR_LOGIN_SERVER/web-ui:latest"
    echo "  ✅ web-ui pushed"

    echo ""
    echo "✅ All images built and pushed successfully!"

    if [[ "$BUILD_ONLY" == true ]]; then
        echo ""
        echo "🎉 Build completed (build-only mode)."
        exit 0
    fi
fi

# ============================================
# DEPLOY TO CONTAINER APPS
# ============================================
echo ""
echo "🚀 Deploying Container Apps..."

# Enable ACR admin credentials for Container Apps
echo ""
echo "🔑 Enabling ACR admin credentials..."
az acr update -n "$ACR_NAME" --admin-enabled true
ACR_PASSWORD=$(az acr credential show -n "$ACR_NAME" --query "passwords[0].value" -o tsv)

# Function to assign Managed Identity and roles to a Container App
assign_identity_and_roles() {
    local APP_NAME=$1
    echo "  🔐 Enabling Managed Identity for $APP_NAME..."
    
    PRINCIPAL_ID=$(az containerapp identity assign \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --system-assigned \
        --query principalId -o tsv 2>/dev/null)
    
    if [[ -n "$PRINCIPAL_ID" ]]; then
        echo "    Principal ID: $PRINCIPAL_ID"
        
        # Assign Service Bus role using REST API
        ASSIGNMENT_ID_SB=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || echo "${APP_NAME}-sb-$(date +%s)")
        az rest --method put \
            --url "https://management.azure.com${SERVICEBUS_ID}/providers/Microsoft.Authorization/roleAssignments/${ASSIGNMENT_ID_SB}?api-version=2022-04-01" \
            --body "{\"properties\": {\"roleDefinitionId\": \"/subscriptions/$SUBSCRIPTION_ID/providers/Microsoft.Authorization/roleDefinitions/$SERVICEBUS_ROLE_ID\", \"principalId\": \"$PRINCIPAL_ID\", \"principalType\": \"ServicePrincipal\"}}" \
            >/dev/null 2>&1 || true
        echo "    ✅ Service Bus role assigned"
        
        # Assign OpenAI role using REST API
        ASSIGNMENT_ID_OAI=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || echo "${APP_NAME}-oai-$(date +%s)")
        az rest --method put \
            --url "https://management.azure.com${OPENAI_ID}/providers/Microsoft.Authorization/roleAssignments/${ASSIGNMENT_ID_OAI}?api-version=2022-04-01" \
            --body "{\"properties\": {\"roleDefinitionId\": \"/subscriptions/$SUBSCRIPTION_ID/providers/Microsoft.Authorization/roleDefinitions/$OPENAI_ROLE_ID\", \"principalId\": \"$PRINCIPAL_ID\", \"principalType\": \"ServicePrincipal\"}}" \
            >/dev/null 2>&1 || true
        echo "    ✅ OpenAI role assigned"
    fi
}

# Common environment variables
COMMON_ENV_VARS="AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT AZURE_OPENAI_DEPLOYMENT=$OPENAI_DEPLOYMENT SERVICEBUS_NAMESPACE=${SERVICEBUS_NAMESPACE}.servicebus.windows.net"

# Deploy Currency MCP Server
echo ""
echo "🚢 Deploying currency-mcp..."
az containerapp create \
    --name "${PROJECT_NAME}-currency-mcp" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$CONTAINER_ENV_NAME" \
    --image "$ACR_LOGIN_SERVER/currency-mcp:latest" \
    --registry-server "$ACR_LOGIN_SERVER" \
    --registry-username "$ACR_NAME" \
    --registry-password "$ACR_PASSWORD" \
    --target-port 8001 \
    --ingress internal \
    --min-replicas 1 \
    --max-replicas 3 \
    --cpu 0.25 \
    --memory 0.5Gi \
    --env-vars $COMMON_ENV_VARS \
    2>/dev/null || \
az containerapp update \
    --name "${PROJECT_NAME}-currency-mcp" \
    --resource-group "$RESOURCE_GROUP" \
    --image "$ACR_LOGIN_SERVER/currency-mcp:latest"
echo "  ✅ currency-mcp deployed"
assign_identity_and_roles "${PROJECT_NAME}-currency-mcp"

# Deploy Activity MCP Server
echo ""
echo "🚢 Deploying activity-mcp..."
az containerapp create \
    --name "${PROJECT_NAME}-activity-mcp" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$CONTAINER_ENV_NAME" \
    --image "$ACR_LOGIN_SERVER/activity-mcp:latest" \
    --registry-server "$ACR_LOGIN_SERVER" \
    --registry-username "$ACR_NAME" \
    --registry-password "$ACR_PASSWORD" \
    --target-port 8002 \
    --ingress internal \
    --min-replicas 1 \
    --max-replicas 3 \
    --cpu 0.25 \
    --memory 0.5Gi \
    --env-vars $COMMON_ENV_VARS \
    2>/dev/null || \
az containerapp update \
    --name "${PROJECT_NAME}-activity-mcp" \
    --resource-group "$RESOURCE_GROUP" \
    --image "$ACR_LOGIN_SERVER/activity-mcp:latest"
echo "  ✅ activity-mcp deployed"
assign_identity_and_roles "${PROJECT_NAME}-activity-mcp"

# Get internal URLs for MCP servers (actual FQDNs from Azure)
CURRENCY_MCP_FQDN=$(az containerapp show -g "$RESOURCE_GROUP" -n "${PROJECT_NAME}-currency-mcp" --query "properties.configuration.ingress.fqdn" -o tsv)
ACTIVITY_MCP_FQDN=$(az containerapp show -g "$RESOURCE_GROUP" -n "${PROJECT_NAME}-activity-mcp" --query "properties.configuration.ingress.fqdn" -o tsv)
CURRENCY_MCP_URL="https://$CURRENCY_MCP_FQDN"
ACTIVITY_MCP_URL="https://$ACTIVITY_MCP_FQDN"

# Deploy Travel Agent
echo ""
echo "🚢 Deploying travel-agent..."
az containerapp create \
    --name "${PROJECT_NAME}-travel-agent" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$CONTAINER_ENV_NAME" \
    --image "$ACR_LOGIN_SERVER/travel-agent:latest" \
    --registry-server "$ACR_LOGIN_SERVER" \
    --registry-username "$ACR_NAME" \
    --registry-password "$ACR_PASSWORD" \
    --target-port 8080 \
    --ingress internal \
    --min-replicas 1 \
    --max-replicas 5 \
    --cpu 0.5 \
    --memory 1Gi \
    --env-vars $COMMON_ENV_VARS \
        CURRENCY_MCP_URL="$CURRENCY_MCP_URL" \
        ACTIVITY_MCP_URL="$ACTIVITY_MCP_URL" \
    2>/dev/null || \
az containerapp update \
    --name "${PROJECT_NAME}-travel-agent" \
    --resource-group "$RESOURCE_GROUP" \
    --image "$ACR_LOGIN_SERVER/travel-agent:latest" \
    --set-env-vars \
        CURRENCY_MCP_URL="$CURRENCY_MCP_URL" \
        ACTIVITY_MCP_URL="$ACTIVITY_MCP_URL"
echo "  ✅ travel-agent deployed"
assign_identity_and_roles "${PROJECT_NAME}-travel-agent"

# Get Travel Agent internal URL (actual FQDN from Azure)
TRAVEL_AGENT_FQDN=$(az containerapp show -g "$RESOURCE_GROUP" -n "${PROJECT_NAME}-travel-agent" --query "properties.configuration.ingress.fqdn" -o tsv)
TRAVEL_AGENT_URL="https://$TRAVEL_AGENT_FQDN"

# Deploy Orchestrator (internal ingress)
echo ""
echo "🚢 Deploying orchestrator..."
az containerapp create \
    --name "${PROJECT_NAME}-orchestrator" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$CONTAINER_ENV_NAME" \
    --image "$ACR_LOGIN_SERVER/orchestrator:latest" \
    --registry-server "$ACR_LOGIN_SERVER" \
    --registry-username "$ACR_NAME" \
    --registry-password "$ACR_PASSWORD" \
    --target-port 8000 \
    --ingress internal \
    --min-replicas 1 \
    --max-replicas 5 \
    --cpu 0.5 \
    --memory 1Gi \
    --env-vars $COMMON_ENV_VARS \
        TRAVEL_AGENT_URL="$TRAVEL_AGENT_URL" \
    2>/dev/null || \
az containerapp update \
    --name "${PROJECT_NAME}-orchestrator" \
    --resource-group "$RESOURCE_GROUP" \
    --image "$ACR_LOGIN_SERVER/orchestrator:latest"
echo "  ✅ orchestrator deployed"
assign_identity_and_roles "${PROJECT_NAME}-orchestrator"

# Get Orchestrator internal URL (actual FQDN from Azure)
ORCHESTRATOR_FQDN=$(az containerapp show -g "$RESOURCE_GROUP" -n "${PROJECT_NAME}-orchestrator" --query "properties.configuration.ingress.fqdn" -o tsv)
ORCHESTRATOR_INTERNAL_URL="https://$ORCHESTRATOR_FQDN"

# Set AGENT_ENDPOINTS on orchestrator to discover travel-agent
echo ""
echo "🔗 Configuring agent discovery..."
az containerapp update \
    --name "${PROJECT_NAME}-orchestrator" \
    --resource-group "$RESOURCE_GROUP" \
    --set-env-vars "AGENT_ENDPOINTS=https://$TRAVEL_AGENT_FQDN/.well-known/agent.json"
echo "  ✅ AGENT_ENDPOINTS configured"

# Deploy Web UI (external ingress - public)
echo ""
echo "🚢 Deploying web-ui (public)..."
az containerapp create \
    --name "${PROJECT_NAME}-web-ui" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$CONTAINER_ENV_NAME" \
    --image "$ACR_LOGIN_SERVER/web-ui:latest" \
    --registry-server "$ACR_LOGIN_SERVER" \
    --registry-username "$ACR_NAME" \
    --registry-password "$ACR_PASSWORD" \
    --target-port 8501 \
    --ingress external \
    --min-replicas 1 \
    --max-replicas 3 \
    --cpu 0.5 \
    --memory 1Gi \
    --env-vars \
        ORCHESTRATOR_URL="$ORCHESTRATOR_INTERNAL_URL" \
    2>/dev/null || \
az containerapp update \
    --name "${PROJECT_NAME}-web-ui" \
    --resource-group "$RESOURCE_GROUP" \
    --image "$ACR_LOGIN_SERVER/web-ui:latest"
echo "  ✅ web-ui deployed"

# ============================================
# GET DEPLOYMENT INFORMATION
# ============================================
echo ""
echo "📊 Deployment Summary"
echo "====================="
echo ""

# Get Web UI URL
WEB_UI_FQDN=$(az containerapp show \
    --name "${PROJECT_NAME}-web-ui" \
    --resource-group "$RESOURCE_GROUP" \
    --query "properties.configuration.ingress.fqdn" -o tsv)

echo "📋 Container Apps Deployed:"
echo ""
az containerapp list -g "$RESOURCE_GROUP" --query "[].{Name:name, Status:properties.runningStatus, URL:properties.configuration.ingress.fqdn}" -o table

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "🌐 Web UI URL: https://$WEB_UI_FQDN"
echo ""
echo "🧪 Open in browser:"
echo "  https://$WEB_UI_FQDN"
echo ""
echo "📝 Architecture:"
echo "  User → Web UI (public) → Orchestrator (internal) → Travel Agent → MCP Servers"
echo ""
echo "🎉 Done!"
