"""
Test script for Currency and Activity MCP Servers

This script tests the MCP servers directly using the MCP Python SDK.
Run this to verify the servers are working before integrating with Travel Agent.
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_currency_mcp():
    """Test Currency MCP Server"""
    print("=" * 60)
    print("Testing Currency MCP Server")
    print("=" * 60)
    
    # Server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_servers/currency_mcp/server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            
            # List available tools
            print("\n📋 Available Tools:")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Test 1: Get exchange rate
            print("\n🧪 Test 1: Get Exchange Rate (USD to EUR)")
            result = await session.call_tool(
                "get_exchange_rate",
                arguments={
                    "currency_from": "USD",
                    "currency_to": "EUR",
                    "date": "latest"
                }
            )
            print(f"Result: {result.content[0].text}")
            
            # Test 2: Convert currency
            print("\n🧪 Test 2: Convert 500 USD to EUR")
            result = await session.call_tool(
                "convert_currency",
                arguments={
                    "amount": 500,
                    "currency_from": "USD",
                    "currency_to": "EUR"
                }
            )
            print(f"Result: {result.content[0].text}")
            
            # Test 3: Get supported currencies
            print("\n🧪 Test 3: Get Supported Currencies")
            result = await session.call_tool(
                "get_supported_currencies",
                arguments={}
            )
            currencies = result.content[0].text
            # Show first 10 lines
            lines = currencies.split('\n')[:11]
            print('\n'.join(lines))
            print("  ... (more currencies)")


async def test_activity_mcp():
    """Test Activity MCP Server"""
    print("\n" + "=" * 60)
    print("Testing Activity MCP Server")
    print("=" * 60)
    
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_servers/activity_mcp/server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            
            # List available tools
            print("\n📋 Available Tools:")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description[:80]}...")
            
            # Test 1: Suggest restaurants
            print("\n🧪 Test 1: Suggest Restaurants in Paris")
            result = await session.call_tool(
                "suggest_restaurants",
                arguments={
                    "location": "Paris",
                    "budget": "moderate"
                }
            )
            restaurants = result.content[0].text
            print(restaurants[:500] + "...")
            
            # Test 2: Find attractions
            print("\n🧪 Test 2: Find Attractions in Tokyo")
            result = await session.call_tool(
                "find_attractions",
                arguments={
                    "location": "Tokyo"
                }
            )
            attractions = result.content[0].text
            print(attractions[:500] + "...")
            
            # Test 3: Create itinerary
            print("\n🧪 Test 3: Create 2-Day Itinerary for Rome")
            result = await session.call_tool(
                "create_itinerary",
                arguments={
                    "destination": "Rome",
                    "duration_days": 2,
                    "budget": "moderate",
                    "interests": ["history", "food"]
                }
            )
            itinerary = result.content[0].text
            # Show first 30 lines
            lines = itinerary.split('\n')[:30]
            print('\n'.join(lines))
            print("  ... (more days)")
            
            # Test 4: Plan day trip
            print("\n🧪 Test 4: Plan Day Trip to Paris")
            result = await session.call_tool(
                "plan_day_trip",
                arguments={
                    "destination": "Paris",
                    "start_time": "09:00",
                    "budget": "$100"
                }
            )
            day_trip = result.content[0].text
            print(day_trip[:600] + "...")


async def main():
    """Run all tests"""
    print("\n🚀 Starting MCP Server Tests\n")
    
    try:
        # Test Currency MCP
        await test_currency_mcp()
        
        # Test Activity MCP
        await test_activity_mcp()
        
        print("\n" + "=" * 60)
        print("✅ All MCP Server Tests Completed Successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
