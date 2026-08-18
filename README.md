# My RSS Feed

A free, GitHub-hosted RSS feed aggregator. LinkedIn is the first source; more sources can be added later.

## Configure LinkedIn

Edit `config.json`:

```json
{
  "linkedin_profiles": [],
  "linkedin_keywords": [
    "AI agents",
    "RAG"
  ],
  "max_items_per_profile": 20,
  "max_items_per_keyword": 20,
  "max_total_items": 200
}
```

- `linkedin_profiles`: public LinkedIn profile URLs to monitor.
- `linkedin_keywords`: terms searched on LinkedIn's public content-search page.
- Posts are deduplicated by LinkedIn post URL.

## Automation

GitHub Actions runs hourly and can also be started manually. It regenerates `feed.xml` and commits changes.

The collector only uses publicly accessible LinkedIn pages. If LinkedIn requires authentication, presents a challenge, or changes its markup, that source is skipped rather than bypassed.

## Feed

Enable GitHub Pages for the repository root if you want a stable public RSS URL:

`https://zhravan.github.io/my-rss-feed/feed.xml`
