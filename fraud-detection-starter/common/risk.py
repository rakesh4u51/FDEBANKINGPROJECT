"""
common.risk — real-time risk prioritization: HIGH / MEDIUM / LOW (Activity 3).

STUB: implement the two functions during Activity 3.

Design intent:
- assign_risk_tier() turns a fraud_score + matched_patterns into one of three
  tiers the fraud desk can act on immediately:
    HIGH   — fraud_score >= 70, OR 2+ matched patterns
    MEDIUM — fraud_score >= 40, OR exactly 1 matched pattern
    LOW    — everything else
- prioritize_queue() groups a scored transaction list by tier and returns the
  HIGH tier sorted by fraud_score descending (the analyst's work queue), plus
  counts for the daily report.
"""

from __future__ import annotations

HIGH_THRESHOLD = 70
MEDIUM_THRESHOLD = 40


def assign_risk_tier(fraud_score: int, matched_patterns: list[str]) -> str:
    """Return "HIGH", "MEDIUM", or "LOW" for one transaction's score/signals."""
    # TODO(P4): apply the HIGH/MEDIUM/LOW rule above (score OR pattern-count).
    raise NotImplementedError("Activity 3: implement assign_risk_tier()")


def prioritize_queue(scored_transactions: list[dict]) -> dict:
    """Group scored transactions by tier.

    Each item in `scored_transactions` already has fraud_score and
    matched_patterns (from common.patterns.detect_fraud_signals). Return:
        {
          "HIGH": [...sorted by fraud_score desc...],
          "MEDIUM": [...],
          "LOW": [...],
          "counts": {"HIGH": n, "MEDIUM": n, "LOW": n},
        }
    """
    # TODO(P4): assign_risk_tier() per transaction, bucket, sort HIGH desc, count.
    raise NotImplementedError("Activity 3: implement prioritize_queue()")


if __name__ == "__main__":
    demo = [
        {"txn_id": "TXN-1", "fraud_score": 82, "matched_patterns": ["AMOUNT_ANOMALY", "ODD_HOUR"]},
        {"txn_id": "TXN-2", "fraud_score": 45, "matched_patterns": ["NEW_DEVICE"]},
        {"txn_id": "TXN-3", "fraud_score": 5, "matched_patterns": []},
    ]
    print(prioritize_queue(demo))
