"""
Orchestrator Agent - A2A Protocol Implementation

This orchestrator discovers and coordinates multiple specialized agents using the
Agent-to-Agent (A2A) protocol. It handles:

1. Agent Discovery: Discovers agents via their .well-known/agent.json endpoints
2. Request Routing: Routes user requests to appropriate specialized agents
3. Service Bus Integration: Supports async communication via Azure Service Bus
4. Multi-Agent Coordination: Combines responses from multiple agents when needed

Architecture:
- Discovers Travel Agent (and other agents) dynamically
- Uses A2A protocol for agent metadata exchange
- Supports both sync (HTTP) and async (Service Bus) communication
"""

import os
import logging
import asyncio
from typing import Optional, Dict, List, Any
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx

from azure.identity.aio import DefaultAzureCredential, AzureCliCredential
from azure.servicebus.aio import ServiceBusClient, ServiceBusReceiver, ServiceBusSender
from azure.servicebus import ServiceBusMessage

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
SERVICEBUS_NAMESPACE = os.getenv("SERVICEBUS_NAMESPACE", "")
USE_MANAGED_IDENTITY = os.getenv("USE_MANAGED_IDENTITY", "true").lower() == "true"
ORCHESTRATOR_PORT = int(os.getenv("PORT", "8000"))

# Agent discovery endpoints (can be configured via environment)
AGENT_ENDPOINTS = os.getenv(
    "AGENT_ENDPOINTS",
    "http://travel-agent-service/.well-known/agent.json"
).split(",")

# Global state
discovered_agents: Dict[str, Dict[str, Any]] = {}
service_bus_client: Optional[ServiceBusClient] = None
queue_processor_task: Optional[asyncio.Task] = None


async def process_queue_messages():
    """Background task to process messages from Service Bus queue"""
    if not service_bus_client:
        logger.warning("Service Bus not available, queue processor not started")
        return
    
    logger.info("🎯 Starting queue message processor...")
    
    try:
        async with service_bus_client.get_queue_receiver(
            queue_name="agent-tasks",
            max_wait_time=5
        ) as receiver:
            while True:
                try:
                    # Receive messages
                    received_msgs = await receiver.receive_messages(max_message_count=10, max_wait_time=5)
                    
                    for msg in received_msgs:
                        try:
                            task = str(msg)
                            user_id = msg.application_properties.get("user_id", "anonymous")
                            preferred_agent = msg.application_properties.get("preferred_agent")
                            
                            logger.info(f"📨 Processing queued task from {user_id}: {task}")
                            
                            # Select and call agent
                            selected_agent = select_best_agent(task, preferred_agent)
                            if selected_agent:
                                result = await call_agent(selected_agent, task, user_id)
                                
                                # Send result to response queue
                                async with service_bus_client.get_queue_sender(queue_name="agent-responses") as sender:
                                    response_msg = ServiceBusMessage(
                                        body=result,
                                        application_properties={
                                            "user_id": user_id,
                                            "agent_used": selected_agent,
                                            "original_task": task
                                        }
                                    )
                                    await sender.send_messages(response_msg)
                                
                                logger.info(f"✅ Task completed and response queued")
                            
                            # Complete the message
                            await receiver.complete_message(msg)
                            
                        except Exception as e:
                            logger.error(f"❌ Error processing message: {e}", exc_info=True)
                            # Dead-letter the message if processing fails
                            await receiver.dead_letter_message(msg, reason="ProcessingError", error_description=str(e))
                    
                    # Small delay between batches
                    await asyncio.sleep(1)
                    
                except asyncio.CancelledError:
                    logger.info("Queue processor cancelled")
                    break
                except Exception as e:
                    logger.error(f"❌ Error in queue processor: {e}", exc_info=True)
                    await asyncio.sleep(5)
                    
    except Exception as e:
        logger.error(f"❌ Fatal error in queue processor: {e}", exc_info=True)


class TaskRequest(BaseModel):
    """Request model for orchestrator tasks"""
    task: str
    user_id: Optional[str] = "anonymous"
    preferred_agent: Optional[str] = None


