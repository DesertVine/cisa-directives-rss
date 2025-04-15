import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import hashlib
import os
import json

URL = "https://www.cisa.gov/directives"
FEED_FILE = "rss.xml"
STATE_FILE = "directives_state.json"

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

def generate_rss(directives):
    fg = FeedGenerator()
    fg.title("CISA Directives")
    fg.link(href=URL)
    fg.description("Feed of CISA's Cybersecurity Directives")
    fg.language("en")

    for d in directives:
        fe = fg.add_entry()
        fe.id(d["id"])
        fe.title(d["title"])
        fe.link(href=d["url"])
        fe.published(datetime.now().isoformat())

    fg.rss_file(FEED_FILE)

def main():
    current = fetch_directives()
    previous = load_previous_state()

    if current != previous:
        print("Change detected, updating RSS feed.")
        generate_rss(current)
        save_current_state(current)
    else:
        print("No changes found.")

if __name__ == "__main__":
    main()
