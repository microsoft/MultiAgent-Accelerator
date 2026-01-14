// Main Bicep template for Multi-Agent System on AKS (Resource Group Scope)
targetScope = 'resourceGroup'

@description('The primary location for all resources')
param location string = resourceGroup().location

@description('Environment name (dev, staging, prod)')
@allowed([
  'dev'
  'staging'
  'prod'
])
param environment string = 'dev'

@description('Project name prefix')
param projectName string = 'multiagent'

@description('Tags to apply to all resources')
param tags object = {
  Environment: environment
  Project: 'MultiAgent-AKS-MAF'
  ManagedBy: 'Bicep'
}

// AKS Cluster
module aksModule 'modules/aks.bicep' = {
  name: 'aks-deployment'
  params: {
    location: location
    environment: environment
    projectName: projectName
    tags: tags
  }
}

// Azure Container Registry
module acrModule 'modules/acr.bicep' = {
  name: 'acr-deployment'
  params: {
    location: location
    environment: environment
    projectName: projectName
    tags: tags
  }
}

// Azure AI Foundry (AI Hub + Project + OpenAI)
module aiFoundryModule 'modules/ai-foundry.bicep' = {
  name: 'ai-foundry-deployment'
  params: {
    location: location
    environment: environment
    projectName: projectName
    tags: tags
  }
}

// Azure Service Bus (for A2A communication)
module serviceBusModule 'modules/service-bus.bicep' = {
  name: 'service-bus-deployment'
  params: {
    location: location
    environment: environment
    projectName: projectName
    tags: tags
  }
}

// Application Insights
module appInsightsModule 'modules/app-insights.bicep' = {
  name: 'app-insights-deployment'
  params: {
    location: location
    environment: environment
    projectName: projectName
    tags: tags
  }
}

// Key Vault
module keyVaultModule 'modules/key-vault.bicep' = {
  name: 'key-vault-deployment'
  params: {
    location: location
    environment: environment
    projectName: projectName
    tags: tags
    aksPrincipalId: aksModule.outputs.kubeletIdentityObjectId
  }
}

// ACR Pull Role Assignment for AKS
module acrRoleAssignment 'modules/role-assignments.bicep' = {
  name: 'acr-role-assignment'
  params: {
    principalId: aksModule.outputs.kubeletIdentityObjectId
    acrName: acrModule.outputs.acrName
  }
}

// Workload Identity for pods
module workloadIdentityModule 'modules/workload-identity.bicep' = {
  name: 'workload-identity-deployment'
  params: {
    location: location
    environment: environment
    projectName: projectName
    tags: tags
    aksOidcIssuerUrl: aksModule.outputs.oidcIssuerUrl
    k8sNamespace: 'multiagent'
    k8sServiceAccountName: 'multiagent-sa'
  }
}

// Grant Workload Identity access to OpenAI
module openAIRoleAssignment 'modules/openai-role-assignment.bicep' = {
  name: 'openai-role-assignment'
  params: {
    openAIName: aiFoundryModule.outputs.openAIName
    workloadIdentityPrincipalId: workloadIdentityModule.outputs.identityPrincipalId
  }
}

// Outputs
output resourceGroupName string = resourceGroup().name
output aksClusterName string = aksModule.outputs.aksClusterName
output acrLoginServer string = acrModule.outputs.acrLoginServer
output aiFoundryEndpoint string = aiFoundryModule.outputs.aiFoundryEndpoint
output openAIEndpoint string = aiFoundryModule.outputs.openAIEndpoint
output openAIName string = aiFoundryModule.outputs.openAIName
output serviceBusNamespace string = serviceBusModule.outputs.serviceBusNamespace
output appInsightsConnectionString string = appInsightsModule.outputs.connectionString
output keyVaultName string = keyVaultModule.outputs.keyVaultName
output workloadIdentityClientId string = workloadIdentityModule.outputs.identityClientId
output workloadIdentityName string = workloadIdentityModule.outputs.identityName
