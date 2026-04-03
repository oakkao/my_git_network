import os
from cache_data import load_cache, save_cache, get_all_followers_cached, get_all_following_cached

def collect_n_hop_graph(root_username, search_level=2, token=None):
    cache = load_cache()
    
    # Root user has no parent data, so counts are None (always fetch)
    user_level_list = [[{"login": root_username, "following": None, "followers": None}]]
    following_dict = {}
    followers_dict = {}

    for level in range(search_level):
        print(f"\nSearch level: {level}")
        next_user_level_list = []

        for user in user_level_list[level]:
            username = user["login"]
            following_count = user.get("following")
            followers_count = user.get("followers")

            # Fetch both directions
            following_result = get_all_following_cached(
                username, cache, token=token,
                following_count=following_count
            )
            followers_result = get_all_followers_cached(
                username, cache, token=token,
                followers_count=followers_count
            )

            following_dict[username] = [u["login"] for u in following_result]
            followers_dict[username] = [u["login"] for u in followers_result]

            # Queue both following and followers for next level
            next_user_level_list.extend(following_result)
            next_user_level_list.extend(followers_result)

        # Deduplicate against all already-seen users across all levels
        already_seen = {
            u["login"]
            for level_users in user_level_list
            for u in level_users
        }
        seen = set()
        next_deduped = []
        for u in next_user_level_list:
            if u["login"] not in already_seen and u["login"] not in seen:
                seen.add(u["login"])
                next_deduped.append(u)

        user_level_list.append(next_deduped)
        print(f"  → {len(next_deduped)} new users queued for level {level + 1}")

    save_cache(cache)
    return following_dict, followers_dict, user_level_list


# --- Run ---
TOKEN = os.environ.get("GITHUB_TOKEN")
following_dict, followers_dict, user_level_list = collect_n_hop_graph(
    "oakkao", search_level=1, token=TOKEN
)