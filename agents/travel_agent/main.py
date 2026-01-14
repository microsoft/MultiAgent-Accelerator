"""
Travel Agent - MAF Agent with Currency and Activity MCP Tools

This agent provides comprehensive travel planning capabilities by integrating:
- Currency MCP Server: Exchange rates and currency conversion
- Activity MCP Server: Itinerary planning, restaurant suggestions, attractions

Architecture:
- Uses ChatAgent from Microsoft Agent Framework
- Connects to MCP servers via MCPStreamableHTTPTool
- Exposes A2A protocol endpoints for discoverability
- Can be called by Orchestrator or other agents
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agent_framework import ChatAgent, MCPStreamableHTTPTool
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import DefaultAzureCredential, AzureCliCredential

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
CURRENCY_MCP_URL = os.getenv("CURRENCY_MCP_URL", "http://localhost:8001")
ACTIVITY_MCP_URL = os.getenv("ACTIVITY_MCP_URL", "http://localhost:8002")
AGENT_PORT = int(os.getenv("PORT", "8080"))

# Global agent instance
travel_agent: Optional[ChatAgent] = None


def get_azure_credential():
    """Get Azure credential for authentication"""
    try:
        # Try DefaultAzureCredential first (works with Managed Identity in production)
        credential = DefaultAzureCredential()
        # Test the credential
        credential.get_token("https://cognitiveservices.azure.com/.default")
        logger.info("Using DefaultAzureCredential (Managed Identity)")
        return credential
    except Exception as e:
        logger.warning(f"DefaultAzureCredential failed: {e}, falling back to AzureCliCredential")
        # Fallback to Azure CLI credential for local development
        return AzureCliCredential()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize agent on startup"""
    global travel_agent
    
    logger.info("🚀 Starting Travel Agent...")
    logger.info(f"Azure OpenAI Endpoint: {AZURE_OPENAI_ENDPOINT}")
    logger.info(f"Deployment: {AZURE_OPENAI_DEPLOYMENT}")
    logger.info(f"Currency MCP: {CURRENCY_MCP_URL}")
    logger.info(f"Activity MCP: {ACTIVITY_MCP_URL}")
    
    try:
        # Get Azure credential
        credential = get_azure_credential()
        
        # Create Azure OpenAI Chat Client
        chat_client = AzureOpenAIChatClient(
            endpoint=AZURE_OPENAI_ENDPOINT,
            credential=credential,
            deployment_name=AZURE_OPENAI_DEPLOYMENT
        )
        
        # Initialize MCP tools - FastMCP StreamableHTTP serves at /mcp endpoint
        # Note: Connection is established lazily on first use
        currency_tool = MCPStreamableHTTPTool(
            url=f"{CURRENCY_MCP_URL}/mcp",
            name="currency_tools",
            description="Currency exchange tools for getting rates and converting money",
            sse_read_timeout=300.0  # 5 minutes timeout for Kubernetes environment
        )
        
        activity_tool = MCPStreamableHTTPTool(
            url=f"{ACTIVITY_MCP_URL}/mcp",
            name="activity_tools",
            description="Travel activity tools for planning itineraries, finding restaurants and attractions",
            sse_read_timeout=300.0  # 5 minutes timeout for Kubernetes environment
        )
        
        # Create ChatAgent with instructions
        travel_agent = ChatAgent(
            chat_client=chat_client,
            tools=[currency_tool, activity_tool],
            instructions="""You are a helpful Travel Planning Assistant with access to specialized tools.

Your capabilities:
1. **Currency Tools** (currency_tools):
   - Get exchange rates between currencies
   - Convert amounts from one currency to another
   - List supported currencies
   
2. **Activity Tools** (activity_tools):
   - Create complete multi-day itineraries
   - Suggest restaurants based on budget and cuisine preferences
   - Find tourist attractions and activities
   - Plan detailed day trips with timing and costs

Guidelines:
- Always be helpful, friendly, and provide detailed travel advice
- When asked about costs or prices, use currency tools to provide conversions
- When planning trips, create comprehensive itineraries with activities and restaurants
- Consider the user's budget and preferences when making recommendations
- Provide practical information like opening hours, typical costs, and time needed
- If you don't have information about a specific location, be honest about it
- Use the sample data available (Paris, Tokyo, Rome) to demonstrate capabilities

Example interactions:
- "Plan a 3-day trip to Paris with a budget of $1000" → Use activity_tools to create itinerary
- "How much is 500 USD in EUR?" → Use currency_tools to convert
- "What are the best restaurants in Tokyo?" → Use activity_tools to suggest restaurants
- "Create a day trip in Rome starting at 9 AM" → Use activity_tools to plan the day

Always provide specific, actionable recommendations with details.
"""
        )
        
        logger.info("✅ Travel Agent initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Travel Agent: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down Travel Agent...")


