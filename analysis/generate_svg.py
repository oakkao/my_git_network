"""
generate_svg.py
---------------
Reads chain_result.json and writes chain_result.svg —

Usage:
    python generate_svg.py
"""

import json
from pathlib import Path

INPUT  = "./outputs/chain_result.json"
OUTPUT = "./outputs/chain_result.svg"

# ── layout constants ──────────────────────────────────────────────────────────
AVATAR_SIZE   = 60
NODE_W        = 90       # total column width per node
CONNECTOR_W   = 80       # width of arrow between nodes
PADDING_X     = 40
PADDING_Y     = 40
ROW_H         = 130      # height of the diagram area
LABEL_H       = 20       # height reserved below avatar for username
FONT          = "ui-monospace, SFMono-Regular, Menlo, monospace"

# ── GitHub dark-mode palette ───────────────────────────────────────────────────
BG            = "#161b22"
BORDER        = "#30363d"
ACCENT        = "#2ea043"
TEXT          = "#e6edf3"
MUTED         = "#8b949e"
LINK          = "#58a6ff"
SURFACE       = "#0d1117"


def avatar_url(login: str) -> str:
    return f"https://avatars.githubusercontent.com/{login}?s=120"


def profile_url(login: str) -> str:
    return f"https://github.com/{login}"


def truncate(s: str, max_len: int = 12) -> str:
    return s if len(s) <= max_len else s[: max_len - 1] + "..."


def build_svg(data: dict) -> str:
    nodes = data["nodes"]
    edges = data["edges"]
    root  = data["root"]
    n     = len(nodes)

    total_w = PADDING_X * 2 + NODE_W * n + CONNECTOR_W * (n - 1)
    total_h = PADDING_Y * 2 + ROW_H

    # ── open SVG ──────────────────────────────────────────────────────────────
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"',
        f'     width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}">',
        "",
        "  <!-- defs: clip path for round avatars -->",
        "  <defs>",
    ]

    for i, login in enumerate(nodes):
        cx = PADDING_X + i * (NODE_W + CONNECTOR_W) + NODE_W // 2
        cy = PADDING_Y + AVATAR_SIZE // 2
        lines.append(
            f'    <clipPath id="cp{i}">'
            f'<circle cx="{cx}" cy="{cy}" r="{AVATAR_SIZE // 2}"/>'
            f'</clipPath>'
        )

    lines += [
        "  </defs>",
        "",
        f'  <!-- background -->',
        f'  <rect width="{total_w}" height="{total_h}" rx="10" fill="{BG}" stroke="{BORDER}" stroke-width="1"/>',
        "",
    ]

    # ── connectors (drawn behind nodes) ──────────────────────────────────────
    lines.append("  <!-- connectors -->")
    for i, edge in enumerate(edges):
        # start = right edge of node i, end = left edge of node i+1
        x1 = PADDING_X + i * (NODE_W + CONNECTOR_W) + NODE_W
        x2 = x1 + CONNECTOR_W
        y  = PADDING_Y + AVATAR_SIZE // 2

        weight_label = f"x{edge['weight']}"

        lines += [
            f'  <line x1="{x1}" y1="{y}" x2="{x2 - 10}" y2="{y}"',
            f'        stroke="{ACCENT}" stroke-width="2" stroke-dasharray="4 2"/>',
            # arrowhead
            f'  <polygon points="{x2-10},{y-5} {x2},{y} {x2-10},{y+5}"',
            f'           fill="{ACCENT}"/>',
            # weight label above line
            f'  <text x="{(x1+x2)//2}" y="{y - 10}" text-anchor="middle"',
            f'        font-family="{FONT}" font-size="10" fill="{ACCENT}">{weight_label}</text>',
        ]

    # ── nodes ────────────────────────────────────────────────────────────────
    lines.append("\n  <!-- nodes -->")
    for i, login in enumerate(nodes):
        cx = PADDING_X + i * (NODE_W + CONNECTOR_W) + NODE_W // 2
        cy = PADDING_Y + AVATAR_SIZE // 2
        label_y = cy + AVATAR_SIZE // 2 + 16
        is_root = (login == root)

        lines += [
            f'  <!-- node: {login} -->',
            # avatar border circle
            f'  <circle cx="{cx}" cy="{cy}" r="{AVATAR_SIZE // 2 + 2}"',
            f'          fill="{ACCENT if is_root else BORDER}"/>',
            # avatar image (clipped to circle)
            f'  <a href="{profile_url(login)}" target="_blank">',
            f'    <image href="{avatar_url(login)}"',
            f'           x="{cx - AVATAR_SIZE // 2}" y="{cy - AVATAR_SIZE // 2}"',
            f'           width="{AVATAR_SIZE}" height="{AVATAR_SIZE}"',
            f'           clip-path="url(#cp{i})" preserveAspectRatio="xMidYMid slice"/>',
            f'  </a>',
            # username label
            f'  <a href="{profile_url(login)}" target="_blank">',
            f'    <text x="{cx}" y="{label_y}" text-anchor="middle"',
            f'          font-family="{FONT}" font-size="11"',
            f'          fill="{ACCENT if is_root else LINK}">{truncate(login)}</text>',
            f'  </a>',
        ]

        # "you" badge on root node
        if is_root:
            bx, by = cx + AVATAR_SIZE // 2 - 6, cy + AVATAR_SIZE // 2 - 6
            lines += [
                f'  <rect x="{bx - 12}" y="{by - 8}" width="24" height="12"',
                f'        rx="6" fill="{ACCENT}"/>',
                f'  <text x="{bx}" y="{by + 2}" text-anchor="middle"',
                f'        font-family="{FONT}" font-size="7" font-weight="bold"',
                f'        fill="white">YOU</text>',
            ]

    # ── footer label ─────────────────────────────────────────────────────────
    footer_y = total_h - 16
    hops     = data["hops"]
    target   = data["target"]
    summary  = f"{target}  ->  {hops} hop{'s' if hops != 1 else ''}  ->  {root}"
    note = "Edge weight = shared mutual friends + 1"
    lines += [
        "",
        f'  <text x="{total_w // 2}" y="{footer_y-18}" text-anchor="middle"',
        f'        font-family="{FONT}" font-size="14" fill="{MUTED}">{summary}</text>',
        f'  <text x="{total_w // 2}" y="{footer_y}" text-anchor="middle"',
        f'        font-family="{FONT}" font-size="10" fill="{MUTED}">{note}</text>',
    ]

    lines.append("</svg>")
    return "\n".join(lines)


def main() -> None:
    data = json.loads(Path(INPUT).read_text())
    svg  = build_svg(data)
    Path(OUTPUT).write_text(svg)
    print(f"Written {OUTPUT}  ({len(data['nodes'])} nodes, {data['hops']} hops)")


if __name__ == "__main__":
    main()