class TaskResponse(BaseModel):
    """Response model for orchestrator tasks"""
    result: str
    agent_used: str
    orchestrator: str = "orchestrator"


def get_azure_credential():
    """Get Azure credential for authentication"""
    if not USE_MANAGED_IDENTITY:
        logger.info("Using AzureCliCredential for local development")
        return AzureCliCredential()
    
    logger.info("Using DefaultAzureCredential (Managed Identity)")
    return DefaultAzureCredential()


async def discover_agent(endpoint_url: str) -> Optional[Dict[str, Any]]:
    """
    Discover an agent by fetching its agent card from .well-known/agent.json
    
    Args:
        endpoint_url: URL to the agent's card endpoint
        
    Returns:
        Agent metadata dictionary or None if discovery fails
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(endpoint_url)
            response.raise_for_status()
            agent_card = response.json()
            
            # Handle both A2A and ADK formats
            # A2A: capabilities.skills
            # ADK: skills (at root level)
            skills = agent_card.get('skills', []) or agent_card.get('capabilities', {}).get('skills', [])
            
            logger.info(f"✅ Discovered agent: {agent_card.get('name', 'unknown')}")
            logger.info(f"   Description: {agent_card.get('description', 'N/A')}")
            logger.info(f"   Protocol: {agent_card.get('protocolVersion', 'A2A')}")
            logger.info(f"   Skills: {len(skills)}")
            
            return agent_card
            
    except Exception as e:
        logger.error(f"❌ Failed to discover agent at {endpoint_url}: {e}")
        return None


async def discover_all_agents():
    """Discover all configured agents"""
    global discovered_agents
    
    logger.info("🔍 Starting agent discovery...")
    
    for endpoint in AGENT_ENDPOINTS:
        endpoint = endpoint.strip()
        if not endpoint:
            continue
            
        agent_card = await discover_agent(endpoint)
        if agent_card:
            agent_name = agent_card.get("name", "unknown")
            # Store both the agent card and its base URL
            agent_card["_discovery_url"] = endpoint
            agent_card["_base_url"] = endpoint.replace("/.well-known/agent.json", "")
            discovered_agents[agent_name] = agent_card
    
    logger.info(f"✅ Discovery complete. Found {len(discovered_agents)} agents:")
    for agent_name in discovered_agents.keys():
        logger.info(f"   - {agent_name}")


def select_best_agent(task: str, preferred_agent: Optional[str] = None) -> Optional[str]:
    """
    Select the best agent for a given task based on agent capabilities
    
    Args:
        task: The task description
        preferred_agent: Optional preferred agent name
        
    Returns:
        Agent name or None if no suitable agent found
    """
    if preferred_agent and preferred_agent in discovered_agents:
        logger.info(f"Using preferred agent: {preferred_agent}")
        return preferred_agent
    
    # Simple keyword matching for demo
    # In production, use LLM-based routing or semantic similarity
    task_lower = task.lower()
    
    for agent_name, agent_card in discovered_agents.items():
        # Get agent metadata for matching
        agent_description = agent_card.get("description", "").lower()
        agent_name_lower = agent_name.lower()
        capabilities = agent_card.get("capabilities", {})
        skills = capabilities.get("skills", [])
        
        # Match by keywords - Burger Orders (check agent name and description first)
        if any(keyword in task_lower for keyword in ["burger", "cheeseburger", "hamburger"]):
            if "burger" in agent_name_lower or "burger" in agent_description:
                logger.info(f"Selected {agent_name} based on burger keyword in name/description")
                return agent_name
        
        # Match by keywords - Pizza Orders (check agent name and description first)
        if any(keyword in task_lower for keyword in ["pizza", "pizzas", "margherita", "pepperoni"]):
            if "pizza" in agent_name_lower or "pizza" in agent_description:
                logger.info(f"Selected {agent_name} based on pizza keyword in name/description")
                return agent_name
        
        # Match by keywords - Illustration agent (check name and description too)
        if any(keyword in task_lower for keyword in ["illustration", "illustrate", "draw", "image", "picture", "visual", "graphic"]):
            if "illustrat" in agent_name_lower or "illustrat" in agent_description:
                logger.info(f"Selected {agent_name} based on illustration keyword in name/description")
                return agent_name
        
        # Check if task matches agent skills
        for skill in skills:
            skill_name = skill.get("name", "").lower()
            skill_desc = skill.get("description", "").lower()
            examples = skill.get("examples", [])
            
            # Match by keywords - Illustration agent (in skills)
            if any(keyword in task_lower for keyword in ["illustration", "illustrate", "draw", "image", "picture", "visual", "graphic"]):
                if "illustrat" in skill_name or "illustrat" in skill_desc:
                    logger.info(f"Selected {agent_name} based on illustration skill match")
                    return agent_name
            
            # Match by keywords - Currency/Exchange
            if any(keyword in task_lower for keyword in ["currency", "exchange", "convert"]):
                if "currency" in skill_name or "currency" in skill_desc:
                    logger.info(f"Selected {agent_name} based on currency skill match")
                    return agent_name
            
            # Match by keywords - Travel/Activity
            if any(keyword in task_lower for keyword in ["restaurant", "attraction", "itinerary", "trip", "plan"]):
                if "travel" in skill_name or "restaurant" in skill_name or "attraction" in skill_name:
                    logger.info(f"Selected {agent_name} based on travel/activity skill match")
                    return agent_name
            
            # Match by keywords - Burger Orders
            if any(keyword in task_lower for keyword in ["burger", "cheeseburger", "hamburger"]):
                if "burger" in skill_name or "burger" in skill_desc or "burger" in agent_name.lower():
                    logger.info(f"Selected {agent_name} based on burger order skill match")
                    return agent_name
            
            # Match by keywords - Pizza Orders
            if any(keyword in task_lower for keyword in ["pizza", "pizzas", "margherita", "pepperoni"]):
                if "pizza" in skill_name or "pizza" in skill_desc or "pizza" in agent_name.lower():
                    logger.info(f"Selected {agent_name} based on pizza order skill match")
                    return agent_name
    
    # Default to first available agent if no specific match
    if discovered_agents:
        default_agent = list(discovered_agents.keys())[0]
        logger.info(f"No specific match found, using default agent: {default_agent}")
        return default_agent
    
    logger.warning("No agents available")
    return None


async def call_agent(agent_name: str, task: str, user_id: str) -> str:
    """
    Call a specific agent to execute a task
    
    Args:
        agent_name: Name of the agent to call
        task: Task description
        user_id: User identifier
        
    Returns:
        Agent response as string
    """
    if agent_name not in discovered_agents:
        raise ValueError(f"Agent '{agent_name}' not found")
    
    agent_card = discovered_agents[agent_name]
    
    # IMPORTANT: Always use the discovery URL (_base_url) instead of agent card's "url" field
    # The agent card's "url" field may contain localhost addresses (like 0.0.0.0:8000)
    # which are not accessible from external callers
    agent_base_url = agent_card.get("_base_url")
    if not agent_base_url:
        raise ValueError(f"No base URL stored for agent '{agent_name}'")
    
    logger.info(f"Using discovery base URL: {agent_base_url}")
    
    # Construct task URL
    # For GCP agents: base_url already includes the full path (e.g., /a2a/illustration_agent)
    # For AKS agents: base_url is just the service URL (e.g., http://travel-agent-service)
    # Try /task endpoint (standard for both)
    task_url = f"{agent_base_url}/task"
    
    logger.info(f"📞 Calling {agent_name} at {task_url}")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                task_url,
                json={"task": task, "user_id": user_id}
            )
            response.raise_for_status()
            result = response.json()
            
            return result.get("result", str(result))
            
    except Exception as e:
        logger.error(f"❌ Error calling {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to call agent: {str(e)}")


async def setup_service_bus():
    """Setup Azure Service Bus client for async communication"""
    global service_bus_client
    
    if not SERVICEBUS_NAMESPACE:
        logger.warning("⚠️  Service Bus namespace not configured, skipping setup")
        return
    
    try:
        credential = get_azure_credential()
        fully_qualified_namespace = f"{SERVICEBUS_NAMESPACE}"
        
        service_bus_client = ServiceBusClient(
            fully_qualified_namespace=fully_qualified_namespace,
            credential=credential
        )
        
        logger.info(f"✅ Connected to Service Bus: {fully_qualified_namespace}")
        
    except Exception as e:
        logger.error(f"❌ Failed to setup Service Bus: {e}")
        service_bus_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize on startup"""
    global queue_processor_task
    
    logger.info("🚀 Starting Orchestrator Agent...")
    
    # Discover agents
    await discover_all_agents()
    
    # Setup Service Bus
    await setup_service_bus()
    
    # Start queue processor if Service Bus is available
    if service_bus_client:
        queue_processor_task = asyncio.create_task(process_queue_messages())
        logger.info("✅ Queue processor started")
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down Orchestrator Agent...")
    if queue_processor_task:
        queue_processor_task.cancel()
        try:
            await queue_processor_task
        except asyncio.CancelledError:
            pass
    
    if service_bus_client:
        await service_bus_client.close()


