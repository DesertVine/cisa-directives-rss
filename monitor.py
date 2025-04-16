import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import hashlib
import os
import json

URL = "https://www.cisa.gov/directives"
FEED_FILE = "docs/rss.xml"
STATE_FILE = "docs/directives_state.json"

def fetch_directives():
    res = requests.get(URL)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    
    directives = []
    for link in soup.select("a[href*='/directive/']"):
        href = link['href']
        title = link.get_text(strip=True)
        full_url = f"https://www.cisa.gov{href}"
        id = hashlib.md5(full_url.encode()).hexdigest()
        directives.append({
            "id": id,
            "title": title,
            "url": full_url
        })
    return directives

def load_previous_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return []

def save_current_state(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)

def generate_rss(new_directives):
    fg = FeedGenerator()
    fg.title("CISA Directives (New Only)")
    fg.link(href=URL)
    fg.description("Latest CISA Directive(s) only")
    fg.language("en")

    for d in new_directives[:25]:
        fe = fg.add_entry()
        fe.id(d["id"])
        fe.title(d["title"])
        fe.link(href=d["url"])
        fe.published(datetime.now().isoformat())

    fg.rss_file(FEED_FILE)

def main():
    current = fetch_directives()
    previous = load_previous_state()

    # Set of known directive IDs
    previous_ids = {d["id"] for d in previous}
    new_directives = [d for d in current if d["id"] not in previous_ids]

    # If no state exists or it's empty, treat as first run
    if not previous_ids:
        print("First run — generating feed for all current directives.")
        generate_rss(current[:25])  # Still limit to 25 if a ton exist
        save_current_state(current)
    elif new_directives:
        print(f"{len(new_directives)} new directive(s) found. Updating feed.")
        generate_rss(new_directives[:25])
        save_current_state(current)
    else:
        print("No new directives. RSS feed not updated.")

if __name__ == "__main__":
    main()
