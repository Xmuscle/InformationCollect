"""
Linux.do Sensor - 抓取 linux.do 每日热门帖子
linux.do 是基于 Discourse 的技术社区，使用 Discourse JSON API
注意：linux.do 有 TLS 指纹检测，httpx 会被 403，需要用 curl 抓取
"""

import json
import logging
import subprocess

logger = logging.getLogger(__name__)

LINUXDO_API_URL = "https://linux.do/top.json?period=daily"
LINUXDO_BASE_URL = "https://linux.do"


def _fetch_json_via_curl(url: str, timeout: int = 15) -> dict:
    """Use curl to fetch JSON, bypassing TLS fingerprint detection."""
    result = subprocess.run(
        [
            "curl", "-s", "-f",
            "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "-H", "Accept: application/json",
            url,
        ],
        capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed (exit {result.returncode}): {result.stderr.strip()}")
    return json.loads(result.stdout)


def fetch_linuxdo(limit: int = 10) -> list[dict]:
    """
    Fetch daily hot topics from linux.do via Discourse JSON API.

    Returns:
        List of dicts with keys: title, url, heat, time, category
    """
    try:
        data = _fetch_json_via_curl(LINUXDO_API_URL)
    except Exception as e:
        logger.warning(f"linux.do 抓取失败: {e}")
        return []

    topics = data.get("topic_list", {}).get("topics", [])
    results = []

    for t in topics[:limit]:
        title = t.get("title", "")
        topic_id = t.get("id", "")
        slug = t.get("slug", "topic")
        views = t.get("views", 0)
        like_count = t.get("like_count", 0)
        posts_count = t.get("posts_count", 0)

        url = f"{LINUXDO_BASE_URL}/t/{slug}/{topic_id}"
        heat = f"{views} views / {like_count} likes / {posts_count} replies"

        results.append({
            "title": title,
            "url": url,
            "heat": heat,
            "time": t.get("created_at", ""),
            "category": "linux.do",
        })

    logger.info(f"linux.do: fetched {len(results)} topics")
    return results


if __name__ == "__main__":
    items = fetch_linuxdo(limit=5)
    for item in items:
        print(f"  {item['title']}")
        print(f"    {item['url']}")
        print(f"    {item['heat']}")
        print()
