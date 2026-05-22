"""Build prompt and greeting overrides from an X handle."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from typing import Any


BASE_URL = "https://api.x.com/2"
TOKEN_ENV_VARS = ("X_API_BEARER_TOKEN", "X_BEARER_TOKEN", "BEARER_TOKEN", "TWITTER_BEARER_TOKEN")
DEFAULT_USER_FIELDS = [
    "created_at",
    "description",
    "profile_image_url",
    "public_metrics",
    "url",
    "username",
    "verified",
]
DEFAULT_TIMELINE_TWEET_FIELDS = [
    "created_at",
    "in_reply_to_user_id",
    "referenced_tweets",
    "text",
]
DEFAULT_MAX_RESULTS = 15
DEFAULT_ANALYSIS_POSTS = 12
DEFAULT_EXAMPLES = 5
DEFAULT_MIN_POST_LENGTH = 25
DEFAULT_MAX_EXAMPLE_CHARS = 220
DEFAULT_MAX_PROMPT_CHARS = 1400

STOPWORDS = {
    "a", "about", "after", "all", "also", "am", "an", "and", "any", "are", "around", "as", "at",
    "back", "be", "because", "been", "before", "being", "between", "both", "but", "by", "can",
    "could", "did", "do", "does", "doing", "don't", "didn't", "down", "each", "even", "few",
    "first", "for", "from", "get", "going", "good", "got", "had", "has", "have", "he", "her",
    "here", "him", "his", "how", "i", "i've", "if", "in", "into", "is", "it", "it's", "its",
    "just", "know", "like", "lot", "make", "many", "more", "most", "much", "my", "new", "no",
    "not", "now", "of", "on", "one", "only", "or", "our", "out", "over", "really", "same", "say",
    "see", "should", "so", "some", "still", "such", "than", "that", "the", "their", "them", "then",
    "there", "there's", "these", "they", "they're", "thing", "think", "this", "those", "through",
    "time", "to", "too", "true", "up", "us", "use", "very", "was", "way", "we", "we're", "well",
    "were", "what", "when", "which", "who", "will", "with", "would", "years", "you", "your",
}

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_'-]{2,}")
WHITESPACE_RE = re.compile(r"\s+")
URL_RE = re.compile(r"https?://\S+|t\.co/\S+")
EMOJI_HINT_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")
PROFILE_SIZE_SUFFIX_RE = re.compile(r"_(normal|bigger|mini)(\.[A-Za-z0-9]+)$")


class XApiError(RuntimeError):
    """Raised when the X API returns an error or is unavailable."""


def clean_text(text: str) -> str:
    return WHITESPACE_RE.sub(" ", (text or "").replace("\n", " ")).strip()


def shorten_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def ensure_sentence(text: str) -> str:
    cleaned = clean_text(text)
    if not cleaned:
        return ""
    if cleaned[-1] in ".!?":
        return cleaned
    return cleaned + "."


def format_series(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def profile_image_original_url(url: str | None) -> str | None:
    if not url:
        return None
    return PROFILE_SIZE_SUFFIX_RE.sub(r"\2", url)


def load_token(explicit_token: str | None = None) -> str | None:
    if explicit_token:
        return explicit_token
    for name in TOKEN_ENV_VARS:
        value = os.getenv(name)
        if value:
            return value
    return None


def build_url(path: str, params: dict[str, Any] | None = None) -> str:
    query = urllib.parse.urlencode(
        [(key, value) for key, value in (params or {}).items() if value not in (None, "", [])]
    )
    return f"{BASE_URL}{path}?{query}" if query else f"{BASE_URL}{path}"


def format_http_error(status_code: int, raw_body: str, url: str) -> str:
    details = raw_body.strip()
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        payload = None

    if isinstance(payload, dict):
        if payload.get("title") and payload.get("detail"):
            details = f"{payload['title']}: {payload['detail']}"
        elif payload.get("errors"):
            details = json.dumps(payload["errors"], indent=2)

    return f"HTTP {status_code} for {url}\n{details}"


def http_get_json(token: str, path: str, params: dict[str, Any] | None = None, *, timeout_seconds: float = 8.0) -> dict[str, Any]:
    url = build_url(path, params)
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "simple-backend-x-profile/1.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        raise XApiError(format_http_error(exc.code, raw_body, url)) from exc
    except urllib.error.URLError as exc:
        raise XApiError(f"Request to {url} failed: {exc.reason}") from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise XApiError(f"Non-JSON response from {url}: {body[:300]}") from exc


def lookup_user(token: str, username: str, *, timeout_seconds: float) -> dict[str, Any]:
    return http_get_json(
        token,
        f"/users/by/username/{urllib.parse.quote(username, safe='')}",
        {"user.fields": ",".join(DEFAULT_USER_FIELDS)},
        timeout_seconds=timeout_seconds,
    )


def fetch_user_timeline(token: str, user_id: str, *, timeout_seconds: float, max_results: int) -> dict[str, Any]:
    return http_get_json(
        token,
        f"/users/{user_id}/tweets",
        {
            "max_results": max_results,
            "exclude": "retweets",
            "tweet.fields": ",".join(DEFAULT_TIMELINE_TWEET_FIELDS),
        },
        timeout_seconds=timeout_seconds,
    )


def is_retweet(post: dict) -> bool:
    if any(item.get("type") == "retweeted" for item in post.get("referenced_tweets") or []):
        return True
    return clean_text(post.get("text", "")).startswith("RT @")


def is_reply(post: dict) -> bool:
    if post.get("in_reply_to_user_id"):
        return True
    return clean_text(post.get("text", "")).startswith("@")


def collect_posts(timeline_payload: dict, *, min_post_length: int) -> list[dict]:
    posts = []
    for post in timeline_payload.get("data") or []:
        text = clean_text(post.get("text", ""))
        if not text or len(text) < min_post_length or is_retweet(post):
            continue
        posts.append(
            {
                "id": post.get("id"),
                "created_at": post.get("created_at"),
                "text": text,
                "is_reply": is_reply(post),
            }
        )
    return posts


def classify_length(avg_length: float) -> str:
    if avg_length < 70:
        return "short and punchy"
    if avg_length < 140:
        return "medium-length and compact"
    return "longer and more detailed"


def classify_energy(exclamation_rate: float, emoji_rate: float) -> str:
    if exclamation_rate > 0.18 or emoji_rate > 0.12:
        return "high-energy and expressive"
    if exclamation_rate > 0.06 or emoji_rate > 0.04:
        return "friendly and upbeat"
    return "measured and restrained"


def classify_links(link_rate: float) -> str:
    if link_rate > 0.45:
        return "often shares links or references external material"
    if link_rate > 0.15:
        return "occasionally links out to supporting material"
    return "rarely relies on links"


def classify_structure(question_rate: float, mention_rate: float) -> str:
    if mention_rate > 0.25:
        return "frequently addresses other accounts directly"
    if question_rate > 0.15:
        return "often frames points as questions or prompts"
    return "usually makes direct statements"


def detect_calls_to_action(posts: list[dict]) -> bool:
    markers = ("get started", "learn more", "check out", "read more", "join", "try", "build", "follow")
    lowered = " ".join(post["text"].lower() for post in posts)
    return any(marker in lowered for marker in markers)


def top_terms(posts: list[dict], limit: int) -> list[str]:
    counter: Counter[str] = Counter()
    for post in posts:
        for token in TOKEN_RE.findall(post["text"].lower()):
            if token in STOPWORDS or token.startswith("http") or token.startswith("@") or token.isdigit():
                continue
            counter[token] += 1
    ranked = [(term, count) for term, count in counter.most_common() if count > 1]
    return [term for term, _ in ranked[:limit]]


def analyze_posts(posts: list[dict]) -> dict:
    if not posts:
        return {
            "post_count": 0,
            "avg_length": 0.0,
            "length_style": "unknown",
            "energy_style": "unknown",
            "link_style": "unknown",
            "structure_style": "unknown",
            "calls_to_action": False,
            "top_terms": [],
            "reply_rate": 0.0,
        }

    texts = [post["text"] for post in posts]
    avg_length = sum(len(text) for text in texts) / len(texts)
    question_rate = sum("?" in text for text in texts) / len(texts)
    exclamation_rate = sum("!" in text for text in texts) / len(texts)
    link_rate = sum(bool(URL_RE.search(text)) for text in texts) / len(texts)
    mention_rate = sum("@" in text for text in texts) / len(texts)
    emoji_rate = sum(bool(EMOJI_HINT_RE.search(text)) for text in texts) / len(texts)
    reply_rate = sum(post["is_reply"] for post in posts) / len(posts)

    return {
        "post_count": len(posts),
        "avg_length": round(avg_length, 1),
        "length_style": classify_length(avg_length),
        "energy_style": classify_energy(exclamation_rate, emoji_rate),
        "link_style": classify_links(link_rate),
        "structure_style": classify_structure(question_rate, mention_rate),
        "calls_to_action": detect_calls_to_action(posts),
        "top_terms": top_terms(posts, limit=10),
        "reply_rate": round(reply_rate, 2),
    }


def sample_examples(posts: list[dict], count: int) -> list[dict]:
    preferred = [post for post in posts if not post["is_reply"]]
    ordered = preferred + [post for post in posts if post["is_reply"]]
    if len(ordered) <= count:
        return ordered
    if count <= 1:
        return [ordered[0]]
    step = max(1, len(ordered) // count)
    return [ordered[index] for index in range(0, len(ordered), step)][:count]


def clean_example_text(text: str, max_chars: int) -> str:
    return shorten_text(clean_text(URL_RE.sub("", text)), max_chars)


def render_prompt(user: dict, stats: dict, examples: list[dict], *, max_prompt_chars: int) -> str:
    name = user.get("name") or user.get("username") or "Unknown"
    username = user.get("username") or "unknown"
    bio = clean_text(user.get("description") or "")
    verified = "verified" if user.get("verified") else "not verified"
    followers = ((user.get("public_metrics") or {}).get("followers_count"))

    lines = [
        f"You are writing as {name} (@{username}) on X.",
        "",
        "Identity and context:",
        f"- Account bio: {bio or 'No bio available.'}",
        f"- Account status: {verified}.",
    ]
    if followers is not None:
        lines.append(f"- Audience scale: about {followers} followers.")
    lines.extend(
        [
            "",
            "Style constraints:",
            f"- Use a {stats['length_style']} sentence length profile.",
            f"- Keep the tone {stats['energy_style']}.",
            f"- The account {stats['structure_style']}.",
            f"- The account {stats['link_style']}.",
        ]
    )
    if stats["reply_rate"] > 0.5:
        lines.append("- Replies are common, so direct responses to other users are in-character.")
    elif stats["reply_rate"] < 0.2:
        lines.append("- Most posts stand on their own rather than acting as replies.")
    if stats["calls_to_action"]:
        lines.append("- Include clear calls to action when appropriate.")
    else:
        lines.append("- Prefer statements over overt calls to action.")
    if stats["top_terms"]:
        lines.append(f"- Reuse this topic vocabulary when relevant: {', '.join(stats['top_terms'][:8])}.")
    lines.extend(
        [
            "- Keep posts aligned with the bio and recent subject matter.",
            "- Do not mention this analysis or say you are imitating someone.",
            "",
            "Representative examples:",
        ]
    )
    tail_lines = [
        "",
        "Task:",
        "Write a new X post in this voice. Keep it original, concise, and plausible for this account.",
    ]

    prompt_lines = list(lines)
    for example in examples:
        candidate_lines = prompt_lines + [f"- Example: {example['text']}"] + tail_lines
        if len("\n".join(candidate_lines)) > max_prompt_chars:
            break
        prompt_lines.append(f"- Example: {example['text']}")

    return shorten_text("\n".join(prompt_lines + tail_lines), max_prompt_chars)


def build_greeting(user: dict, stats: dict) -> str:
    name = user.get("name") or user.get("username") or "there"
    bio = ensure_sentence(user.get("description") or "")
    topics = [term for term in stats.get("top_terms", []) if len(term) >= 5][:3]
    reply_heavy = stats.get("reply_rate", 0) > 0.5

    parts = [f"Hi, I'm {name}."]
    if bio:
        parts.append(bio)
    elif topics and not reply_heavy:
        parts.append(f"I usually post about {format_series(topics)}.")
    else:
        parts.append("I share thoughts, reactions, and observations on X.")

    if reply_heavy:
        parts.append("I often respond directly and conversationally.")
    elif stats.get("length_style") == "longer and more detailed":
        parts.append("I tend to write in a more detailed, reflective style.")
    elif stats.get("length_style") == "short and punchy":
        parts.append("I tend to keep things short and direct.")

    return " ".join(parts)


def build_profile_overrides_from_handle(
    handle: str,
    *,
    bearer_token: str | None = None,
    timeout_seconds: float = 8.0,
) -> dict[str, Any]:
    token = load_token(bearer_token)
    if not token:
        raise XApiError("X_API_BEARER_TOKEN is required when xhandle is provided.")

    username = (handle or "").strip().lstrip("@")
    if not username:
        raise XApiError("xhandle must not be empty.")

    user_lookup = lookup_user(token, username, timeout_seconds=timeout_seconds)
    user = user_lookup.get("data") or {}
    user_id = user.get("id")
    if not user_id:
        raise XApiError(f"Could not resolve X handle @{username}.")

    timeline = fetch_user_timeline(
        token,
        str(user_id),
        timeout_seconds=timeout_seconds,
        max_results=DEFAULT_MAX_RESULTS,
    )
    posts = collect_posts(timeline, min_post_length=DEFAULT_MIN_POST_LENGTH)[:DEFAULT_ANALYSIS_POSTS]
    stats = analyze_posts(posts)
    avatar_url_normal = user.get("profile_image_url")
    avatar_id = profile_image_original_url(avatar_url_normal)
    examples = []
    for example in sample_examples(posts, DEFAULT_EXAMPLES):
        cleaned = clean_example_text(example["text"], DEFAULT_MAX_EXAMPLE_CHARS)
        if cleaned:
            examples.append({**example, "text": cleaned})

    return {
        "handle": username,
        "username": user.get("username"),
        "display_name": user.get("name"),
        "avatar_id": avatar_id,
        "avatar_url": avatar_id,
        "avatar_url_normal": avatar_url_normal,
        "user": user,
        "analysis": stats,
        "prompt": render_prompt(user, stats, examples, max_prompt_chars=DEFAULT_MAX_PROMPT_CHARS),
        "greeting": build_greeting(user, stats),
    }
