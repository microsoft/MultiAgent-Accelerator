// Workload Identity Module
param location string
param environment string
param projectName string
param tags object

@description('AKS OIDC Issuer URL')
param aksOidcIssuerUrl string

@description('Kubernetes namespace')
param k8sNamespace string = 'multiagent'

@description('Kubernetes service account name')
param k8sServiceAccountName string = 'multiagent-sa'

// Create User-Assigned Managed Identity
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${projectName}-${environment}-identity'
  location: location
  tags: tags
}

// Create Federated Identity Credential
resource federatedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = {
  name: 'kubernetes-federated-identity'
  parent: managedIdentity
  properties: {
    audiences: [
      'api://AzureADTokenExchange'
    ]
    issuer: aksOidcIssuerUrl
    subject: 'system:serviceaccount:${k8sNamespace}:${k8sServiceAccountName}'
  }
}

output identityName string = managedIdentity.name
output identityClientId string = managedIdentity.properties.clientId
output identityPrincipalId string = managedIdentity.properties.principalId
output identityResourceId string = managedIdentity.id