# FastAPI app
app = FastAPI(
    title="Orchestrator Agent",
    description="A2A Protocol Orchestrator for Multi-Agent System",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "agent": "orchestrator",
        "status": "running",
        "protocol": "a2a",
        "discovered_agents": list(discovered_agents.keys()),
        "capabilities": ["agent_discovery", "request_routing", "multi_agent_coordination"]
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agents_discovered": len(discovered_agents),
        "service_bus_connected": service_bus_client is not None
    }


@app.get("/agents")
async def list_agents():
    """List all discovered agents and their capabilities"""
    agents_info = []
    
    for agent_name, agent_card in discovered_agents.items():
        agents_info.append({
            "name": agent_name,
            "description": agent_card.get("description", ""),
            "skills": [
                {
                    "name": skill.get("name"),
                    "description": skill.get("description")
                }
                for skill in agent_card.get("capabilities", {}).get("skills", [])
            ]
        })
    
    return {
        "total_agents": len(agents_info),
        "agents": agents_info
    }


@app.post("/task", response_model=TaskResponse)
async def execute_task(request: TaskRequest):
    """
    Execute a task by routing it to the appropriate agent
    
    This endpoint:
    1. Analyzes the task
    2. Selects the best agent based on capabilities
    3. Routes the request to that agent
    4. Returns the result
    """
    logger.info(f"📝 New task from {request.user_id}: {request.task}")
    
    if not discovered_agents:
        raise HTTPException(
            status_code=503,
            detail="No agents available. Agent discovery may have failed."
        )
    
    # Select best agent for the task
    selected_agent = select_best_agent(request.task, request.preferred_agent)
    
    if not selected_agent:
        raise HTTPException(
            status_code=404,
            detail="No suitable agent found for this task"
        )
    
    # Call the selected agent
    try:
        result = await call_agent(selected_agent, request.task, request.user_id)
        
        logger.info(f"✅ Task completed by {selected_agent}")
        
        return TaskResponse(
            result=result,
            agent_used=selected_agent,
            orchestrator="orchestrator"
        )
        
    except Exception as e:
        logger.error(f"❌ Error executing task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/task/async")
