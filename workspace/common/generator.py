"""
common.generator — synthetic transaction feed for the fraud engine.

Baseline is provided and working. Produces realistic-looking BFSI transactions
(amount, merchant category, channel, location, device, timestamp) with a small,
seeded share of transactions shaped to look suspicious (high amount, odd hour,
high-risk merchant, new device) so the engine has real signal to find.

This never emits a "ground truth fraud" label to the rest of the pipeline —
your engine has to find the patterns itself, same as production.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

MERCHANT_CATEGORIES = [
    "grocery", "fuel", "utility", "online_retail", "electronics",
    "travel", "atm_withdrawal", "jewellery", "wallet_topup", "insurance_premium",
]
HIGH_RISK_MERCHANTS = {"jewellery", "electronics", "wallet_topup"}
CHANNELS = ["POS", "ONLINE", "ATM", "MOBILE_APP"]
CITIES = [
    "Mumbai", "Bengaluru", "Delhi", "Chennai", "Hyderabad",
    "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Kochi",
]


def _mask_pan(card_number: str) -> str:
    """Render a card number safe for display/logs — last 4 digits only."""
    digits = card_number.replace(" ", "")
    return f"****{digits[-4:]}"


def _random_card_number(rng: random.Random) -> str:
    return "4" + "".join(str(rng.randint(0, 9)) for _ in range(15))


def generate_transactions(count: int = 1000, seed: int = 42, anomaly_rate: float = 0.06) -> list[dict]:
    """Generate `count` synthetic transactions with a seeded share of anomalies.

    Each transaction: txn_id, account_id, card_number (already masked), amount_inr,
    merchant_category, channel, city, device_id, hour_of_day, timestamp.
    """
    rng = random.Random(seed)
    now = datetime.now(timezone.utc)
    transactions: list[dict] = []

    for i in range(count):
        is_anomaly_shape = rng.random() < anomaly_rate
        account_id = f"ACC-{rng.randint(100000, 999999)}"
        card_number = _random_card_number(rng)

        if is_anomaly_shape:
            amount_inr = rng.randint(150_000, 900_000)
            merchant_category = rng.choice(list(HIGH_RISK_MERCHANTS))
            hour_of_day = rng.choice([1, 2, 3, 23])
            device_id = f"DEV-NEW-{rng.randint(1000, 9999)}"
        else:
            amount_inr = rng.randint(50, 45_000)
            merchant_category = rng.choice(MERCHANT_CATEGORIES)
            hour_of_day = rng.randint(6, 22)
            device_id = f"DEV-{rng.randint(1, 300):04d}"

        txn = {
            "txn_id": f"TXN-{i + 1:06d}",
            "account_id": account_id,
            "card_number_masked": _mask_pan(card_number),
            "amount_inr": amount_inr,
            "merchant_category": merchant_category,
            "channel": rng.choice(CHANNELS),
            "city": rng.choice(CITIES),
            "device_id": device_id,
            "hour_of_day": hour_of_day,
            "timestamp": (now - timedelta(seconds=rng.randint(0, 86_400))).isoformat(),
        }
        transactions.append(txn)

    return transactions


if __name__ == "__main__":
    batch = generate_transactions(count=5, seed=1)
    for t in batch:
        print(t)
