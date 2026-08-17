import html
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

CONFIG = "config.json"
FEED = "feed.xml"
USER_AGENT = "Mozilla/5.0 (compatible; MyRSSFeed/1.0; +https://github.com/zhravan/my-rss-feed)"


def clean_text(value):
    return re.sub(r"\\s+", " ", value or "").strip()


def load_existing():
    if not os.path.exists(FEED):
        return []
    try:
        root = ET.parse(FEED).getroot()
        return [
            {
                "title": item.findtext("title", "LinkedIn post"),
                "link": item.findtext("link", ""),
                "description": item.findtext("description", ""),
                "pubDate": item.findtext("pubDate", format_datetime(datetime.now(timezone.utc))),
                "guid": item.findtext("guid", item.findtext("link", "")),
            }
            for item in root.findall("./channel/item")
        ]
    except (ET.ParseError, OSError):
        return []


def fetch_profile(url):
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
        timeout=30,
    )
    response.raise_for_status()
    return response.text


def parse_posts(profile_url, markup):
    soup = BeautifulSoup(markup, "html.parser")
    profile_name = clean_text(soup.find("h1").get_text(" ", strip=True)) if soup.find("h1") else profile_url.rstrip("/").split("/")[-1]
    posts = []

    # LinkedIn's public activity pages can expose post/article links in anchors.
    for anchor in soup.find_all("a", href=True):
        href = urljoin(profile_url, anchor["href"])
        if "linkedin.com/posts/" not in href and "linkedin.com/feed/update/" not in href:
            continue
        text = clean_text(anchor.get_text(" ", strip=True))
        if not text:
            continue
        posts.append({
            "title": f"{profile_name}: {text[:140]}",
            "link": href.split("?")[0],
            "description": text,
            "pubDate": format_datetime(datetime.now(timezone.utc)),
            "guid": href.split("?")[0],
        })

    # Remove duplicate links while preserving order.
    unique = {}
    for post in posts:
        unique.setdefault(post["link"], post)
    return list(unique.values())


def write_feed(items):
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "My RSS Feed"
    ET.SubElement(channel, "link").text = "https://zhravan.github.io/my-rss-feed/"
    ET.SubElement(channel, "description").text = "Personal RSS feed"
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(datetime.now(timezone.utc))

    for item in items:
        node = ET.SubElement(channel, "item")
        ET.SubElement(node, "title").text = item["title"]
        ET.SubElement(node, "link").text = item["link"]
        ET.SubElement(node, "guid", {"isPermaLink": "true"}).text = item["guid"]
        ET.SubElement(node, "pubDate").text = item["pubDate"]
        ET.SubElement(node, "description").text = item["description"]

    ET.ElementTree(rss).write(FEED, encoding="utf-8", xml_declaration=True)


def main():
    with open(CONFIG, encoding="utf-8") as f:
        config = json.load(f)

    existing = load_existing()
    by_guid = {item["guid"]: item for item in existing}

    for profile in config.get("linkedin_profiles", []):
        try:
            markup = fetch_profile(profile)
            for post in parse_posts(profile, markup):
                by_guid.setdefault(post["guid"], post)
        except requests.RequestException as exc:
            print(f"Could not fetch {profile}: {exc}")

    items = list(by_guid.values())[: config.get("max_total_items", 100)]
    write_feed(items)


if __name__ == "__main__":
    main()
