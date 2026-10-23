# XRPLME Agent Examples

Working code showing how AI agents connect to the `xrplme.online` MCP server,
pay per call via **x402** (XRP Ledger or Solana USDC), and receive structured
country policy data.

## Quick Start

### 1. Add to your MCP client (Claude Desktop, Cursor, Cline)

Copy the config for your client:

**Claude Desktop** — `~/Library/Application Support/Claude/claude_desktop_config.json`
(on Windows: `%APPDATA%\Claude\claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "xrplme": {
      "type": "http",
      "url": "https://api.xrplme.online/mcp"
    }
  }
}
```

**Cursor** — `.cursor/mcp.json` in your project:
```json
{
  "mcp": {
    "servers": {
      "xrplme": {
        "type": "http",
        "url": "https://api.xrplme.online/mcp"
      }
    }
  }
}
```

**Cline** — in the Cline MCP settings:
```
URL: https://api.xrplme.online/mcp
```

Full configs with descriptions:
- `claude-desktop-xmcp.json` — Claude Desktop config
- `cursor-mcp.json` — Cursor config

### 2. Use the REST API directly (Python script)

```bash
export XRPL_WALLET_SEED="sYourSeedHere"
python3 examples/example_xrplme_agent.py --country thailand --query "company formation"
```

This script demonstrates the full flow:
1. Send request → get 402 with `invoiceId`, `payTo`, `amount`
2. Sign + submit XRPL payment
3. Retry with `X-PAYMENT-SIGNATURE` + `X-INVOICE-ID` headers
4. Receive structured JSON with sources, facts, synthesis, and payment TXID

Prerequisites: `pip install requests xrpl-py`

### 3. Use with CrewAI

```bash
export XRPL_WALLET_SEED="sYourSeedHere"
python3 examples/crewai_xrplme_agent.py
```

### 4. Use with MCP Python SDK

```bash
pip install mcp
python3 examples/mcp_client_example.py
```

## Pricing

| Tool | XRP | USDC | Description |
|---|---|---|---|
| `xrplme_list_countries` | Free | Free | List the 30 countries |
| `xrplme_get_country_status` | Free | Free | Health probe |
| `xrplme_get_pricing` | Free | Free | Current prices |
| `xrplme_get_survey_questions` | Free | Free | Feedback questions |
| `xrplme_submit_survey` | Free | Free | Submit feedback |
| `xrplme_get_survey_stats` | Free | Free | Quality stats |
| `xrplme_get_country_data` | 0.5 XRP | 0.25 USDC | Structured data + sources |
| `xrplme_get_country_schema` | 0.1 XRP | 0.05 USDC | Field schema |

## Response Schema

All paid responses follow the v1 schema at:
https://xrplme.online/schema/v1/response-schema.json

Key fields: `meta` (payment proof + freshness), `sources[]` (URLs + confidence),
`facts` (structured by domain), `synthesis` (summary + contradictions).
