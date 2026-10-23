#!/usr/bin/env python3
"""
CrewAI Agent that uses XRPLME country data
==========================================
Shows how to integrate XRPLME's paid MCP tools into a CrewAI workflow.

Prerequisites:
    pip install crewai requests

Usage:
    XRPL_WALLET_SEED='s...' python3 examples/crewai_xrplme_agent.py
"""

import json
import os
import requests
from crewai import Agent, Task, Crew

# XRPLME REST endpoint (same as MCP, via StreamableHTTP)
BASE_URL = "https://xrplme.online/wc/v1"


class XRPLMETool:
    """Wrapper tool for XRPLME's paid country data API."""

    def __init__(self, wallet_seed: str):
        self.wallet_seed = wallet_seed

    def get_country_data(self, country: str, query: str) -> dict:
        """Get structured country policy data. Cost: 0.5 XRP or 0.25 USDC."""
        # Step 1: Get 402 with payment requirements
        resp = requests.post(
            f"{BASE_URL}/{country}/bot",
            json={"prompt": query},
            timeout=15,
        )

        if resp.status_code == 402:
            payment = resp.json()
            accept = payment["accepts"][0]
            invoice_id = accept["extra"]["invoiceId"]
            pay_to = accept["payTo"]
            amount_drops = int(accept["amount"])

            # Step 2: Sign + pay via xrpl-py
            from xrpl.core import Keypair
            from xrpl.clients import JsonRpcClient
            from xrpl.transaction import submit, sign
            from xrpl.account import get_account_info

            kp = Keypair.from_seed(self.wallet_seed)
            client = JsonRpcClient("wss://xrplcluster.com")
            info = get_account_info(client, kp.classic_address)
            seq = info.result["account_data"]["Sequence"]
            last = info.result["account_data"]["LedgerIndex"] + 10

            tx = {
                "TransactionType": "Payment",
                "Account": kp.classic_address,
                "Destination": pay_to,
                "Amount": str(amount_drops),
                "SourceTag": accept["extra"]["sourceTag"],
                "Fee": "12",
                "Sequence": str(seq),
                "LastLedgerSequence": str(last),
            }

            signed = sign(tx, kp)
            result = submit(signed, client)
            tx_hash = result.result.get("tx_json", {}).get("hash", "")

            if not tx_hash:
                return {"error": "Payment failed", "detail": result.result}

            # Step 3: Retry with payment proof
            resp = requests.post(
                f"{BASE_URL}/{country}/bot",
                json={"prompt": query},
                headers={
                    "X-PAYMENT-SIGNATURE": tx_hash,
                    "X-INVOICE-ID": invoice_id,
                },
                timeout=15,
            )

        if resp.status_code == 200:
            data = resp.json()
            # Extract the payment TXID from the response
            txid = data.get("meta", {}).get("payment", {}).get("txid", tx_hash)
            return {
                "success": True,
                "country": country,
                "payment_txid": txid,
                "data": data,
            }
        else:
            return {"error": f"HTTP {resp.status_code}", "response": resp.text[:500]}


def main():
    wallet_seed = os.environ.get("XRPL_WALLET_SEED")
    if not wallet_seed:
        print("Set XRPL_WALLET_SEED environment variable")
        return

    tool = XRPLMETool(wallet_seed)

    # Create a CrewAI agent
    agent = Agent(
        role="Country Risk Analyst",
        goal="Analyze economic and regulatory data for Southeast Asian countries",
        backstory="You are an expert on Southeast Asian markets with deep knowledge "
                   "of regulatory environments. You use source-backed data from xrplme.online.",
        tools=[tool.get_country_data],
        verbose=True,
    )

    task = Task(
        description="Compare company formation requirements between Thailand and Singapore. "
                    "Focus on foreign ownership limits, minimum capital, and timeline.",
        expected_output="A structured comparison with sources cited.",
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task])
    result = crew.kickoff()
    print("\n=== CrewAI Result ===")
    print(result)


if __name__ == "__main__":
    main()
