#!/bin/bash
# Workaround: Create .env file for local A2A testing (without Key Vault)
# Use this if you can't set Key Vault permissions

echo "========================================="
echo "A2A Testing - Alternative Secrets Setup"
echo "========================================="
echo ""
echo "⚠️  This creates a .env file for LOCAL testing only"
echo "    For AKS deployment, Key Vault permissions are still needed"
echo ""

# Configuration
RESOURCE_GROUP="multiagent-github-test-rg"
OPENAI_NAME="multiagent-test-dev-openai"
SERVICEBUS_NS="multiagent-test-dev-servicebus"

# Get OpenAI credentials
echo "Getting OpenAI credentials..."
OPENAI_ENDPOINT=$(az cognitiveservices account show \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.endpoint \
  --output tsv)

OPENAI_KEY=$(az cognitiveservices account keys list \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --query key1 \
  --output tsv)

echo "✅ OpenAI Endpoint: $OPENAI_ENDPOINT"

# Get Service Bus connection string
echo "Getting Service Bus connection string..."
SERVICEBUS_CONN=$(az servicebus namespace authorization-rule keys list \
  --namespace-name $SERVICEBUS_NS \
  --resource-group $RESOURCE_GROUP \
  --name RootManageSharedAccessKey \
  --query primaryConnectionString \
  --output tsv)

echo "✅ Service Bus connection retrieved"

# Create .env file
echo ""
echo "Creating .env file for LOCAL testing..."
cat > .env << EOF
# Local A2A Testing Environment Variables
# ⚠️ DO NOT COMMIT THIS FILE - Contains sensitive credentials!

KEYVAULT_URL=https://multiagent-test-dev-kv.vault.azure.net/
SERVICEBUS_NAMESPACE=$SERVICEBUS_NS.servicebus.windows.net
USE_MANAGED_IDENTITY=false

# Direct credentials (for local testing only)
OPENAI_ENDPOINT=$OPENAI_ENDPOINT
OPENAI_API_KEY=$OPENAI_KEY
SERVICEBUS_CONNECTION_STRING=$SERVICEBUS_CONN
EOF

echo "✅ Created .env file"
echo ""
echo "========================================="
echo "✅ Local Testing Setup Complete!"
echo "========================================="
echo ""
echo "You can now test A2A locally:"
echo ""
echo "  1. Test Service Bus connection:"
echo "     cd agents/data_agent"
echo "     pip install azure-servicebus python-dotenv azure-identity openai"
echo "     python -c 'from dotenv import load_dotenv; load_dotenv(); print(\"Loaded!\")'"
echo ""
echo "  2. For AKS deployment, you'll need to:"
echo "     - Contact your Azure admin to grant Key Vault permissions"
echo "     - Or use Azure Portal to manually add secrets to Key Vault"
echo ""
echo "⚠️  IMPORTANT: The .env file is in .gitignore - don't commit it!"
echo ""
