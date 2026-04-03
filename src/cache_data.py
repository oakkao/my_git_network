import os
import json
from datetime import datetime, timezone
from fetch_users import get_all_following, get_all_followers

CACHE_FILE = "./data/connection_cache.json"
CACHE_TTL_DAYS = 7

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def is_cache_fresh(cache, username):
    if username not in cache:
        return False
    cached_at = cache[username].get("cached_at")
    if not cached_at:
        return False
    age_days = (datetime.now(timezone.utc) - datetime.fromisoformat(cached_at)).days
    return age_days < CACHE_TTL_DAYS


KEEP_FIELDS = {"login", "id", "type"}
MAX_FOLLOWING = 1000
MAX_FOLLOWERS = 1000  # optional — add if you want the same guard for followers

def slim_user(user: dict) -> dict:
    return {k: user[k] for k in KEEP_FIELDS if k in user}

def _get_cached(username, cache, key, fetch_fn, token=None, count=None, max_count=None):
    """
    Generic cached fetcher for following or followers.
    
    Args:
        key:      "following" or "followers" — which cache sub-key to use
        fetch_fn: get_all_following or get_all_followers
        count:    known count from parent's slim_user data
        max_count: skip threshold (None = no limit)
    """
    cached = cache.get(username, {})

    # Fresh cache check per key
    cached_at = cached.get(f"{key}_cached_at")
    if cached_at:
        age_days = (datetime.now(timezone.utc) - datetime.fromisoformat(cached_at)).days
        if age_days < CACHE_TTL_DAYS:
            print(f"\t[cache] {username} {key} (skipping fetch)")
            return cached.get(key, [])

    # Count guard
    if max_count is not None and count is not None and count > max_count:
        print(f"\t[skip]  {username} has {count} {key} — too many")
        cache.setdefault(username, {})[key] = []
        cache[username][f"{key}_cached_at"] = datetime.now(timezone.utc).isoformat()
        cache[username][f"{key}_skipped"] = True
        cache[username][f"{key}_reason"] = f"{key} count {count} exceeds {max_count}"
        save_cache(cache)
        return []

    print(f"\t[fetch] {username} {key}")
    result = fetch_fn(username, token=token)
    cache.setdefault(username, {})[key] = [slim_user(u) for u in result]
    cache[username][f"{key}_cached_at"] = datetime.now(timezone.utc).isoformat()
    cache[username][f"{key}_skipped"] = False
    save_cache(cache)
    return cache[username][key]


def get_all_following_cached(username, cache, token=None, following_count=None):
    return _get_cached(
        username, cache,
        key="following",
        fetch_fn=get_all_following,
        token=token,
        count=following_count,
        max_count=MAX_FOLLOWING
    )

def get_all_followers_cached(username, cache, token=None, followers_count=None):
    return _get_cached(
        username, cache,
        key="followers",
        fetch_fn=get_all_followers,
        token=token,
        count=followers_count,
        max_count=MAX_FOLLOWERS
    )