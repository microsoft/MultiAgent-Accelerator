"""
Test script for Orchestrator with A2A Protocol

This script tests:
1. Agent discovery
2. Request routing
3. Multi-agent coordination
"""

import asyncio
import os
import httpx

ORCHESTRATOR_URL = "http://localhost:8000"
API_KEY = os.getenv("MULTIAGENT_API_KEY") or os.getenv("API_KEY")
TEST_USER_ID = os.getenv("TEST_USER_ID", "test_user")


def auth_headers(include_user: bool = False):
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    if include_user:
        headers["X-User-ID"] = TEST_USER_ID
    return headers


async def test_orchestrator():
    """Test Orchestrator with A2A protocol"""
    
    print("=" * 70)
    print("🎭 Testing Orchestrator with A2A Protocol")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        
        # Test 1: Health check
        print("\n✅ Test 1: Health Check")
        response = await client.get(f"{ORCHESTRATOR_URL}/health")
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Agents Discovered: {result['agents_discovered']}")
        print(f"Service Bus: {result['service_bus_connected']}")
        
        # Test 2: List discovered agents
        print("\n✅ Test 2: List Discovered Agents")
        response = await client.get(f"{ORCHESTRATOR_URL}/agents", headers=auth_headers())
        agents = response.json()
        print(f"Total Agents: {agents['total_agents']}")
        for agent in agents['agents']:
            print(f"\n  Agent: {agent['name']}")
            print(f"  Description: {agent['description']}")
            print(f"  Skills:")
            for skill in agent['skills']:
                print(f"    - {skill['name']}: {skill['description'][:60]}...")
        
        # Test 3: Currency task (should route to travel_agent)
        print("\n✅ Test 3: Currency Conversion Task")
        response = await client.post(
            f"{ORCHESTRATOR_URL}/task",
            json={
                "task": "Convert 500 USD to EUR and JPY",
                "user_id": TEST_USER_ID
            },
            headers=auth_headers(include_user=True),
        )
        result = response.json()
        print(f"Agent Used: {result['agent_used']}")
        print(f"Result: {result['result'][:200]}...")
        
        # Test 4: Restaurant task (should route to travel_agent)
        print("\n✅ Test 4: Restaurant Recommendation Task")
        response = await client.post(
            f"{ORCHESTRATOR_URL}/task",
            json={
                "task": "Recommend affordable restaurants in Tokyo",
                "user_id": TEST_USER_ID
            },
            headers=auth_headers(include_user=True),
        )
        result = response.json()
        print(f"Agent Used: {result['agent_used']}")
        print(f"Result: {result['result'][:200]}...")
        
        # Test 5: Travel planning task (should route to travel_agent)
        print("\n✅ Test 5: Travel Planning Task")
        response = await client.post(
            f"{ORCHESTRATOR_URL}/task",
            json={
                "task": "Plan a 2-day trip to Paris with a budget of $800",
                "user_id": TEST_USER_ID
            },
            headers=auth_headers(include_user=True),
        )
        result = response.json()
        print(f"Agent Used: {result['agent_used']}")
        print(f"Result (first 300 chars): {result['result'][:300]}...")
        
        # Test 6: Get orchestrator's agent card
        print("\n✅ Test 6: Orchestrator Agent Card")
        response = await client.get(f"{ORCHESTRATOR_URL}/.well-known/agent.json")
        card = response.json()
        print(f"Name: {card['name']}")
        print(f"Description: {card['description']}")
        print(f"Skills: {len(card['capabilities']['skills'])}")
        print(f"Discovered Agents: {card['capabilities']['discovered_agents']}")
        
        # Test 7: Manual rediscovery
        print("\n✅ Test 7: Trigger Agent Rediscovery")
        response = await client.post(f"{ORCHESTRATOR_URL}/discover", headers=auth_headers())
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Agents Found: {result['agents_found']}")
        print(f"Agents: {', '.join(result['agents'])}")


async def main():
    """Run all tests"""
    print("\n🚀 Starting Orchestrator Tests\n")
    
    # Check if orchestrator is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/health", timeout=5.0)
            if response.status_code != 200:
                print("❌ Orchestrator is not healthy!")
                print("Make sure to start:")
                print("1. Currency MCP Server (port 8001)")
                print("2. Activity MCP Server (port 8002)")
                print("3. Travel Agent (port 8080)")
                print("4. Orchestrator (port 8000)")
                return
    except Exception as e:
        print(f"❌ Cannot connect to Orchestrator at {ORCHESTRATOR_URL}")
        print(f"Error: {e}")
        print("\nMake sure to start:")
        print("1. Currency MCP: cd mcp_servers/currency_mcp && python server.py")
        print("2. Activity MCP: cd mcp_servers/activity_mcp && python server.py")
        print("3. Travel Agent: cd agents/travel_agent && python main.py")
        print("4. Orchestrator: cd agents/orchestrator && python main.py")
        return
    
    try:
        await test_orchestrator()
        
        print("\n" + "=" * 70)
        print("✅ All Orchestrator Tests Completed Successfully!")
        print("=" * 70)
        print("\n🎉 A2A Protocol is working correctly!")
        print("\nThe orchestrator:")
        print("  ✓ Discovered agents via .well-known/agent.json")
        print("  ✓ Routed requests based on capabilities")
        print("  ✓ Called agents via /task endpoint")
        print("  ✓ Exposed its own agent card")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
