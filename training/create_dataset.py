"""Create a deterministic synthetic churn dataset for the local assignment environment."""

from __future__ import annotations

import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "raw" / "customer_churn.csv"


def main() -> None:
    random.seed(4016)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["tenure_months", "monthly_charge", "support_tickets", "contract", "churn"],
        )
        writer.writeheader()
        for _ in range(240):
            tenure = random.randint(1, 72)
            charge = round(random.uniform(20, 120), 2)
            tickets = random.randint(0, 6)
            contract = random.choice(["month_to_month", "one_year", "two_year"])
            # This is deliberately deterministic rather than a realistic customer
            # simulator.  It gives the coursework pipeline a learnable relationship
            # that is easy to inspect: flexible contracts, more support tickets,
            # short tenure, and higher charges all increase churn risk.
            risk_score = 2.6 if contract == "month_to_month" else (-0.4 if contract == "one_year" else -1.1)
            risk_score += tickets * 0.82
            risk_score -= tenure * 0.055
            risk_score += (charge - 60) * 0.018
            writer.writerow(
                {
                    "tenure_months": tenure,
                    "monthly_charge": charge,
                    "support_tickets": tickets,
                    "contract": contract,
                    "churn": int(risk_score > 1.35),
                }
            )


if __name__ == "__main__":
    main()
