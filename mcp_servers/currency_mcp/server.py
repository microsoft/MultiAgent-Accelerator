"""
Currency MCP Server

A Model Context Protocol (MCP) server that provides currency exchange tools
using the Frankfurter API for real-time exchange rates.

Tools:
- get_exchange_rate: Get exchange rate between two currencies
- convert_currency: Convert an amount from one currency to another
- get_supported_currencies: List all supported currency codes
"""

import asyncio
import logging
import httpx
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Frankfurter API base URL
FRANKFURTER_API = "https://api.frankfurter.app"

# Timeout for HTTP requests
HTTP_TIMEOUT = 10.0

# Create FastMCP server
mcp = FastMCP("currency-mcp", host="0.0.0.0", port=8001)


@mcp.tool()
async def get_exchange_rate(
    currency_from: str,
    currency_to: str,
    date: str = "latest"
) -> str:
    """
    Get the current exchange rate between two currencies.
    
    Args:
        currency_from: Source currency code (e.g., 'USD', 'EUR', 'GBP')
        currency_to: Target currency code (e.g., 'EUR', 'JPY', 'CNY')
        date: Optional date in YYYY-MM-DD format. Use 'latest' for current rate (default).
    
    Returns:
        Exchange rate information as a string
    """
    try:
        url = f"{FRANKFURTER_API}/{date}"
        params = {"from": currency_from.upper(), "to": currency_to.upper()}

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        if "rates" not in data or currency_to.upper() not in data["rates"]:
            return f"Could not retrieve rate for {currency_from} to {currency_to}"

        rate = data["rates"][currency_to.upper()]
        rate_date = data.get("date", date)

        return (
            f"Exchange rate on {rate_date}: "
            f"1 {currency_from.upper()} = {rate:.4f} {currency_to.upper()}"
        )

    except httpx.HTTPStatusError as e:
        return f"HTTP error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Error fetching exchange rate: {str(e)}"


@mcp.tool()
async def convert_currency(
    amount: float,
    currency_from: str,
    currency_to: str,
    date: str = "latest"
) -> str:
    """
    Convert an amount from one currency to another.
    
    Args:
        amount: Amount to convert
        currency_from: Source currency code (e.g., 'USD')
        currency_to: Target currency code (e.g., 'EUR')
        date: Optional date in YYYY-MM-DD format for historical rates
    
    Returns:
        Conversion result as a string
    """
    try:
        url = f"{FRANKFURTER_API}/{date}"
        params = {
            "amount": amount,
            "from": currency_from.upper(),
            "to": currency_to.upper(),
        }

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        if "rates" not in data or currency_to.upper() not in data["rates"]:
            return f"Could not convert {currency_from} to {currency_to}"

        converted_amount = data["rates"][currency_to.upper()]
        rate = converted_amount / amount if amount != 0 else 0
        conversion_date = data.get("date", date)

        return (
            f"Conversion on {conversion_date}:\n"
            f"{amount:.2f} {currency_from.upper()} = "
            f"{converted_amount:.2f} {currency_to.upper()}\n"
            f"Exchange rate: 1 {currency_from.upper()} = {rate:.4f} {currency_to.upper()}"
        )

    except httpx.HTTPStatusError as e:
        return f"HTTP error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Error converting currency: {str(e)}"


@mcp.tool()
async def get_supported_currencies() -> str:
    """
    Get a list of all currency codes supported by the exchange rate service.
    
    Returns:
        List of currency codes with their full names
    """
    try:
        url = f"{FRANKFURTER_API}/currencies"

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.get(url)
            response.raise_for_status()
            currencies = response.json()

        result = "Supported currencies:\n"
        for code, name in sorted(currencies.items()):
            result += f"  {code}: {name}\n"

        return result

    except Exception as e:
        return f"Error fetching supported currencies: {str(e)}"


if __name__ == "__main__":
    logger.info("Starting Currency MCP Server in StreamableHTTP mode on port 8001")
    mcp.run(transport="streamable-http")
