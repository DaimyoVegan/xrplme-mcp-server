#!/usr/bin/env python3
"""
DEMO: xrplme Online - x402 Payment + Structured Data Flow
=========================================================
Shows the complete flow:
  1. POST /wc/v1/{country}/bot  → 402 with x402 invoice
  2. Pay via XRPL mainnet (0.5 XRP)
  3. POST again with X-PAYMENT-SIGNATURE + X-INVOICE-ID headers → 200
  4. Response is v1-structured JSON with sources[], facts, synthesis, TXID in meta.payment.txid

Prerequisites:
  pip install requests xrpl-py

Usage:
  python3 demo_xrplme_x402.py --country thailand

Environment:
  XRPL_SEED  - Your XRPL mainnet wallet seed (starts with 's')
  If not set, the script will show the payment flow without signing.
"""
import json
import sys
import argparse
import requests

# --- xrpl-py for on-chain payment ---
from xrpl.wallet import Wallet
from xrpl.clients import JsonRpcClient
from xrpl.transaction import submit_and_wait, autofill, sign
from xrpl.models import Payment

BASE = "https://xrplme.online"

def get_payment_requirements(country):
    """Step 1: GET the 402 payment requirements."""
    resp = requests.post(
        f"{BASE}/wc/v1/{country}/bot",
        json={"prompt": "What are visa requirements for retirees?", "session_id": "demo"},
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    if resp.status_code != 402:
        print(f"Unexpected status {resp.status_code}: {resp.text[:200]}")
        return None

    print(f"[Step 1] Got 402 Payment Required")
    data = resp.json()
    accepts = data.get("accepts", [])

    # Pick XRPL payment (first accept on xrpl:0)
    xrpl_accept = None
    for a in accepts:
        if a.get("network", "").startswith("xrpl"):
            xrpl_accept = a
            break
    if not xrpl_accept:
        print("No XRPL payment option found")
        return None

    invoice_id = xrpl_accept.get("extra", {}).get("invoiceId")
    amount_drops = int(xrpl_accept.get("amount", "0"))
    pay_to = xrpl_accept.get("payTo")
    source_tag = xrpl_accept.get("extra", {}).get("sourceTag")

    print(f"  Invoice ID: {invoice_id}")
    print(f"  Amount: {amount_drops / 1_000_000} XRP ({amount_drops} drops)")
    print(f"  Pay To: {pay_to}")
    if source_tag:
        print(f"  Source Tag: {source_tag}")

    return {
        "invoice_id": invoice_id,
        "amount_drops": amount_drops,
        "pay_to": pay_to,
        "source_tag": source_tag,
    }


def pay_invoice_xrpl(payment_info, wallet_seed):
    """Step 2: Sign and submit the XRPL payment."""
    print(f"\n[Step 2] Signing and submitting XRPL payment...")

    client = JsonRpcClient("https://s1.ripple.com/")
    wallet = Wallet(seed=wallet_seed)

    payment_tx = Payment(
        account=wallet.address,
        destination=payment_info["pay_to"],
        amount=str(payment_info["amount_drops"]),
    )
    if payment_info.get("source_tag"):
        payment_tx = Payment(
            account=wallet.address,
            destination=payment_info["pay_to"],
            amount=str(payment_info["amount_drops"]),
            destination_tag=payment_info["source_tag"],
        )

    # Sign and submit
    try:
        signed_tx = sign(payment_tx, wallet); signed_tx = autofill(signed_tx, client)
        result = submit_and_wait(signed_tx, client)
        tx_hash = result["tx_hash"] if isinstance(result, dict) else result[0]["tx_hash"]
        print(f"  ✅ Payment submitted! TXID: {tx_hash}")
        return tx_hash
    except Exception as e:
        print(f"  ❌ Payment failed: {e}")
        # For demo without real mainnet XRP, generate a mock tx_hash
        import hashlib
        mock_hash = hashlib.sha256(f"demo_{payment_info['invoice_id']}".encode()).hexdigest().upper()[:64]
        print(f"  Using mock TXID for demo: {mock_hash}")
        return mock_hash


def get_paid_data(country, invoice_id, tx_hash):
    """Step 3: Retry the request with payment proof → 200 with v1-structured data."""
    print(f"\n[Step 3] Retrying with payment proof...")
    print(f"  X-PAYMENT-SIGNATURE: {tx_hash}")
    print(f"  X-INVOICE-ID: {invoice_id}")

    resp = requests.post(
        f"{BASE}/wc/v1/{country}/bot",
        json={"prompt": "What are visa requirements for retirees?", "session_id": "demo"},
        headers={
            "Content-Type": "application/json",
            "X-PAYMENT-SIGNATURE": tx_hash,
            "X-INVOICE-ID": invoice_id,
        },
        timeout=30,
    )

    if resp.status_code != 200:
        print(f"  ❌ Got {resp.status_code}: {resp.text[:200]}")
        return None

    print(f"\n[Step 4] ✅ Got structured data (HTTP 200)!")

    # Parse response — it's JSON with v1 schema structure
    try:
        data = resp.json()
        # Check if it has the v1 schema structure
        if "meta" in data:
            print("\n=== V1 Schema Response ===")
            meta = data.get("meta", {})
            print(f"  Country: {meta.get('country_slug')}")
            print(f"  Schema: {meta.get('schema_version')}")
            print(f"  Query ID: {meta.get('query_id')}")
            print(f"  TXID: {meta.get('payment', {}).get('txid')}")
            print(f"  Amount paid: {meta.get('payment', {}).get('amount')}")
            print(f"  Retrieved: {meta.get('retrieved_at')}")
            print(f"  Sources: {len(data.get('sources', []))}")
            print(f"  Facts topics: {list(data.get('facts', {}).keys())}")
            synth = data.get("synthesis", {})
            print(f"  Confidence: {synth.get('confidence_overall')}")
            print(f"  Summary: {synth.get('summary')[:100]}...")
        else:
            print(f"  Raw response (no v1 schema): {json.dumps(data)[:300]}...")
        return data
    except Exception as e:
        print(f"  Could not parse as JSON: {e}")
        print(f"  Raw: {resp.text[:500]}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="xrplme x402 payment demo")
    parser.add_argument("--country", default="thailand", help="Country slug (default: thailand)")
    parser.add_argument("--seed", default=None, help="XRPL mainnet wallet seed (or set XRPL_SEED env)")
    args = parser.parse_args()

    import os
    wallet_seed = args.seed or os.environ.get("XRPL_SEED")

    print(f"=== xrplme x402 Demo — Country: {args.country} ===\n")

    # Step 1: Get payment requirements
    payment = get_payment_requirements(args.country)
    if not payment:
        sys.exit(1)

    # Step 2: Pay via XRPL
    if wallet_seed:
        tx_hash = pay_invoice_xrpl(payment, wallet_seed)
    else:
        print("\n[Step 2] Skipping payment (no wallet seed provided)")
        print("  Set XRPL_SEED env var or use --seed to make a real payment")
        import hashlib
        tx_hash = hashlib.sha256(b"demo_tx_placeholder").hexdigest().upper()[:64]
        print(f"  Using placeholder TXID: {tx_hash}")

    # Step 3+4: Get paid data
    data = get_paid_data(args.country, payment["invoice_id"], tx_hash)
    if data:
        print("\n=== Demo complete ===")
        print(f"Full response saved below (first 500 chars):")
        print(json.dumps(data, indent=2)[:500])
