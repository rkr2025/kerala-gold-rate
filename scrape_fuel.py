import json
import re
from datetime import datetime, timezone

import requests

PETROL_URL = "https://www.goodreturns.in/petrol-price-in-kerala-s18.html"
DIESEL_URL = "https://www.goodreturns.in/diesel-price-in-kerala-s18.html"

HEADERS = {"User-Agent": "Mozilla/5.0"}

ROW_PATTERN = re.compile(r"<tr[^>]*>((?:(?!</tr>).)*?)</tr>", re.IGNORECASE | re.DOTALL)
DISTRICT_PATTERN = re.compile(r'title="([^"]+)"[^>]*>([^<]+)</a>', re.IGNORECASE)
PRICE_PATTERN = re.compile(r"&#x20b9;\s*([\d.]+)")
CHANGE_PATTERN = re.compile(r'class="(fp-flat|fp-up|fp-down)">\s*([+\-\d.]+)', re.IGNORECASE)


def fetch_district_table(url):
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    html = response.text

    rows = {}
    for row in ROW_PATTERN.finditer(html):
        content = row.group(1)
        district_match = DISTRICT_PATTERN.search(content)
        price_match = PRICE_PATTERN.search(content)
        if not district_match or not price_match:
            continue

        change_match = CHANGE_PATTERN.search(content)
        change = change_match.group(2).strip() if change_match else None

        district = district_match.group(1).strip()
        rows[district] = {
            "price": price_match.group(1),
            "change": change,
        }

    if not rows:
        raise ValueError(f"Could not find any district rows at {url}")

    return rows


def main():
    petrol_rows = fetch_district_table(PETROL_URL)
    diesel_rows = fetch_district_table(DIESEL_URL)

    districts = sorted(set(petrol_rows) | set(diesel_rows))
    combined = []
    for district in districts:
        petrol = petrol_rows.get(district, {})
        diesel = diesel_rows.get(district, {})
        combined.append({
            "district": district,
            "petrol_price": petrol.get("price"),
            "petrol_change": petrol.get("change"),
            "diesel_price": diesel.get("price"),
            "diesel_change": diesel.get("change"),
        })

    today_district = "Thiruvananthapuram"
    today = next((d for d in combined if d["district"] == today_district), None)

    data = {
        "source_urls": {"petrol": PETROL_URL, "diesel": DIESEL_URL},
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "today": today,
        "districts": combined,
    }

    with open("data-fuel.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Wrote {len(combined)} districts to data-fuel.json")


if __name__ == "__main__":
    main()
