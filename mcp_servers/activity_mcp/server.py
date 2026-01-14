"""
Activity MCP Server using FastMCP

A Model Context Protocol (MCP) server that provides travel activity planning tools
including itinerary creation, restaurant recommendations, and sightseeing suggestions.

Tools:
- create_itinerary: Generate a day-by-day travel itinerary
- suggest_restaurants: Get restaurant recommendations for a location
- find_attractions: Find tourist attractions and sightseeing spots
- plan_day_trip: Plan a complete day trip with activities
"""

import asyncio
import logging
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP("activity-mcp", host="0.0.0.0", port=8002)

# Sample data (in production, this would come from APIs or databases)
RESTAURANT_DB = {
    "paris": [
        {"name": "Le Comptoir du Relais", "cuisine": "French Bistro", "price": "€€€", "rating": 4.5},
        {"name": "L'As du Fallafel", "cuisine": "Middle Eastern", "price": "€", "rating": 4.7},
        {"name": "Breizh Café", "cuisine": "Creperie", "price": "€€", "rating": 4.6},
    ],
    "tokyo": [
        {"name": "Sukiyabashi Jiro", "cuisine": "Sushi", "price": "€€€€", "rating": 4.9},
        {"name": "Ichiran Ramen", "cuisine": "Ramen", "price": "€", "rating": 4.5},
        {"name": "Tsukiji Market", "cuisine": "Seafood", "price": "€€", "rating": 4.7},
    ],
    "rome": [
        {"name": "Roscioli", "cuisine": "Italian Deli", "price": "€€€", "rating": 4.6},
        {"name": "Pizzarium", "cuisine": "Pizza", "price": "€", "rating": 4.8},
        {"name": "Trattoria Da Enzo", "cuisine": "Traditional Roman", "price": "€€", "rating": 4.7},
    ],
}

ATTRACTIONS_DB = {
    "paris": [
        {"name": "Eiffel Tower", "type": "Monument", "duration": "2-3 hours", "price": "€26"},
        {"name": "Louvre Museum", "type": "Museum", "duration": "3-4 hours", "price": "€17"},
        {"name": "Notre-Dame Cathedral", "type": "Historic Site", "duration": "1-2 hours", "price": "Free"},
        {"name": "Sacré-Cœur", "type": "Church", "duration": "1-2 hours", "price": "Free"},
    ],
    "tokyo": [
        {"name": "Senso-ji Temple", "type": "Temple", "duration": "1-2 hours", "price": "Free"},
        {"name": "Tokyo Skytree", "type": "Observation Tower", "duration": "2-3 hours", "price": "¥2100"},
        {"name": "Meiji Shrine", "type": "Shrine", "duration": "1-2 hours", "price": "Free"},
        {"name": "Shibuya Crossing", "type": "Landmark", "duration": "30 min", "price": "Free"},
    ],
    "rome": [
        {"name": "Colosseum", "type": "Historic Site", "duration": "2-3 hours", "price": "€18"},
        {"name": "Vatican Museums", "type": "Museum", "duration": "3-4 hours", "price": "€17"},
        {"name": "Trevi Fountain", "type": "Landmark", "duration": "30 min", "price": "Free"},
        {"name": "Roman Forum", "type": "Archaeological Site", "duration": "2 hours", "price": "€16"},
    ],
}


@mcp.tool()
async def create_itinerary(
    destination: str,
    duration_days: int,
    budget: str = "moderate"
) -> str:
    """
    Create a detailed day-by-day travel itinerary for a destination.
    
    Args:
        destination: Destination city (e.g., 'Paris', 'Tokyo', 'Rome')
        duration_days: Number of days for the trip
        budget: Budget level: 'budget', 'moderate', or 'luxury'
    
    Returns:
        Detailed itinerary as a string
    """
    dest_lower = destination.lower()
    
    if dest_lower not in ATTRACTIONS_DB:
        return f"No data available for {destination}. Available destinations: Paris, Tokyo, Rome"
    
    attractions = ATTRACTIONS_DB[dest_lower]
    restaurants = RESTAURANT_DB[dest_lower]
    
    itinerary = f"# {destination.title()} Itinerary ({duration_days} days - {budget.title()} Budget)\n\n"
    
    for day in range(1, min(duration_days + 1, 4)):  # Max 3 days of detailed planning
        itinerary += f"## Day {day}\n\n"
        
        # Morning
        if len(attractions) > (day - 1) * 3:
            attr = attractions[(day - 1) * 3]
            itinerary += f"**Morning (9:00 AM - 12:00 PM)**\n"
            itinerary += f"- Visit: {attr['name']} ({attr['type']})\n"
            itinerary += f"- Duration: {attr['duration']}\n"
            itinerary += f"- Price: {attr['price']}\n\n"
        
        # Lunch
        if len(restaurants) > (day - 1) * 2:
            rest = restaurants[(day - 1) * 2]
            itinerary += f"**Lunch (12:30 PM - 2:00 PM)**\n"
            itinerary += f"- Restaurant: {rest['name']}\n"
            itinerary += f"- Cuisine: {rest['cuisine']}\n"
            itinerary += f"- Price Range: {rest['price']}\n"
            itinerary += f"- Rating: {rest['rating']}/5\n\n"
        
        # Afternoon
        if len(attractions) > (day - 1) * 3 + 1:
            attr = attractions[(day - 1) * 3 + 1]
            itinerary += f"**Afternoon (2:30 PM - 5:30 PM)**\n"
            itinerary += f"- Visit: {attr['name']} ({attr['type']})\n"
            itinerary += f"- Duration: {attr['duration']}\n"
            itinerary += f"- Price: {attr['price']}\n\n"
        
        # Evening
        if len(restaurants) > (day - 1) * 2 + 1:
            rest = restaurants[(day - 1) * 2 + 1]
            itinerary += f"**Dinner (7:00 PM - 9:00 PM)**\n"
            itinerary += f"- Restaurant: {rest['name']}\n"
            itinerary += f"- Cuisine: {rest['cuisine']}\n"
            itinerary += f"- Price Range: {rest['price']}\n"
            itinerary += f"- Rating: {rest['rating']}/5\n\n"
    
    return itinerary


