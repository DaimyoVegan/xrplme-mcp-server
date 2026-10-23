#!/usr/bin/env python3
"""
XRPLME Country Intelligence — Paid MCP Agent Example
====================================================
Demonstrates the full x402 payment flow to /wc/v1/{country}/bot:
  1. Send request -> get 402 Payment Required
  2. Extract invoiceId, payTo, amount from the x402 response
  3. Sign + submit XRPL payment from your wallet
  4. Retry request with X-PAYMENT-SIGNATURE + X-INVOICE-ID headers
  5. Get structured JSON data + transaction proof

Prerequisites:
    pip install requests xrpl-py

Set your XRPL wallet seed as an environment variable:
    export XRPL_WALLET_SEED="sEs..."

Usage:
    python3 examples/example_xrplme_agent.py --country thailand --query "company formation"
"""

import argparse
import json
import os
import sys
import time

import requests
from xrpl.core import Keypair
from xrpl.clients import JsonRpcClient
from xrpl.transaction import submit, sign
from xrpl.account import get_account_info

# --- Configuration ---
BASE_URL = "https://xrplme.online/wc/v1"
XRPL_SERVER = "wss://xrplcluster.com"
COLLECTOR_ADDRESS = "razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8"  # x402 payTo address (public)
SOURCE_TAG = 804681468


def get_wallet():
    """Load wallet from environment variable."""
    seed = os.environ.get("XRPL_WALLET_SEED")
    if not seed:
        print("\nError: Set XRPL_WALLET_SEED environment variable.")
        print("  export XRPL_WALLET_SEED='sYourSeedHere'")
        print("  (NEVER commit your seed to version control)")
        sys.exit(1)
    return Keypair.from_seed(seed)


def call_endpoint(country, query, payment_sig=None, invoice_id=None):
    """Make a request to the country bot endpoint."""
    url = f"{BASE_URL}/{country}/bot"
    headers = {"Content-Type": "application/json"}
    if payment_sig:
        headers["X-PAYMENT-SIGNATURE"] = payment_sig
        headers["X-INVOICE-ID"] = invoice_id
    
    payload = {"prompt": query}
    return requests.post(url, json=payload, headers=headers, timeout=15)


def pay_xrp(wallet_seed, pay_to, amount_drops, source_tag, invoice_id):
    """Submit an XRPL payment transaction and return the transaction hash."""
    kp = Keypair.from_seed(wallet_seed)
    sender_addr = kp.classic_address

    client = JsonRpcClient(XRPL_SERVER)

    # Get account info for sequence + last_ledger
    info = get_account_info(client, sender_addr)
    account_data = info.result["account_data"]
    sequence = account_data["Sequence"]
    last_ledger = account_data["LedgerIndex"] + 10

    # Build the payment transaction
    tx = {
        "TransactionType": "Payment",
        "Account": sender_addr,
        "Destination": pay_to,
        "Amount": str(amount_drops),
        "SourceTag": source_tag,
        "Fee": "12",
        "Sequence": str(sequence),
        "LastLedgerSequence": str(last_ledger),
    }

    # Sign and submit
    signed = sign(tx, kp)
    result = submit(signed, client)
    
    meta = result.result
    if meta.get("engine_result") != "tesSUCCESS":
        return None, meta.get("engine_result", "unknown error")
    
    tx_hash = meta.get("tx_json", {}).get("hash", "")
    return tx_hash, None


def pay_solana(wallet_keypair, pay_to, amount_usdc_micro, invoice_id):
    """Submit a Solana USDC payment and return the transaction signature."""
    from solders.keypair import Keypair as SolKeypair
    from solders.transaction import Transaction
    from solders.system_program import transfer
    from solders.rpc.api import Client

    client = Client("https://api.mainnet-beta.solana.com")

    # Create transfer instruction
    sender_kp = wallet_keypair
    txn = Transaction().add(
        transfer(
            from_pubkey=sender_kp.pubkey(),
            to_pubkey=pay_to,
            lamports=amount_usdc_micro,  # USDC amount in micro-units
        )
    )

    blockhash = client.get_latest_blockhash().value.blockhash
    txn.recent_blockhash = blockhash
    txn.fee_payer = sender_kp.pubkey()

    txn.sign([sender_kp])
    sig = client.send_raw_transaction(txn.serialize()).value
    return str(sig)


