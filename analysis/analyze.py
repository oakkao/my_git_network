"""
analyze.py
----------
Orchestrator script.

Steps:
  1. Load connection_cache.json produced by main_collect.py
  2. Build directed graph → extract mutual pairs → build friends dict
  3. Pick a random friend (weighted by follower count) reachable within
     MAX_HOPS hops of ROOT_USER
  4. Find the best introduction chain from that friend back to ROOT_USER
  5. Write chain_result.json  (consumed by visualize_chain.html)

Usage:
    python analyze.py [--root <username>] [--hops <int>] [--seed <int>]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from graph_builder   import build_graph, get_mutual_pairs, build_friends_dict
from graph_traversal import build_level_dict, search_friends_within_hops, find_chain
from graph_weights   import build_weighted_friends

# ---------------------------------------------------------------------------
# Defaults (override via CLI or edit here)
# ---------------------------------------------------------------------------
CACHE_FILE   = "./data/connection_cache.json"
OUTPUT_FILE  = "./outputs/chain_result.json"
ROOT_USER    = "oakkao"       # replace with your GitHub username
MAX_HOPS     = 3          # search depth for reachable friends


# ---------------------------------------------------------------------------
# Cache loader
# ---------------------------------------------------------------------------

def load_graph_data(cache_path: str) -> tuple[dict, dict, dict]:
    """
    Parse connection_cache.json into three dicts:
      following_dict  : {user: [login, ...]}
      followers_dict  : {user: [login, ...]}
      follower_counts : {user: int}   (from cached followers list length)
    """
    with open(cache_path) as f:
        cache: dict = json.load(f)

    following_dict: dict[str, list[str]] = {}
    followers_dict: dict[str, list[str]] = {}

    for username, data in cache.items():
        following_dict[username] = [u["login"] for u in data.get("following", [])]
        followers_dict[username] = [u["login"] for u in data.get("followers", [])]

    follower_counts = {u: len(v) for u, v in followers_dict.items()}
    return following_dict, followers_dict, follower_counts


# ---------------------------------------------------------------------------
# Chain result builder
# ---------------------------------------------------------------------------

def build_chain_result(
    chain: list[tuple[str, int]],
    root: str,
) -> dict:
    """
    Convert a raw chain list into a JSON-friendly dict.
    """
    nodes = [node for node, _ in chain]
    edges = [
        {"from": chain[i][0], "to": chain[i + 1][0], "weight": chain[i][1]}
        for i in range(len(chain) - 1)
    ]
    return {
        "root":   root,
        "target": nodes[0],
        "hops":   len(edges),
        "nodes":  nodes,
        "edges":  edges,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(root: str, max_hops: int, seed: int | None) -> None:
    if seed is not None:
        random.seed(seed)

    # 1. Load cache
    cache_path = Path(CACHE_FILE)
    if not cache_path.exists():
        sys.exit(f"[error] Cache file not found: {CACHE_FILE}\n"
                 "Run main_collect.py first.")

    print(f"[1/5] Loading cache from {CACHE_FILE} …")
    following_dict, followers_dict, follower_counts = load_graph_data(CACHE_FILE)

    # 2. Build graph structures
    print("[2/5] Building graph …")
    G             = build_graph(following_dict, followers_dict)
    mutual_pairs  = get_mutual_pairs(G)
    friends_dict  = build_friends_dict(mutual_pairs)

    if root not in friends_dict:
        sys.exit(f"[error] Root user '{root}' has no mutual friends in cache.\n"
                 "Check ROOT_USER or run main_collect.py with the correct username.")

    # 3. Find reachable friends & compute weights
    print(f"[3/5] Searching friends within {max_hops} hops of '{root}' …")
    reachable     = search_friends_within_hops([root], max_hops, friends_dict)
    weighted      = build_weighted_friends(friends_dict, node_subset=reachable)
    level_dict    = build_level_dict(root, friends_dict)

    print(f"      {len(reachable)} users reachable.")

    # 4. Pick a random target (weighted by follower count)
    print("[4/5] Selecting random target …")
    candidates = [u for u in reachable if u != root]
    if not candidates:
        sys.exit("[error] No reachable friends to pick from.")

    weights = [max(follower_counts.get(u, 1), 1) for u in candidates]
    target  = random.choices(candidates, weights=weights, k=1)[0]
    print(f"      Target: {target}")

    # 5. Find introduction chain
    print("[5/5] Finding best chain …")
    chain = find_chain(target, root, level_dict, weighted)

    if chain is None:
        sys.exit(f"[error] No valid chain found from '{target}' to '{root}'.")

    result = build_chain_result(chain, root)

    out_path = Path(OUTPUT_FILE)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"\n✓ Chain written to {OUTPUT_FILE}")
    print(f"  {' → '.join(result['nodes'])}  ({result['hops']} hop(s))")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyse GitHub friend chains.")
    parser.add_argument("--root",  default=ROOT_USER, help="Your GitHub username")
    parser.add_argument("--hops",  type=int, default=MAX_HOPS, help="Max hop depth")
    parser.add_argument("--seed",  type=int, default=None, help="Random seed")
    args = parser.parse_args()

    main(root=args.root, max_hops=args.hops, seed=args.seed)
