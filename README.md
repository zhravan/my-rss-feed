# My RSS Feed

A free, GitHub-hosted RSS feed aggregator. LinkedIn is the first source; more sources can be added later.

## Configure LinkedIn profiles

Edit `config.json` and add public LinkedIn profile URLs to `linkedin_profiles`.

## Feed

The generated feed is `feed.xml`. Enable GitHub Pages for the repository root if you want a stable public RSS URL.

## Important

The workflow only attempts to process publicly accessible LinkedIn pages. It does not log in to LinkedIn, bypass authentication, or circumvent access controls. LinkedIn may change its public page markup or restrict automated requests, in which case the scraper may need updating.
