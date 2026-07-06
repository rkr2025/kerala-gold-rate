import json
import re
from datetime import datetime, timezone

import requests

SOURCE_URL = "https://keralagold.com/daily-gold-prices.htm"


def fetch_month_rates():
    response = requests.get(SOURCE_URL, timeout=10)
    response.raise_for_status()
    html = response.text

    row_pattern = re.compile(r"<tr[^>]*>((?:(?!</tr>).)*?)</tr>", re.IGNORECASE | re.DOTALL)
    date_pattern = re.compile(r"(\d{1,2}-[A-Za-z]{3}-\d{2})")

    rows = []
    for row in row_pattern.finditer(html):
        content = row.group(1)
        date_match = date_pattern.search(content)
        if not date_match:
            continue

        tail = content[date_match.end():]
        price_match = re.search(r"([\d,]{4,})", tail)
        if not price_match:
            continue

        if "Morning" in content:
            label = "Morning"
        elif "Forenoon" in content:
            label = "Forenoon"
        elif "Evening" in content:
            label = "Evening"
        elif "Today" in content:
            label = "Today"
        else:
            label = ""

        note = ""
        if "Lowest of Month" in content:
            note = "Lowest of Month"
        elif "Highest of Month" in content:
            note = "Highest of Month"
        elif "Yesterday" in content:
            note = "Yesterday"

        price = price_match.group(1)
        pavan_value = int(price.replace(",", ""))
        if "," not in price:
            price = f"{pavan_value:,}"

        gram_value = round(pavan_value / 8)  # 1 Pavan = 8 grams

        rows.append({
            "date": date_match.group(1),
            "label": label,
            "price": f"Rs. {price}",
            "price_per_gram": f"Rs. {gram_value:,}",
            "note": note,
        })

    if not rows:
        raise ValueError("Could not find any gold rate rows on source page")

    return rows


def main():
    rows = fetch_month_rates()
    today_row = next((r for r in rows if r["label"] == "Today"), None)

    data = {
        "source_url": SOURCE_URL,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "today": today_row,
        "month_rows": rows,
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Wrote {len(rows)} rows to data.json")


if __name__ == "__main__":
    main()
