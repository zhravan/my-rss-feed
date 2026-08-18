import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

CONFIG = "config.json"
FEED = "feed.xml"
USER_AGENT = "Mozilla/5.0 (compatible; MyRSSFeed/1.0; +https://github.com/zhravan/my-rss-feed)"


def clean_text(value):
    return re.sub(r"\s+", " ", value or "").strip()


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


def fetch_page(url):
    response = requests.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.text


def parse_linkedin_posts(markup, source_label):
    soup = BeautifulSoup(markup, "html.parser")
    posts = []

    for anchor in soup.find_all("a", href=True):
        href = urljoin("https://www.linkedin.com", anchor["href"])
        clean_href = href.split("?")[0]
        if "linkedin.com/posts/" not in clean_href and "linkedin.com/feed/update/" not in clean_href:
            continue

        text = clean_text(anchor.get_text(" ", strip=True))
        if not text:
            # Some public search pages expose the post text in a nearby parent.
            parent = anchor.find_parent()
            text = clean_text(parent.get_text(" ", strip=True)) if parent else ""
        if not text:
            continue

        posts.append({
            "title": f"{source_label}: {text[:140]}",
            "link": clean_href,
            "description": text[:4000],
            "pubDate": format_datetime(datetime.now(timezone.utc)),
            "guid": clean_href,
        })

    unique = {}
    for post in posts:
        unique.setdefault(post["guid"], post)
    return list(unique.values())


def fetch_profile(profile_url):
    return parse_linkedin_posts(fetch_page(profile_url), profile_url.rstrip("/").split("/")[-1])


def fetch_keyword(keyword):
    # Public LinkedIn content-search URL. If LinkedIn requires authentication or
    # returns a challenge page, the request is skipped rather than bypassing it.
    search_url = "https://www.linkedin.com/search/results/content/?keywords=" + quote(keyword)
    return parse_linkedin_posts(fetch_page(search_url), f'LinkedIn · {keyword}')


def write_feed(items):
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "My LinkedIn RSS Feed"
    ET.SubElement(channel, "link").text = "https://zhravan.github.io/my-rss-feed/"
    ET.SubElement(channel, "description").text = "LinkedIn posts from followed people and keywords"
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

    for profile in config.get("linkedin_profiles", [])[: config.get("max_items_per_profile", 20)]:
        try:
            for post in fetch_profile(profile):
                by_guid.setdefault(post["guid"], post)
        except requests.RequestException as exc:
            print(f"Could not fetch LinkedIn profile {profile}: {exc}")

    for keyword in config.get("linkedin_keywords", []):
        try:
            posts = fetch_keyword(keyword)
            for post in posts[: config.get("max_items_per_keyword", 20)]:
                by_guid.setdefault(post["guid"], post)
        except requests.RequestException as exc:
            print(f"Could not fetch LinkedIn keyword '{keyword}': {exc}")

    items = list(by_guid.values())[: config.get("max_total_items", 200)]
    write_feed(items)


if __name__ == "__main__":
    main()
