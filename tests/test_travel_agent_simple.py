"""
Simple test for Travel Agent without MCP tools
"""

import asyncio
import httpx

TRAVEL_AGENT_URL = "http://localhost:8080"


async def test_simple():
    """Test basic agent response"""
    
    print("Testing simple response (no tools)...")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Simple greeting
        response = await client.post(
            f"{TRAVEL_AGENT_URL}/task",
            json={
                "task": "Hello! What can you help me with?",
                "user_id": "test_user"
            }
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response: {result['result']}")
        else:
            print(f"❌ Error: {response.text}")


if __name__ == "__main__":
    asyncio.run(test_simple())
