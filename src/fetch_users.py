import requests
import time

def _get_all_users(endpoint, token=None):
    """
    Generic paginated fetcher for any GitHub user-list endpoint.
    Handles rate limiting with X-RateLimit-Reset + exponential backoff.
    """
    all_users = []
    page = 1
    MAX_RETRIES = 5

    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    while True:
        params = {"per_page": 100, "page": page}
        retries = 0

        while retries < MAX_RETRIES:
            response = requests.get(endpoint, headers=headers, params=params)

            if response.status_code == 200:
                break

            if response.status_code in (403, 429):
                reset_ts = response.headers.get("X-RateLimit-Reset")
                if reset_ts:
                    wait = max(int(reset_ts) - int(time.time()), 0) + 5
                    print(f"Rate limited. Waiting {wait}s for reset...")
                else:
                    wait = (2 ** retries) * 10
                    print(f"Rate limited. Backing off {wait}s (retry {retries+1}/{MAX_RETRIES})...")
                time.sleep(wait)
                retries += 1
                continue

            print(f"Error {response.status_code} for {endpoint}: {response.text}")
            return all_users

        else:
            print(f"Failed after {MAX_RETRIES} retries. Aborting.")
            return all_users

        data = response.json()
        if not data:
            break

        all_users.extend(data)
        print(f"  Page {page} -> {len(data)} users (total: {len(all_users)})")

        remaining = int(response.headers.get("X-RateLimit-Remaining", 1))
        if remaining < 5:
            reset_ts = response.headers.get("X-RateLimit-Reset")
            wait = max(int(reset_ts) - int(time.time()), 0) + 2
            print(f"Near rate limit ({remaining} left). Pausing {wait}s...")
            time.sleep(wait)
        else:
            time.sleep(0.5)

        page += 1

    return all_users


def get_all_following(username, token=None):
    endpoint = f"https://api.github.com/users/{username}/following"
    return _get_all_users(endpoint, token=token)


def get_all_followers(username, token=None):
    endpoint = f"https://api.github.com/users/{username}/followers"
    return _get_all_users(endpoint, token=token)