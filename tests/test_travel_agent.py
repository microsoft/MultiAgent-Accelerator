"""
Test script for Travel Agent with MCP tools

This script tests the Travel Agent by making various travel planning requests.
It requires the MCP servers and Travel Agent to be running.
"""

import asyncio
import httpx
import json


TRAVEL_AGENT_URL = "http://localhost:8080"


async def test_travel_agent():
    """Test Travel Agent with various requests"""
    
    print("=" * 70)
    print("🌍 Testing Travel Agent with MCP Tools")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=180.0) as client:  # 3 minutes timeout
        
        # Test 1: Health check
        print("\n✅ Test 1: Health Check")
        response = await client.get(f"{TRAVEL_AGENT_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test 2: Get Agent Card (A2A Protocol)
        print("\n✅ Test 2: Agent Card (A2A Protocol)")
        response = await client.get(f"{TRAVEL_AGENT_URL}/.well-known/agent.json")
        agent_card = response.json()
        print(f"Agent: {agent_card['name']}")
        print(f"Description: {agent_card['description']}")
        print(f"Skills: {len(agent_card['capabilities']['skills'])} skills")
        for skill in agent_card['capabilities']['skills']:
            print(f"  - {skill['name']}: {skill['description'][:60]}...")
        
        # Test 3: Currency conversion
        print("\n✅ Test 3: Currency Conversion")
        response = await client.post(
            f"{TRAVEL_AGENT_URL}/task",
            json={
                "task": "How much is 500 USD in EUR and JPY?",
                "user_id": "test_user"
            }
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response Content: {response.text[:500]}")
        if response.status_code == 200:
            result = response.json()
            print(f"Result: {result['result'][:300]}...")
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Error: {response.text}")
        
        # Test 4: Restaurant recommendations
        print("\n✅ Test 4: Restaurant Recommendations")
        response = await client.post(
            f"{TRAVEL_AGENT_URL}/task",
            json={
                "task": "Recommend affordable restaurants in Tokyo",
                "user_id": "test_user"
            }
        )
        result = response.json()
        print(f"Result: {result['result'][:400]}...")
        
        # Test 5: Find attractions
        print("\n✅ Test 5: Find Attractions")
        response = await client.post(
            f"{TRAVEL_AGENT_URL}/task",
            json={
                "task": "What are the top attractions in Paris?",
                "user_id": "test_user"
            }
        )
        result = response.json()
        print(f"Result: {result['result'][:400]}...")
        
        # Test 6: Complete itinerary (combines multiple tools)
        print("\n✅ Test 6: Complete Travel Itinerary")
        response = await client.post(
            f"{TRAVEL_AGENT_URL}/task",
            json={
                "task": "Plan a 2-day trip to Rome with a budget of $800. Include restaurants, attractions, and convert the budget to EUR.",
                "user_id": "test_user"
            }
        )
        result = response.json()
        print(f"Result (first 600 chars): {result['result'][:600]}...")
        print("\n... (full itinerary created)")
        
        # Test 7: Day trip planning
        print("\n✅ Test 7: Day Trip Planning")
        response = await client.post(
            f"{TRAVEL_AGENT_URL}/task",
            json={
                "task": "Create a day trip plan for Paris starting at 9 AM with a budget of $150",
                "user_id": "test_user"
            }
        )
        result = response.json()
        print(f"Result: {result['result'][:500]}...")


async def main():
    """Run all tests"""
    print("\n🚀 Starting Travel Agent Tests\n")
    
    # Check if agent is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TRAVEL_AGENT_URL}/health", timeout=5.0)
            if response.status_code != 200:
                print("❌ Travel Agent is not healthy!")
                print("Make sure to start:")
                print("1. Currency MCP Server (port 8001)")
                print("2. Activity MCP Server (port 8002)")
                print("3. Travel Agent (port 8080)")
                return
    except Exception as e:
        print(f"❌ Cannot connect to Travel Agent at {TRAVEL_AGENT_URL}")
        print(f"Error: {e}")
        print("\nMake sure to start:")
        print("1. Currency MCP Server: cd mcp_servers/currency_mcp && python server.py")
        print("2. Activity MCP Server: cd mcp_servers/activity_mcp && python server.py")
        print("3. Travel Agent: cd agents/travel_agent && python main.py")
        return
    
    try:
        await test_travel_agent()
        
        print("\n" + "=" * 70)
        print("✅ All Travel Agent Tests Completed Successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
