// Azure AI Foundry Module
// Note: location parameter is kept for consistency but AI resources always deploy to East US for model availability
@description('Location parameter (not used - AI resources deploy to East US)')
param location string
param environment string
param projectName string
param tags object

var aiHubName = '${projectName}-${environment}-aihub'
var aiProjectName = '${projectName}-${environment}-aiproject'
// Storage account names: 3-24 chars, lowercase, numbers only, no hyphens
var storageAccountName = 'st${replace(projectName, '-', '')}${environment}ai'
// Force East US for Azure OpenAI model availability
var aiLocation = 'eastus'

// Storage Account for AI Foundry
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: aiLocation
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// Azure AI Hub (Workspace)
resource aiHub 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: aiHubName
  location: aiLocation
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: 'Multi-Agent AI Hub'
    description: 'AI Hub for Multi-Agent System'
    storageAccount: storageAccount.id
    publicNetworkAccess: 'Enabled'
  }
  kind: 'Hub'
}

// Azure AI Project
resource aiProject 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: aiProjectName
  location: aiLocation
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: 'Multi-Agent System Project'
    description: 'AI Project for orchestrating multiple agents'
    hubResourceId: aiHub.id
    publicNetworkAccess: 'Enabled'
  }
  kind: 'Project'
}

// Azure OpenAI Service (for GPT-4 and other models)
resource openAI 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: '${projectName}-${environment}-openai'
  location: aiLocation
  tags: tags
  sku: {
    name: 'S0'
  }
  kind: 'OpenAI'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: '${projectName}-${environment}-openai'
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

// GPT-4o Deployment (latest GPT-4 generation)
resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: openAI
  name: 'gpt-4o'
  sku: {
    name: 'Standard'
    capacity: 10
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-08-06'
    }
    raiPolicyName: 'Microsoft.Default'
  }
}

// GPT-4o-mini Deployment (faster, cost-effective)
resource gpt4oMiniDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: openAI
  name: 'gpt-4o-mini'
  sku: {
    name: 'Standard'
    capacity: 30
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o-mini'
      version: '2024-07-18'
    }
    raiPolicyName: 'Microsoft.Default'
  }
  dependsOn: [
    gpt4oDeployment
  ]
}

// GPT-3.5 Turbo Deployment (for faster, cheaper operations)
resource gpt35TurboDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  parent: openAI
  name: 'gpt-4.1-mini'
  sku: {
    name: 'Standard'
    capacity: 30
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4.1-mini'
      version: '2025-04-14'
    }
    raiPolicyName: 'Microsoft.Default'
  }
  dependsOn: [
    gpt4oMiniDeployment
  ]
}

output aiHubName string = aiHub.name
output aiProjectName string = aiProject.name
output aiFoundryEndpoint string = aiProject.properties.discoveryUrl
output openAIEndpoint string = openAI.properties.endpoint
output openAIName string = openAI.name
output openAIResourceId string = openAI.id
output storageAccountName string = storageAccount.name
