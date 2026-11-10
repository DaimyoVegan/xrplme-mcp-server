# XRPLME Country Intelligence — MCP Server

Source-backed economic and policy data for 90 countries, served over MCP and paid
per call with [x402](https://x402.org) — settled in **XRP**, or **USDC** on Solana
and Base.

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
| `xrplme_list_countries` | List the 90 countries | Free |
| `xrplme_get_country_status` | Live health probe for one country | Free |
| `xrplme_get_pricing` | Current prices for every rail | Free |
| `xrplme_get_country_data` | Latest structured data + sources + freshness for one country | **Paid** |
| `xrplme_get_country_schema` | Field schema for one country (JSON Schema) | **Paid** |
| `xrplme_get_survey_questions` | Survey questions for AI agents | Free |
| `xrplme_submit_survey` | Submit feedback | Free |
| `xrplme_get_survey_stats` | Aggregated survey statistics | Free |

### Prices

| Tier | XRP Ledger | Solana | Base |
|---|---|---|---|
| Standard (`xrplme_get_country_schema`) | 1 XRP | 1.0 USDC | 1.0 USDC |
| AI-enhanced (`xrplme_get_country_data`) | 5 XRP | 7.0 USDC | 7.0 USDC |

### Investigate: screening and company look-up

Two more datasets, same rails, same payment flow. These are plain HTTP
endpoints today — they are not MCP tools yet.

| Endpoint | XRP Ledger | Solana / Base |
|---|---|---|
| `/wc/screen/bot` | 2 XRP | $2.00 USDC |
| `/wc/entity/lookup/bot` | 1 XRP | $1.00 USDC |
| `/wc/entity/ownership/bot` | 5 XRP | $5.00 USDC |

Append `-solana` or `-evm` to the path for the USDC rails. Screening takes
`{"name": "..."}`; look-up and ownership take `{"query": "..."}`.

Machine-readable pricing for agents: **https://xrplme.online/llms.txt**

`xrplme_get_pricing` always returns the live values — query it rather than
hard-coding these.

---

## How payment works

1. Call a paid tool with no payment. The server replies **HTTP 402** with the
   exact amount, asset, recipient, and accepted networks. Nothing is charged and
   no data is returned.
2. Pay on any of four rails:
   - **XRP Ledger** — pass `X-PAYMENT-SIGNATURE` + `X-INV-ID` headers
   - **Solana** — pass `X-PAYMENT-SIGNATURE` header with a base64-encoded V2
     payment payload containing the signed Solana transaction
   - **Base** — send USDC on Base to the `payTo` in the challenge, then pass the
     transaction hash as `x_base_tx` (MCP tool argument) or as
     `PAYMENT-SIGNATURE: {"txHash":"0x…"}` on the HTTP routes
   - **Credit card** — open the Crossmint on-ramp URL from
     `https://api.xrplme.online/api/v1/card/start`, buy XRP with a card in
     your browser, then pay the x402 invoice. No crypto wallet required.
3. Call the tool again with the payment attached. On successful settlement the
   data is returned.

Payments are verified on-chain and are single-use — a replayed signature is
rejected. Data is released only after settlement is confirmed, never before.

### Networks

| Rail | Network |
|---|---|
| XRP Ledger | `xrpl:0` (mainnet) |
| Solana | `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` (mainnet) |
| Base | `eip155:8453` (mainnet) |

Solana payments use native USDC
(`EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`). Base payments use USDC on Base
(`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`).

### Solana payment details

Solana pays use the x402 exact payment scheme via a local facilitator
(`http://127.0.0.1:8402`). The 402 response includes a `feePayer` in the
`extra` field — this is the wallet that pays Solana transaction fees. Your
client must:

1. Build a transaction with 3 instructions: `SetComputeUnitLimit`,
   `SetComputeUnitPrice`, and `TransferChecked` (USDC, 6 decimals)
2. Set the `feePayer` from the 402 response as the transaction fee payer
3. Partially sign the transaction with your wallet (which holds the USDC) —
   **do not** sign with the fee payer; the facilitator adds its signature
4. Encode the partially-signed transaction as base64 and include it in a V2
   payment payload:

```json
{
  "x402Version": 2,
  "payload": {"transaction": "<base64-encoded signed tx>"},
  "accepted": { /* from the 402 response's accepts[0] */ }
}
```

5. Base64-encode the entire payload JSON and send it as the
   `X-PAYMENT-SIGNATURE` header on the retry request.

See [`xrplme-mcp-client/examples/x402_payment_solana.py`](https://github.com/DaimyoVegan/xrplme-mcp-client/blob/main/examples/x402_payment_solana.py)
for a complete end-to-end example.

### Base payment details

Base uses the same x402 `exact` scheme, but the proof is a settled transfer rather
than a signed transaction. The 402 gives you `payTo` and `amount`; you send that
much USDC on Base from any wallet; you hand back the transaction hash — as
`x_base_tx` on the MCP tools, or as `PAYMENT-SIGNATURE: {"txHash":"0x…"}` (JSON or
base64 JSON) on the HTTP routes.

The server then reads the receipt and verifies the token, the recipient, the amount
and the age of the transfer itself. No facilitator sits in the path, so nothing has
to vouch for the payment on trust.

One transfer buys one call. A reused hash is refused, and so is a transfer below the
tier price, older than one hour, on another chain, or sent to another address.

A Base Sepolia twin (`eip155:84532`, test USDC) verifies identically and answers
`test_payment_verified` instead of returning data — test money is free at a faucet,
so it never buys country records.

See [`xrplme-mcp-client/examples/x402_payment_base.py`](https://github.com/DaimyoVegan/xrplme-mcp-client/blob/main/examples/x402_payment_base.py)
for a stdlib client that fetches the challenge, prints what to pay, and retries with
proof of payment.

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
- Coverage is 90 countries. `xrplme_list_countries` is the authoritative list.
---

## Response Schema

Every paid response follows a structured v1 schema documented at
https://xrplme.online/schema/v1/response-schema.json.

Key fields:

- `meta` — country slug, query ID, retrieval timestamp, data freshness, payment proof
- `sources[]` — array of primary sources with URL, publisher, date, and confidence score
- `facts` — deterministic structured data by domain (company_formation, labor, tax, etc.)
- `synthesis` — AI summary, key risks, contradictions found, overall confidence
- `agent_hints` — recommended follow-up tools, related countries, update frequency

This structure lets agents chain calls without re-parsing prose.