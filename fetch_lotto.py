"""
Downloads the UK Lotto draw history and keeps a running copy in data/lotto.csv.

The National Lottery only publishes roughly the last 180 days, so new draws are
merged into the existing file rather than replacing it.
"""
import csv
import io
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

SOURCE = "https://www.national-lottery.co.uk/results/lotto/draw-history/csv"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "lotto.csv")
FIELDS = ["DrawDate", "Ball 1", "Ball 2", "Ball 3", "Ball 4", "Ball 5", "Ball 6",
          "Bonus Ball", "DrawNumber"]

# Ordinary browser headers – the site refuses requests that don't look like a browser.
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"),
    "Accept": "text/csv,text/plain,text/html;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Referer": "https://www.national-lottery.co.uk/results/lotto/draw-history",
}


def download(url, tries=3):
    last = None
    for attempt in range(1, tries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8-sig")
        except urllib.error.HTTPError as e:
            body = e.read()[:200].decode("utf-8", "replace").replace("\n", " ")
            last = f"HTTP {e.code} {e.reason} – {body}"
        except Exception as e:  # noqa: BLE001
            last = f"{type(e).__name__}: {e}"
        print(f"Attempt {attempt} failed: {last}", file=sys.stderr)
        time.sleep(10 * attempt)
    fail(f"Could not download results: {last}")


def fail(msg):
    # ::error:: shows the message on the run's summary page.
    print(f"::error::{msg}")
    raise SystemExit(1)


def parse_date(s):
    s = s.strip()
    for fmt in ("%d-%b-%Y", "%d-%b-%y", "%d %b %Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def norm(h):
    return h.strip().lower().replace(" ", "")


def parse(text):
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) < 2:
        fail("Download had no rows – the site may have sent a block page: " + text[:200].replace("\n", " "))
    head = [norm(h) for h in rows[0]]
    try:
        i_date = next(i for i, h in enumerate(head) if "date" in h)
        i_balls = [head.index(f"ball{n}") for n in range(1, 7)]
    except (StopIteration, ValueError):
        fail(f"Unexpected file layout: {rows[0][:12]}")
    i_bonus = next((i for i, h in enumerate(head) if "bonus" in h), None)
    i_no = next((i for i, h in enumerate(head) if h == "drawnumber"), None)

    draws = {}
    for r in rows[1:]:
        if len(r) <= max(i_balls):
            continue
        d = parse_date(r[i_date])
        try:
            balls = [int(r[i]) for i in i_balls]
        except ValueError:
            continue
        if not d or not all(1 <= b <= 59 for b in balls):
            continue
        bonus = r[i_bonus].strip() if i_bonus is not None and i_bonus < len(r) else ""
        no = r[i_no].strip() if i_no is not None and i_no < len(r) else ""
        draws[d.isoformat()] = [d.isoformat(), *map(str, balls), bonus, no]
    return draws


def load_existing():
    if not os.path.exists(OUT):
        return {}
    with open(OUT, newline="", encoding="utf-8") as f:
        return {row[0]: row for row in list(csv.reader(f))[1:] if row}


def main():
    new = parse(download(SOURCE))
    if not new:
        fail("No valid draws found in the download.")
    merged = load_existing()
    added = [d for d in new if d not in merged]
    merged.update(new)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        for d in sorted(merged, reverse=True):  # newest first, like the official file
            w.writerow(merged[d])

    latest = max(merged)
    print(f"{len(merged)} draws saved, {len(added)} new. Latest: {latest} {merged[latest][1:7]}")


if __name__ == "__main__":
    main()
