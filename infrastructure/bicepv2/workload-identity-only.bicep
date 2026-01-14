// Workload Identity Only Deployment
targetScope = 'resourceGroup'

@description('The primary location for all resources')
param location string = resourceGroup().location

@description('Environment name (dev, staging, prod)')
param environment string = 'dev'

@description('Project name prefix')
param projectName string = 'multiagent'

@description('Tags to apply to all resources')
param tags object = {
  Environment: environment
  Project: 'MultiAgent-AKS-MAF'
  ManagedBy: 'Bicep'
}

// Get reference to existing AKS cluster
resource aks 'Microsoft.ContainerService/managedClusters@2024-02-01' existing = {
  name: '${projectName}-${environment}-aks'
}

// Get reference to existing OpenAI resource
resource openAI 'Microsoft.CognitiveServices/accounts@2023-10-01-preview' existing = {
  name: '${projectName}-${environment}-openai'
}

// Create Workload Identity
module workloadIdentityModule 'modules/workload-identity.bicep' = {
  name: 'workload-identity-deployment'
  params: {
    location: location
    environment: environment
    projectName: projectName
    tags: tags
    aksOidcIssuerUrl: aks.properties.oidcIssuerProfile.issuerURL
    k8sNamespace: 'multiagent'
    k8sServiceAccountName: 'multiagent-sa'
  }
}

// Grant Workload Identity access to OpenAI
module openAIRoleAssignment 'modules/openai-role-assignment.bicep' = {
  name: 'openai-role-assignment'
  params: {
    openAIName: openAI.name
    workloadIdentityPrincipalId: workloadIdentityModule.outputs.identityPrincipalId
  }
}

// Outputs
output workloadIdentityName string = workloadIdentityModule.outputs.identityName
output workloadIdentityClientId string = workloadIdentityModule.outputs.identityClientId
output workloadIdentityPrincipalId string = workloadIdentityModule.outputs.identityPrincipalId
