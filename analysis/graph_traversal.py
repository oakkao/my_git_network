"""
graph_traversal.py
------------------
BFS-based traversal helpers:
  - build a hop-level dict rooted at any user
  - collect all friends reachable within N hops
  - find the highest-quality introduction chain between two users
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# BFS helpers
# ---------------------------------------------------------------------------

def build_level_dict(root: str, friends_dict: dict[str, list[str]]) -> dict[str, int]:
    """
    BFS from *root* over the undirected friends graph.

    Returns:
        {username: hop_distance_from_root}   (root itself → 0)
    """
    level_dict: dict[str, int] = {}
    visited: set[str] = {root}
    current_frontier: set[str] = {root}
    level = 0

    while current_frontier:
        next_frontier: set[str] = set()

        for user in current_frontier:
            level_dict[user] = level
            for friend in friends_dict.get(user, []):
                if friend not in visited:
                    visited.add(friend)
                    next_frontier.add(friend)

        current_frontier = next_frontier
        level += 1

    return level_dict


def search_friends_within_hops(
    seeds: list[str],
    max_hops: int,
    friends_dict: dict[str, list[str]],
) -> list[str]:
    """
    Return every user reachable from *seeds* within *max_hops* hops
    (seeds themselves are always included).
    """
    visited: set[str] = set(seeds)
    frontier: set[str] = set(seeds)

    for _ in range(max_hops):
        next_frontier: set[str] = set()
        for user in frontier:
            for friend in friends_dict.get(user, []):
                if friend not in visited:
                    visited.add(friend)
                    next_frontier.add(friend)
        frontier = next_frontier

    return list(visited)


# ---------------------------------------------------------------------------
# Chain finder
# ---------------------------------------------------------------------------

def find_chain(
    user_a: str,
    user_b: str,
    level_dict: dict[str, int],
    weighted_friends_dict: dict[str, dict[str, int]],
) -> list[tuple[str, int]] | None:
    """
    Find the best introduction path from *user_a* → *user_b* where every
    hop strictly descends in BFS level (rooted at *user_b*).

    Scoring priority:
      1. Maximise the bottleneck weight (weakest link along the path).
      2. Maximise the total weight (tiebreaker).

    Args:
        user_a               : start node (higher level number)
        user_b               : end node   (level 0 = root)
        level_dict           : {username: hop_level} rooted at user_b
        weighted_friends_dict: {u: {v: weight}} — omitted key = no edge

    Returns:
        List of ``(node, weight_to_next)`` tuples ending at *user_b*, e.g.::

            [("alice", 5), ("carol", 3), ("me", 0)]

        The last entry always carries weight 0.
        Returns ``None`` when no valid strict-descent path exists.
    """
    if user_a == user_b:
        return [(user_a, 0)]

    if user_a not in level_dict or user_b not in level_dict:
        return None

    level_a = level_dict[user_a]
    level_b = level_dict[user_b]

    if level_a <= level_b:
        return None  # user_a must sit at a higher level than user_b

    INF = float("inf")
    # dp[node] = (bottleneck, total_sum, path_so_far)
    dp: dict[str, tuple] = {user_a: (INF, 0, [])}
    frontier = [user_a]

    for lvl in range(level_a, 0, -1):
        candidates: dict[str, tuple] = {}

        for node in frontier:
            node_bn, node_sum, node_path = dp[node]
            for neighbor, weight in weighted_friends_dict.get(node, {}).items():
                if level_dict.get(neighbor) != lvl - 1:
                    continue

                new_bn   = min(weight, node_bn)
                new_sum  = weight + node_sum
                new_path = node_path + [(node, weight)]

                current = candidates.get(neighbor)
                if current is None or (new_bn, new_sum) > (current[0], current[1]):
                    candidates[neighbor] = (new_bn, new_sum, new_path)

        dp.update(candidates)
        frontier = list(candidates.keys())

    if user_b not in dp:
        return None

    return dp[user_b][2] + [(user_b, 0)]
