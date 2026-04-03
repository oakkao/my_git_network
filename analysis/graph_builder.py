"""
graph_builder.py
----------------
Builds a directed NetworkX graph from following/followers dicts,
extracts mutual (bidirectional) pairs, and assembles an undirected
friends dict for downstream traversal.
"""

import networkx as nx


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph(following_dict: dict[str, list[str]],
                followers_dict: dict[str, list[str]]) -> nx.DiGraph:
    """
    Build a directed graph from following/followers dicts.

    Each edge carries a ``mutual`` attribute:
      - True  → both a→b and b→a exist  (GitHub "friends")
      - False → one-way only
    """
    G = nx.DiGraph()

    all_users = set(following_dict.keys()) | set(followers_dict.keys())
    G.add_nodes_from(all_users)

    for user, targets in following_dict.items():
        for target in targets:
            G.add_edge(user, target, mutual=False)

    # Second pass — mark mutual edges
    for u, v in list(G.edges()):
        if G.has_edge(v, u):
            G[u][v]["mutual"] = True
            G[v][u]["mutual"] = True

    return G


def get_mutual_pairs(G: nx.DiGraph) -> list[tuple[str, str]]:
    """
    Return a deduplicated, sorted list of mutual (a, b) pairs where a < b
    lexicographically.
    """
    pairs: set[tuple[str, str]] = set()
    for u, v, data in G.edges(data=True):
        if data.get("mutual"):
            pairs.add(tuple(sorted([u, v])))  # type: ignore[arg-type]
    return sorted(pairs)


# ---------------------------------------------------------------------------
# Friends dict  (undirected adjacency from mutual pairs)
# ---------------------------------------------------------------------------

def build_friends_dict(mutual_pairs: list[tuple[str, str]]) -> dict[str, list[str]]:
    """
    Convert a list of mutual pairs into an undirected adjacency dict.

    Returns:
        {username: [sorted list of mutual friends]}
    """
    friends: dict[str, list[str]] = {}

    for a, b in mutual_pairs:
        friends.setdefault(a, []).append(b)
        friends.setdefault(b, []).append(a)

    # Keep lists sorted for deterministic output
    for user in friends:
        friends[user] = sorted(friends[user])

    return friends
