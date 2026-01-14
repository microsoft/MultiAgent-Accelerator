// OpenAI Role Assignment Module
param openAIName string
param workloadIdentityPrincipalId string

// Reference existing OpenAI resource
resource openAI 'Microsoft.CognitiveServices/accounts@2023-10-01-preview' existing = {
  name: openAIName
}

// Assign Cognitive Services OpenAI User role to Workload Identity
resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAI.id, workloadIdentityPrincipalId, 'Cognitive Services OpenAI User')
  scope: openAI
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd') // Cognitive Services OpenAI User
    principalId: workloadIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output roleAssignmentId string = roleAssignment.id