def main():
    parser = argparse.ArgumentParser(description="XRPLME paid agent example")
    parser.add_argument("--country", default="thailand", help="Country slug (e.g. thailand)")
    parser.add_argument("--query", default="company formation requirements", help="Query prompt")
    parser.add_argument("--rail", choices=["xrpl", "solana"], default="xrpl", help="Payment rail")
    args = parser.parse_args()

    wallet_seed = os.environ.get("XRPL_WALLET_SEED")

    print(f"1. Querying {args.country}: '{args.query}'")
    resp = call_endpoint(args.country, args.query)

    if resp.status_code == 402:
        payment_data = resp.json()
        accept = payment_data["accepts"][0]
        invoice_id = accept["extra"]["invoiceId"]
        pay_to = accept["payTo"]
        amount_drops = int(accept["amount"])
        xrp_amount = amount_drops / 1_000_000
        qr_data = accept.get("qrData", "")
        scheme = accept["scheme"]["network"]

        print(f"   Got 402: invoice={invoice_id[:8]}..., payTo={pay_to[:12]}...")
        print(f"   Amount: {xrp_amount} XRP ({amount_drops} drops)")
        print(f"   Network: {scheme}")
        if qr_data:
            print(f"   QR for mobile wallets: {qr_data}")

        if args.rail == "xrpl":
            print(f"\n2. Paying {xrp_amount} XRP via XRPL...")
            print(f"   TX: {qr_data}")
            tx_hash, err = pay_xrp(
                wallet_seed, pay_to, amount_drops, SOURCE_TAG, invoice_id
            )
            if err:
                print(f"   Payment failed: {err}")
                print(f"\n   MANUAL: Pay {xrp_amount} XRP to {pay_to}")
                print(f"   Source tag: {SOURCE_TAG}")
                print(f"   Then run with the tx hash as X-PAYMENT-SIGNATURE header")
                return

            print(f"   Transaction submitted! TXID: {tx_hash}")
            print(f"   Explorer: https://livenet.xrpl.org/transactions/{tx_hash}")

            print(f"\n3. Retrying with payment proof...")
            resp = call_endpoint(args.country, args.query, tx_hash, invoice_id)

        elif args.rail == "solana":
            print(f"\n2. Paying via Solana USDC...")
            print(f"   TODO: Connect your Solana wallet to pay {amount_drops / 1_000_000} USDC to {pay_to}")
            return

    elif resp.status_code == 200:
        print("   Already paid or using cached payment")
    else:
        print(f"   Unexpected response: {resp.status_code}")
        print(resp.text[:500])
        return

    # Step 4: Show the structured response
    if resp.status_code == 200:
        data = resp.json()
        print(f"\n4. SUCCESS! Structured data received:")
        print(f"   Country: {data.get('slug', args.country)}")
        print(f"   Retrieved: {data.get('retrieved_at', 'N/A')}")

        # Show sources
        sources = data.get("sources", [])
        if sources:
            print(f"\n   Sources ({len(sources)}):")
            for s in sources[:3]:
                print(f"   - {s.get('title', 'N/A')} ({s.get('confidence', 0)})")
                print(f"     URL: {s.get('url', 'N/A')}")

        # Show facts
        facts = data.get("facts", {})
        if facts:
            print(f"\n   Facts domains: {', '.join(facts.keys())}")
            for domain, values in list(facts.items())[:1]:
                print(f"   {domain}: {json.dumps(values, indent=2)[:500]}")

        # Show synthesis
        synthesis = data.get("synthesis", {})
        if synthesis:
            print(f"\n   Summary: {synthesis.get('summary', 'N/A')[:200]}")
            if synthesis.get("contradictions_found"):
                print(f"   Contradictions found: {len(synthesis['contradictions_found'])}")

        # Payment proof
        meta = data.get("meta", {})
        if meta.get("payment", {}).get("txid"):
            print(f"\n   Payment TXID: {meta['payment']['txid']}")
            print(f"   Rail: {meta['payment']['rail']}")
            print(f"   Amount: {meta['payment']['amount']}")

        print(f"\n   Full response saved to: response_{args.country}_{int(time.time())}.json")
        with open(f"response_{args.country}_{int(time.time())}.json", "w") as f:
            json.dump(data, f, indent=2)

        print("\n   Done! You paid for and received structured policy data.")
    else:
        print(f"\n   Retry failed: {resp.status_code}")
        print(resp.text[:500])


if __name__ == "__main__":
    main()
