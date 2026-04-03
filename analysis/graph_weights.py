"""
graph_weights.py
----------------
Computes edge weights for the friends graph.

Weight definition
-----------------
  weight(u, v) = |mutual_friends(u, v)| + 1

The +1 ensures every direct friend has weight ≥ 1 even when they share no
other mutual friends (they at least "know" each other directly).
"""

from __future__ import annotations


def mutual_friends(
    user_a: str,
    user_b: str,
    friends_dict: dict[str, list[str]],
) -> list[str]:
    """Return users who are friends with *both* user_a and user_b."""
    set_a = set(friends_dict.get(user_a, []))
    set_b = set(friends_dict.get(user_b, []))
    return list(set_a & set_b)


def build_weighted_friends(
    friends_dict: dict[str, list[str]],
    node_subset: list[str] | None = None,
) -> dict[str, dict[str, int]]:
    """
    Build a weighted adjacency dict restricted to *node_subset*.

    Args:
        friends_dict: undirected adjacency {user: [friends]}
        node_subset : if given, only include nodes in this collection.
                      Defaults to all nodes in friends_dict.

    Returns:
        {user: {friend: weight}}  where weight = |mutual_friends| + 1
    """
    active: set[str] = set(node_subset) if node_subset is not None else set(friends_dict.keys())

    weighted: dict[str, dict[str, int]] = {}

    for user in active:
        neighbours = list(set(friends_dict.get(user, [])) & active)
        weighted[user] = {
            friend: len(mutual_friends(user, friend, friends_dict)) + 1
            for friend in neighbours
        }

    return weighted
