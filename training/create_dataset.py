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
            risk = (0.45 if contract == "month_to_month" else 0.16) + tickets * 0.07
            risk += 0.18 if tenure < 10 else 0
            risk += 0.1 if charge > 95 else 0
            writer.writerow(
                {
                    "tenure_months": tenure,
                    "monthly_charge": charge,
                    "support_tickets": tickets,
                    "contract": contract,
                    "churn": int(random.random() < min(risk, 0.9)),
                }
            )


if __name__ == "__main__":
    main()
