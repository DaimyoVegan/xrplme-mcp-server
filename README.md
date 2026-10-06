# XRPLME Country Intelligence — MCP Server

Source-backed economic and policy data for 30 countries, served over MCP and paid
per call with [x402](https://x402.org) — settled in **XRP** or **USDC**.

No accounts, no API keys. The payment *is* the authentication.

**Live endpoint:** `https://api.xrplme.online/mcp` — Streamable HTTP transport.

> **What this repository is.** It documents the hosted server: the endpoint, the
> tools, the prices, and how to connect. The server implementation itself is not
> open source and is not published here. Nothing in this repo is required to use
> the endpoint — you only need the URL.

---

## Connect

Add the server to any MCP client that supports Streamable HTTP:

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

Then call `xrplme_list_countries` to see the coverage. It is free.

---

## Tools

Eight tools are exposed. Six are free; two require payment.

| Tool | What it does | Cost |
|---|---|---|
| `xrplme_list_countries` | List the 30 countries | Free |
| `xrplme_get_country_status` | Live health probe for one country | Free |
| `xrplme_get_pricing` | Current prices for both rails | Free |
| `xrplme_get_country_data` | Latest data + freshness for one country | **Paid** |
| `xrplme_get_country_schema` | Field schema for one country | **Paid** |
| `xrplme_get_survey_questions` | Survey questions for AI agents | Free |
| `xrplme_submit_survey` | Submit agent feedback | Free |
| `xrplme_get_survey_stats` | Aggregated survey statistics | Free |

### Prices

| Tier | XRP Ledger | Solana |
|---|---|---|
| Standard (`xrplme_get_country_schema`) | 0.1 XRP | 0.05 USDC |
| AI-enhanced (`xrplme_get_country_data`) | 0.5 XRP | 0.25 USDC |

`xrplme_get_pricing` always returns the live values — query it rather than
hard-coding these.

---

## How payment works

1. Call a paid tool with no payment. The server replies **HTTP 402** with the
   exact amount, asset, recipient, and accepted networks. Nothing is charged and
   no data is returned.
2. Pay on either rail:
   - **XRP Ledger** — pass `x_payment_signature` + `x_inv_id`
   - **Solana** — pass `x_sol_payload` (USDC; a Solana Pay URI is included in
     the 402 response)
3. Call the tool again with the payment attached. On successful settlement the
   data is returned.

Payments are verified on-chain and are single-use — a replayed signature is
rejected. Data is released only after settlement is confirmed, never before.

### Networks

| Rail | Network |
|---|---|
| XRP Ledger | `xrpl:0` (mainnet) |
| Solana | `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` (mainnet) |

Solana payments use native USDC
(`EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`).

---

## Registry

Listed in the official MCP Registry as
[`io.github.DaimyoVegan/xrplme-paid`](https://registry.modelcontextprotocol.io/v0.1/servers?search=xrplme-paid).

---

## Related

- **[xrplme-mcp-client](https://github.com/DaimyoVegan/xrplme-mcp-client)** —
  client examples and working payment flows.
- **Website / API docs:** <https://xrplme.online/api-docs.html>

---

## Notes

- Data is sourced from national statistics offices, central banks, and
  regulators. Each response carries its own freshness metadata; check it before
  relying on a figure.
- Coverage is 30 countries. `xrplme_list_countries` is the authoritative list.
