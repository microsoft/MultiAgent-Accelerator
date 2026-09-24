# AKS Deployment Guide

This guide explains how to deploy the Multi-Agent System with MCP Servers to Azure Kubernetes Service (AKS).

## Architecture

The deployment consists of:

1. **Currency MCP Server** - Provides currency exchange rate tools via Frankfurter API
2. **Activity MCP Server** - Provides travel activity planning tools
3. **Travel Agent** - MAF agent that uses both MCP servers and Azure OpenAI

## Prerequisites

- Azure CLI installed and logged in
- Docker installed
- kubectl installed
- Infrastructure deployed (ACR, AKS, Azure OpenAI, Workload Identity)

## Deployment Steps

### Option 1: Automated Deployment (Recommended)

Run the deployment script:

```bash
chmod +x scripts/deploy-to-aks.sh
./scripts/deploy-to-aks.sh
```

This script will:
1. Login to Azure Container Registry
2. Build and push all Docker images
3. Get AKS credentials
4. Configure Workload Identity
5. Deploy all services to AKS
6. Wait for pods to be ready
7. Configure internal services with API-key authentication

### Option 2: Manual Deployment

#### Step 1: Build and Push Images

```bash
# Set variables
RESOURCE_GROUP="multiagent-dev-rg"
ACR_NAME=$(az acr list -g $RESOURCE_GROUP --query '[0].name' -o tsv)

# Login to ACR
az acr login --name $ACR_NAME

# Build and push Currency MCP
docker build -t $ACR_NAME.azurecr.io/currency-mcp:latest ./mcp_servers/currency_mcp
docker push $ACR_NAME.azurecr.io/currency-mcp:latest

# Build and push Activity MCP
docker build -t $ACR_NAME.azurecr.io/activity-mcp:latest ./mcp_servers/activity_mcp
docker push $ACR_NAME.azurecr.io/activity-mcp:latest

# Build and push Travel Agent
docker build -t $ACR_NAME.azurecr.io/travel-agent:latest ./agents/travel_agent
docker push $ACR_NAME.azurecr.io/travel-agent:latest
```

#### Step 2: Get AKS Credentials

```bash
AKS_NAME=$(az aks list -g $RESOURCE_GROUP --query '[0].name' -o tsv)
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_NAME
```

#### Step 3: Configure Environment Variables

```bash
OPENAI_NAME=$(az cognitiveservices account list -g $RESOURCE_GROUP --query "[?kind=='OpenAI'].name" -o tsv)
WORKLOAD_IDENTITY_CLIENT_ID=$(az identity show -g $RESOURCE_GROUP -n multiagent-identity --query clientId -o tsv)
AZURE_TENANT_ID=$(az account show --query tenantId -o tsv)
```

#### Step 4: Deploy to AKS

```bash
# Create namespace
kubectl apply -f k8s/namespace-and-sa.yaml

# Create the shared API authentication secret used by the UI, orchestrator, and agents
scripts/ensure-api-auth.sh multiagent

# Deploy services with variable substitution
cat k8s/currency-mcp-deployment.yaml | \
  sed "s/\${ACR_NAME}/$ACR_NAME/g" | \
  kubectl apply -f -

cat k8s/activity-mcp-deployment.yaml | \
  sed "s/\${ACR_NAME}/$ACR_NAME/g" | \
  kubectl apply -f -

cat k8s/travel-agent-deployment.yaml | \
  sed "s/\${ACR_NAME}/$ACR_NAME/g" | \
  sed "s/\${OPENAI_NAME}/$OPENAI_NAME/g" | \
  sed "s/\${WORKLOAD_IDENTITY_CLIENT_ID}/$WORKLOAD_IDENTITY_CLIENT_ID/g" | \
  sed "s/\${AZURE_TENANT_ID}/$AZURE_TENANT_ID/g" | \
  kubectl apply -f -

kubectl apply -f k8s/network-policies.yaml
```

## Verify Deployment

### Check Pod Status

```bash
kubectl get pods -n multiagent
```