async def execute_task_async(request: TaskRequest):
    """
    Queue a task for async processing via Service Bus
    
    This endpoint:
    1. Validates the task
    2. Sends it to Service Bus queue
    3. Returns immediately with message ID
    """
    if not service_bus_client:
        raise HTTPException(
            status_code=503,
            detail="Service Bus not available. Use /task for synchronous execution."
        )
    
    logger.info(f"📬 Queueing task from {request.user_id}: {request.task}")
    
    try:
        # Send message to Service Bus queue
        async with service_bus_client.get_queue_sender(queue_name="agent-tasks") as sender:
            message = ServiceBusMessage(
                body=request.task,
                application_properties={
                    "user_id": request.user_id,
                    "preferred_agent": request.preferred_agent or ""
                }
            )
            await sender.send_messages(message)
            message_id = message.message_id
        
        logger.info(f"✅ Task queued successfully: {message_id}")
        
        return {
            "status": "queued",
            "message_id": message_id,
            "queue": "agent-tasks",
            "message": "Task queued for async processing"
        }
        
    except Exception as e:
        logger.error(f"❌ Error queuing task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")


@app.post("/discover")
async def trigger_discovery():
    """Manually trigger agent discovery"""
    await discover_all_agents()
    return {
        "status": "discovery_complete",
        "agents_found": len(discovered_agents),
        "agents": list(discovered_agents.keys())
    }


