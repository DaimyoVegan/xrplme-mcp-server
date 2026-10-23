#!/usr/bin/env python3
"""
MCP Client Example — Call XRPLME MCP tools
============================================
Shows how to connect to the XRPLME MCP server via StreamableHTTP,
list tools, and call them. For paid tools, the MCP client handles
x402 payment automatically if a wallet is configured.

Prerequisites:
    pip install mcp requests

Connects to: https://api.xrplme.online/mcp

The MCP StreamableHTTP transport handles the x402 handshake:
  1. Client calls tool -> server returns 402 with PaymentRequirements
  2. Client pays (auto via wallet or manual QR scan)
  3. Client retries with x_payment_signature + x_inv_id
  4. Server returns structured data
"""

import asyncio
import json
import os

from mcp import ClientSession
from mcp.transport.http import ClientHttpUrl
from mcp.types import Tool


MCP_URL = "https://api.xrplme.online/mcp"


async def main():
    # Connect to the MCP server
    async with ClientSession(transport=ClientHttpUrl(MCP_URL)) as session:
        # List available tools
        tools = await session.list_tools()
        print("=== Available Tools ===")
        for tool in tools.tools:
            print(f"\n{tool.name}:")
            print(f"  Description: {tool.description}")
            print(f"  Parameters: {json.dumps(tool.inputSchema, indent=2)[:500]}")

        # Call free tools
        print("\n=== Free: list_countries ===")
        result = await session.call_tool("xrplme_list_countries")
        countries = json.loads(result.content[0].text)
        print(f"Countries: {countries.get('countries', [])[:5]}...")

        print("\n=== Free: get_country_status (thailand) ===")
        result = await session.call_tool("xrplme_get_country_status", {"slug": "thailand"})
        status = json.loads(result.content[0].text)
        print(f"Status: {json.dumps(status, indent=2)[:500]}")

        print("\n=== Free: get_pricing ===")
        result = await session.call_tool("xrplme_get_pricing")
        pricing = json.loads(result.content[0].text)
        print(f"Pricing: {json.dumps(pricing, indent=2)[:500]}")

        # Paid tool - requires x402
        print("\n=== Paid: get_country_data (thailand) ===")
        try:
            result = await session.call_tool(
                "xrplme_get_country_data",
                {"slug": "thailand", "x_payment_signature": "...", "x_inv_id": "..."}
            )
            data = json.loads(result.content[0].text)
            print(f"Data: {json.dumps(data, indent=2)[:500]}")

            # Show payment proof
            payment = data.get("meta", {}).get("payment", {})
            if payment:
                print(f"\nPayment TXID: {payment.get('txid')}")
                print(f"Rail: {payment.get('rail')}")
                print(f"Amount: {payment.get('amount')}")
        except Exception as e:
            print(f"Expected 402 — set up wallet for auto-payment or pay manually")
            print(f"Error: {e}")

        print("\n=== Resources ===")
        resources = await session.list_resources()
        for r in resources.resources:
            print(f"  {r.uri}: {r.name}")

        # Read the schema resource
        schema_uri = "https://xrplme.online/schema/v1/response-schema.json"
        try:
            resource = await session.read_resource(schema_uri)
            print(f"\n=== Schema ({schema_uri}) ===")
            print(resource.content[:500] if isinstance(resource.content, str) else resource.content)
        except:
            print("Schema resource not accessible via MCP read (use HTTP)")

        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