Expected output:
```
NAME                            READY   STATUS    RESTARTS   AGE
currency-mcp-xxxxx              1/1     Running   0          2m
currency-mcp-yyyyy              1/1     Running   0          2m
activity-mcp-xxxxx              1/1     Running   0          2m
activity-mcp-yyyyy              1/1     Running   0          2m
travel-agent-xxxxx              1/1     Running   0          2m
travel-agent-yyyyy              1/1     Running   0          2m
```

### Check Services

```bash
kubectl get services -n multiagent
```

Expected output:
```
NAME                     TYPE           CLUSTER-IP     EXTERNAL-IP     PORT(S)        AGE
currency-mcp-service     ClusterIP      10.0.x.x       <none>          8001/TCP       2m
activity-mcp-service     ClusterIP      10.0.x.x       <none>          8002/TCP       2m
travel-agent-service     ClusterIP      10.0.x.x       <none>          80/TCP         2m
```

### Access Services Securely

Services are internal `ClusterIP` services by default. Use `kubectl port-forward` for development, or expose the Streamlit UI through an authenticated ingress, Azure Application Gateway, or API Management. Do not expose the orchestrator or agent services directly to the public internet.

## Test the Deployment

Port-forward the travel agent for local testing:

```bash
kubectl port-forward -n multiagent service/travel-agent-service 8080:80
API_KEY=$(kubectl get secret multiagent-api-auth -n multiagent -o jsonpath='{.data.api-key}' | base64 -d)

# Test currency exchange
curl -X POST http://localhost:8080/task \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -H "X-User-ID: test-user" \
  -d '{"task": "What is the exchange rate from USD to EUR?"}'

# Test restaurant recommendations
curl -X POST http://localhost:8080/task \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -H "X-User-ID: test-user" \
  -d '{"task": "Recommend restaurants in Paris"}'

# Test itinerary planning with currency
curl -X POST http://localhost:8080/task \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -H "X-User-ID: test-user" \
  -d '{"task": "Plan a 2-day trip to Tokyo with 500 USD budget. How much is that in JPY?"}'
```

## View Logs

```bash
# Currency MCP logs
kubectl logs -l app=currency-mcp -n multiagent --tail=50

# Activity MCP logs
kubectl logs -l app=activity-mcp -n multiagent --tail=50

# Travel Agent logs
kubectl logs -l app=travel-agent -n multiagent --tail=50

# Follow logs in real-time
kubectl logs -l app=travel-agent -n multiagent -f
```

## Troubleshooting

### Pods not starting

```bash
kubectl describe pod -l app=travel-agent -n multiagent
```

### Image pull errors

Ensure ACR is attached to AKS:
```bash
az aks update -n $AKS_NAME -g $RESOURCE_GROUP --attach-acr $ACR_NAME
```

### Workload Identity issues

Check service account:
```bash
kubectl describe sa multiagent-sa -n multiagent
```

Check federated identity:
```bash
az identity federated-credential list \
  --identity-name multiagent-identity \
  --resource-group $RESOURCE_GROUP
```

### Azure OpenAI permission errors

Grant permissions to the managed identity:
```bash
IDENTITY_PRINCIPAL_ID=$(az identity show -g $RESOURCE_GROUP -n multiagent-identity --query principalId -o tsv)
OPENAI_RESOURCE_ID=$(az cognitiveservices account show -n $OPENAI_NAME -g $RESOURCE_GROUP --query id -o tsv)

az role assignment create \
  --assignee $IDENTITY_PRINCIPAL_ID \
  --role "Cognitive Services OpenAI User" \
  --scope $OPENAI_RESOURCE_ID
```

## Update Deployment

To update after code changes:

```bash
# Rebuild and push new images
./scripts/deploy-to-aks.sh

# Or manually rebuild specific service
docker build -t $ACR_NAME.azurecr.io/travel-agent:latest ./agents/travel_agent
docker push $ACR_NAME.azurecr.io/travel-agent:latest

# Restart pods to pull new image
kubectl rollout restart deployment/travel-agent -n multiagent
```

## Clean Up

To remove the deployment:

```bash
kubectl delete namespace multiagent
```

To remove all infrastructure:

```bash
az group delete --name multiagent-dev-rg --yes --no-wait
```