# FastAPI app
app = FastAPI(
    title="Travel Agent",
    description="MAF-based Travel Planning Agent with Currency and Activity tools",
    version="1.0.0",
    lifespan=lifespan
)


class TaskRequest(BaseModel):
    """Request model for task execution"""
    task: str
    user_id: Optional[str] = "anonymous"


class TaskResponse(BaseModel):
    """Response model for task execution"""
    result: str
    agent: str = "travel_agent"


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "agent": "travel_agent",
        "status": "running",
        "capabilities": ["travel_planning", "currency_exchange", "itinerary_creation"],
        "mcp_tools": ["currency_tools", "activity_tools"]
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    if travel_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return {"status": "healthy"}


@app.post("/task", response_model=TaskResponse)
async def execute_task(request: TaskRequest):
    """
    Execute a travel planning task
    
    Example requests:
    - "Plan a 2-day trip to Paris"
    - "Convert 500 USD to EUR"
    - "What restaurants do you recommend in Tokyo?"
    - "Create an itinerary for Rome with a budget of $800"
    """
    if travel_agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    logger.info(f"📝 Task from {request.user_id}: {request.task}")
    
    try:
        # Execute task with the agent
        result = await travel_agent.run(request.task)
        
        # Extract the response text
        response_text = result.response if hasattr(result, 'response') else str(result)
        
        logger.info(f"✅ Task completed for {request.user_id}")
        
        return TaskResponse(
            result=response_text,
            agent="travel_agent"
        )
        
    except Exception as e:
        logger.error(f"❌ Error executing task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error executing task: {str(e)}")


@app.get("/.well-known/agent.json")
async def agent_card():
    """
    A2A Protocol: Agent Card endpoint
    
    This endpoint exposes the agent's capabilities for discovery by other agents
    and the orchestrator.
    """
    return JSONResponse({
        "name": "travel_agent",
        "description": "Specialized travel planning agent with currency exchange and activity planning capabilities",
        "version": "1.0.0",
        "capabilities": {
            "skills": [
                {
                    "id": "travel_planning",
                    "name": "Travel Planning",
                    "description": "Create comprehensive travel itineraries with activities, restaurants, and attractions",
                    "examples": [
                        "Plan a 3-day trip to Paris",
                        "Create an itinerary for Tokyo with a budget of $1500",
                        "Suggest a day trip in Rome starting at 9 AM"
                    ]
                },
                {
                    "id": "currency_exchange",
                    "name": "Currency Exchange",
                    "description": "Get real-time exchange rates and convert between 30+ currencies",
                    "examples": [
                        "What's the exchange rate from USD to EUR?",
                        "Convert 500 USD to JPY",
                        "What currencies are supported?"
                    ]
                },
                {
                    "id": "restaurant_recommendations",
                    "name": "Restaurant Recommendations",
                    "description": "Suggest restaurants based on location, budget, and cuisine preferences",
                    "examples": [
                        "Recommend restaurants in Paris",
                        "Find affordable dining options in Tokyo",
                        "What are the best restaurants in Rome?"
                    ]
                },
                {
                    "id": "attraction_discovery",
                    "name": "Attraction Discovery",
                    "description": "Find tourist attractions, museums, landmarks, and activities",
                    "examples": [
                        "What are the top attractions in Paris?",
                        "Find cultural activities in Tokyo",
                        "List must-see sights in Rome"
                    ]
                }
            ],
            "supported_locations": ["Paris", "Tokyo", "Rome"],
            "mcp_tools": ["currency_tools", "activity_tools"]
        },
        "endpoints": {
            "task": {
                "url": "/task",
                "method": "POST",
                "description": "Execute a travel planning task",
                "request_schema": {
                    "task": "string (required) - The travel planning task to execute",
                    "user_id": "string (optional) - User identifier"
                }
            },
            "health": {
                "url": "/health",
                "method": "GET",
                "description": "Health check endpoint"
            }
        },
        "protocol": "a2a",
        "contact": {
            "author": "MAF Team",
            "repository": "https://github.com/darkanita/MultiAgent-AKS-MAF"
        }
    })


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"🌍 Starting Travel Agent on port {AGENT_PORT}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=AGENT_PORT,
        log_level="info"
    )
