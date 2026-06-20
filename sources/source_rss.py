import sys
import os
import json
import feedparser
from datetime import datetime

# add project root to path so we can import from contracts/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contracts import source_schema

RSS_URL = "https://www.cnbc.com/id/100003114/device/rss/rss.html"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fetch():
    # Purpose: get the latest 5 news items from CNBC RSS and write to data/
    # Input: none
    # Output: none (writes to data/source_rss.json)

    feed = feedparser.parse(RSS_URL)

    if len(feed.entries) == 0:
        print("source_rss: no entries found, feed may be unavailable or blocked")
        print("source_rss: feed status:", getattr(feed, "status", "unknown"))
        return

    items = []
    count = 0

    for entry in feed.entries:
        if count >= 5:
            break

        title = entry.get("title", "")
        summary = entry.get("summary", "")

        if summary != "":
            text = title + " — " + summary
        else:
            text = title

        item = {
            "text": text,
            "meta": {
                "title": title,
                "link": entry.get("link", "")
            }
        }
        items.append(item)
        count = count + 1

    data = {
        "source_name": "rss",
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "items": items
    }

    is_valid = source_schema.validate(data)
    if not is_valid:
        print("source_rss: data failed validation, not writing file")
        return

    data_dir = os.path.join(PROJECT_ROOT, "data")
    os.makedirs(data_dir, exist_ok=True)
    filepath = os.path.join(data_dir, "source_rss.json")

    f = open(filepath, "w", encoding="utf-8")
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.close()

    print("source_rss: wrote", len(items), "items to", filepath)


if __name__ == "__main__":
    fetch()