@app.get("/responses/{user_id}")
async def get_responses(user_id: str, max_messages: int = 10):
    """
    Fetch async responses for a specific user from Service Bus queue
    
    This endpoint:
    1. Connects to the agent-responses queue
    2. Peeks at messages (without removing them)
    3. Filters by user_id
    4. Returns the responses
    """
    if not service_bus_client:
        raise HTTPException(
            status_code=503,
            detail="Service Bus not available"
        )
    
    try:
        responses = []
        
        async with service_bus_client.get_queue_receiver(
            queue_name="agent-responses",
            max_wait_time=5
        ) as receiver:
            # Receive messages (peek and delete)
            async for message in receiver:
                try:
                    # Get message body
                    body = str(message)
                    
                    # Get properties
                    props = message.application_properties or {}
                    msg_user_id = props.get("user_id", "unknown")
                    
                    # Filter by user_id if it matches or include all if no filter
                    if user_id == "all" or msg_user_id == user_id:
                        responses.append({
                            "user_id": msg_user_id,
                            "response": body,
                            "agent_used": props.get("agent_used", "unknown"),
                            "timestamp": str(message.enqueued_time_utc) if message.enqueued_time_utc else "N/A",
                            "message_id": message.message_id
                        })
                    
                    # Complete the message (remove from queue)
                    await receiver.complete_message(message)
                    
                    if len(responses) >= max_messages:
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await receiver.abandon_message(message)
                    continue
        
        return {
            "total": len(responses),
            "user_id": user_id,
            "responses": responses
        }
        
    except Exception as e:
        logger.error(f"Error fetching responses: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch responses: {str(e)}")


@app.get("/.well-known/agent.json")
async def agent_card():
    """
    A2A Protocol: Orchestrator's Agent Card
    
    The orchestrator exposes its own agent card for discovery by other systems
    """
    return JSONResponse({
        "name": "orchestrator",
        "description": "Multi-agent orchestrator that discovers and coordinates specialized agents using A2A protocol",
        "version": "1.0.0",
        "capabilities": {
            "skills": [
                {
                    "id": "agent_discovery",
                    "name": "Agent Discovery",
                    "description": "Discover available agents via A2A protocol and their capabilities",
                    "examples": [
                        "List available agents",
                        "What agents are available?",
                        "Show me agent capabilities"
                    ]
                },
                {
                    "id": "request_routing",
                    "name": "Request Routing",
                    "description": "Route user requests to the most appropriate specialized agent",
                    "examples": [
                        "Plan a trip to Paris",
                        "Convert 500 USD to EUR",
                        "Find restaurants in Tokyo"
                    ]
                },
                {
                    "id": "multi_agent_coordination",
                    "name": "Multi-Agent Coordination",
                    "description": "Coordinate multiple agents to fulfill complex requests",
                    "examples": [
                        "Plan a trip with budget conversion",
                        "Create itinerary with currency exchange"
                    ]
                }
            ],
            "protocols": ["a2a", "http", "servicebus"],
            "discovered_agents": list(discovered_agents.keys())
        },
        "endpoints": {
            "task": {
                "url": "/task",
                "method": "POST",
                "description": "Execute a task by routing to appropriate agent"
            },
            "agents": {
                "url": "/agents",
                "method": "GET",
                "description": "List all discovered agents"
            },
            "discover": {
                "url": "/discover",
                "method": "POST",
                "description": "Trigger agent discovery"
            },
            "health": {
                "url": "/health",
                "method": "GET",
                "description": "Health check"
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
    
    logger.info(f"🌐 Starting Orchestrator on port {ORCHESTRATOR_PORT}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=ORCHESTRATOR_PORT,
        log_level="info"
    )
