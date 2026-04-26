---
name: web-search
description: "Live web search via DuckDuckGo API — no API key, no pip install required. Use for searching current information, documentation, news, or any web content during task execution."
user-invocable: true
risk: safe
---

# Web Search

Live web search using DuckDuckGo's free API — zero configuration, no API key required.

## When to Use
- Looking up current documentation, library versions, or changelogs
- Searching for error messages or stack traces
- Researching technologies, frameworks, or best practices
- Finding code examples or official guides

## Quick Usage

```python
import urllib.request
import urllib.parse
import json

def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Search the web using DuckDuckGo's JSON API."""
    encoded = urllib.parse.quote(query)
    url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_redirect=1"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read())
    
    results = []
    # Instant answer
    if data.get('AbstractText'):
        results.append({
            'title': data.get('Heading', 'Summary'),
            'snippet': data['AbstractText'],
            'url': data.get('AbstractURL', '')
        })
    # Related topics
    for topic in data.get('RelatedTopics', [])[:max_results]:
        if 'Text' in topic:
            results.append({
                'title': topic.get('Text', '')[:60],
                'snippet': topic.get('Text', ''),
                'url': topic.get('FirstURL', '')
            })
    return results

# Usage
results = web_search("FastAPI dependency injection tutorial")
for r in results:
    print(f"[{r['title']}] {r['url']}")
    print(f"  {r['snippet'][:120]}\n")
```

## Shell One-liner

```bash
# Quick search via curl
query="python asyncio best practices"
curl -s "https://api.duckduckgo.com/?q=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$query'))")&format=json" | python3 -m json.tool | grep -A2 '"AbstractText"'
```

## Alternative: Brave Search API

```python
import requests

def brave_search(query: str, count: int = 5) -> list[dict]:
    """Requires BRAVE_API_KEY env var (free tier: 2000 queries/month)."""
    resp = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={"Accept": "application/json", "X-Subscription-Token": os.environ["BRAVE_API_KEY"]},
        params={"q": query, "count": count}
    )
    return [
        {"title": r["title"], "url": r["url"], "snippet": r.get("description", "")}
        for r in resp.json().get("web", {}).get("results", [])
    ]
```

## Best Practices
- Be specific in queries — include version numbers, framework names
- For documentation, prefix query with "site:docs.example.com"
- Check `AbstractURL` for authoritative sources (Wikipedia, official docs)
- For code search: add "example", "tutorial", or "github" to query
- Rate limit: add `time.sleep(1)` between rapid searches to be respectful