@mcp.tool()
async def suggest_restaurants(
    location: str,
    cuisine_type: str = "any",
    budget: str = "moderate"
) -> str:
    """
    Get restaurant recommendations for a location.
    
    Args:
        location: City or location name
        cuisine_type: Type of cuisine (optional, e.g., 'French', 'Italian')
        budget: Budget level: 'budget', 'moderate', or 'luxury'
    
    Returns:
        List of restaurant recommendations
    """
    loc_lower = location.lower()
    
    if loc_lower not in RESTAURANT_DB:
        return f"No restaurant data for {location}. Available cities: Paris, Tokyo, Rome"
    
    restaurants = RESTAURANT_DB[loc_lower]
    
    result = f"# Restaurant Recommendations in {location.title()}\n\n"
    
    for i, rest in enumerate(restaurants, 1):
        result += f"## {i}. {rest['name']}\n"
        result += f"- **Cuisine**: {rest['cuisine']}\n"
        result += f"- **Price Range**: {rest['price']}\n"
        result += f"- **Rating**: {rest['rating']}/5 ⭐\n\n"
    
    return result


@mcp.tool()
async def find_attractions(
    location: str,
    attraction_type: str = "any"
) -> str:
    """
    Find tourist attractions and sightseeing spots.
    
    Args:
        location: City or location name
        attraction_type: Type of attraction (e.g., 'museum', 'monument', 'historic')
    
    Returns:
        List of attractions with details
    """
    loc_lower = location.lower()
    
    if loc_lower not in ATTRACTIONS_DB:
        return f"No attraction data for {location}. Available cities: Paris, Tokyo, Rome"
    
    attractions = ATTRACTIONS_DB[loc_lower]
    
    result = f"# Attractions in {location.title()}\n\n"
    
    for i, attr in enumerate(attractions, 1):
        result += f"## {i}. {attr['name']}\n"
        result += f"- **Type**: {attr['type']}\n"
        result += f"- **Recommended Duration**: {attr['duration']}\n"
        result += f"- **Entrance Fee**: {attr['price']}\n\n"
    
    return result


@mcp.tool()
async def plan_day_trip(
    start_location: str,
    interests: str = "culture"
) -> str:
    """
    Plan a complete day trip with morning, afternoon, and evening activities.
    
    Args:
        start_location: Starting city or location
        interests: Interests (e.g., 'culture', 'food', 'nature', 'shopping')
    
    Returns:
        Complete day trip plan
    """
    loc_lower = start_location.lower()
    
    if loc_lower not in ATTRACTIONS_DB:
        return f"No data for {start_location}. Available cities: Paris, Tokyo, Rome"
    
    attractions = ATTRACTIONS_DB[loc_lower]
    restaurants = RESTAURANT_DB[loc_lower]
    
    plan = f"# Day Trip Plan: {start_location.title()}\n"
    plan += f"**Focus**: {interests.title()}\n\n"
    
    plan += "## Morning Adventure (9:00 AM - 12:00 PM)\n"
    if attractions:
        plan += f"**Visit**: {attractions[0]['name']}\n"
        plan += f"- Type: {attractions[0]['type']}\n"
        plan += f"- Duration: {attractions[0]['duration']}\n"
        plan += f"- Cost: {attractions[0]['price']}\n\n"
    
    plan += "## Lunch Break (12:30 PM - 2:00 PM)\n"
    if restaurants:
        plan += f"**Dining**: {restaurants[0]['name']}\n"
        plan += f"- Cuisine: {restaurants[0]['cuisine']}\n"
        plan += f"- Budget: {restaurants[0]['price']}\n\n"
    
    plan += "## Afternoon Exploration (2:30 PM - 6:00 PM)\n"
    if len(attractions) > 1:
        plan += f"**Visit**: {attractions[1]['name']}\n"
        plan += f"- Type: {attractions[1]['type']}\n"
        plan += f"- Duration: {attractions[1]['duration']}\n"
        plan += f"- Cost: {attractions[1]['price']}\n\n"
    
    plan += "## Evening Experience (7:00 PM - 9:00 PM)\n"
    if len(restaurants) > 1:
        plan += f"**Dinner**: {restaurants[1]['name']}\n"
        plan += f"- Cuisine: {restaurants[1]['cuisine']}\n"
        plan += f"- Budget: {restaurants[1]['price']}\n"
    
    return plan


if __name__ == "__main__":
    logger.info("Starting Activity MCP Server in StreamableHTTP mode on port 8002")
    mcp.run(transport="streamable-http")
