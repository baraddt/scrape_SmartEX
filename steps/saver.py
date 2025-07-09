import json
import pandas as pd
from pathlib import Path


def export_to_excel(append=False, filename="train_schedule.xlsx"):
    path = Path("response.json")
    if not path.exists():
        print("response.json not found.")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print("No data in response.json.")
        return

    rows = []
    for item in data:
        adult = item.get("adult_passengers", "0")
        child = item.get("child_passengers", "0")

        ticket_parts = []
        if adult and adult != "0":
            ticket_parts.append("Adult(s)")
        if child and child != "0":
            ticket_parts.append("Child(ren)")

        ticket_type = ", ".join(ticket_parts) if ticket_parts else "-"

        rows.append(
            {
                # "Date": item.get("date", ""),
                "Route": f"{item.get('departure_station')} - {item.get('arrival_station')}",
                "Time": f"{item.get('departure_time')} - {item.get('arrival_time')}",
                "Arr": item.get("duration", ""),
                "Fare": item.get("fare_type", ""),
                "Ticket Type": ticket_type,
                "Class": item.get("class", ""),
                "Price": item.get("price", ""),
                "Train": f"Shinkansen {item.get('train_name')}",
            }
        )

    rows.append({key: "" for key in rows[0].keys()})

    df = pd.DataFrame(rows)

    file_path = filename

    if append and Path(file_path).exists():
        existing = pd.read_excel(file_path)
        combined = pd.concat([existing, df], ignore_index=True)
        combined.to_excel(file_path, index=False)
    else:
        df.to_excel(file_path, index=False)

    print(f"Data successfully exported ({len(df)} rows) → {file_path}")
