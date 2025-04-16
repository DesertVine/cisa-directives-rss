import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import hashlib
import os
import json

URL = "https://www.cisa.gov/news-events/directives"
FEED_FILE = "docs/rss.xml"
STATE_FILE = "docs/directives_state.json"

def fetch_directives():
    print("Fetching directives from CISA...")
    res = requests.get(URL)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    directives = []

    for article in soup.select("article.c-teaser"):
        a_tag = article.find("a", href=True)
        title = a_tag.get_text(strip=True)
        url = f"https://www.cisa.gov{a_tag['href']}"
        date_tag = article.find("time")
        pub_date = date_tag["datetime"] if date_tag else datetime.now(timezone.utc).isoformat()

        id = hashlib.md5(url.encode()).hexdigest()
        directives.append({
            "id": id,
            "title": title,
            "url": url,
            "published": pub_date
        })

    print(f"Found {len(directives)} directive(s).")
    return directives

def load_previous_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    print(f"Loaded {len(data)} previous directive(s).")
                    return data
        except Exception as e:
            print(f"Warning: Could not load previous state. Reason: {e}")
    print("No previous state found or file was invalid.")
    return []

def save_current_state(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)
    print(f"Saved {len(data)} directive(s) to state file.")

def generate_rss(directives):
    print(f"Generating RSS feed with {len(directives)} item(s).")
    fg = FeedGenerator()
    fg.title("CISA Directives (New Only)")
    fg.link(href=URL)
    fg.description("Latest CISA Directive(s) only")
    fg.language("en")

    for d in directives[:25]:
        fe = fg.add_entry()
        fe.id(d["id"])
        fe.title(d["title"])
        fe.link(href=d["url"])
        fe.published(d.get("published", datetime.now(timezone.utc).isoformat()))

    fg.rss_file(FEED_FILE)
    print("RSS feed written to file.")

def main():
    current = fetch_directives()
    previous = load_previous_state()

    previous_ids = {d["id"] for d in previous}
    new_directives = [d for d in current if d["id"] not in previous_ids]

    if not previous_ids:
        print("First run — generating RSS for all current directives.")
        generate_rss(current[:25])
        save_current_state(current)
    elif new_directives:
        print(f"{len(new_directives)} new directive(s) found. Updating RSS.")
        generate_rss(new_directives[:25])
        save_current_state(current)
    else:
        print("No new directives found. Nothing to do.")

if __name__ == "__main__":
    main()
