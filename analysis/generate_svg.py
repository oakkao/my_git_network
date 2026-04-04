"""
generate_svg.py
---------------
Reads chain_result.json and writes chain_result.svg —
a fully self-contained SVG with avatars embedded as base64 data URIs.

Usage:
    python generate_svg.py
"""

import base64
import json
import urllib.request
import urllib.error
from pathlib import Path

INPUT  = "./outputs/chain_result.json"
OUTPUT = "./outputs/chain_result.svg"

# ── layout ────────────────────────────────────────────────────────────────────
AVATAR_SIZE  = 60
NODE_W       = 90
CONNECTOR_W  = 90
PADDING_X    = 40
PADDING_Y    = 44
FOOTER_H     = 28
LABEL_H      = 22
FONT         = "ui-monospace, SFMono-Regular, Menlo, monospace"

# ── palette (GitHub dark) ─────────────────────────────────────────────────────
BG     = "#161b22"
BORDER = "#30363d"
ACCENT = "#2ea043"
MUTED  = "#8b949e"
LINK   = "#58a6ff"


# ── avatar fetching ───────────────────────────────────────────────────────────

def fetch_avatar_b64(login: str, size: int = AVATAR_SIZE * 2):
    """
    Download the GitHub avatar for *login* and return a base64 data URI,
    or None if the request fails.
    """
    url = f"https://avatars.githubusercontent.com/{login}?s={size}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "generate_svg/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw   = resp.read()
            ctype = resp.headers.get_content_type() or "image/jpeg"
            b64   = base64.b64encode(raw).decode()
            return f"data:{ctype};base64,{b64}"
    except urllib.error.URLError as exc:
        print(f"  [warn] could not fetch avatar for {login}: {exc}")
        return None


def placeholder_b64() -> str:
    """1x1 transparent PNG as a fallback when the avatar fetch fails."""
    RAW = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return "data:image/png;base64," + base64.b64encode(RAW).decode()


# ── helpers ───────────────────────────────────────────────────────────────────

def truncate(s: str, max_len: int = 11) -> str:
    return s if len(s) <= max_len else s[:max_len - 1] + "…"


# ── SVG builder ───────────────────────────────────────────────────────────────

def build_svg(data: dict, avatars: dict[str, str]) -> str:
    nodes   = data["nodes"]
    edges   = data["edges"]
    root    = data["root"]
    n       = len(nodes)

    content_h = PADDING_Y + AVATAR_SIZE + LABEL_H
    total_w   = PADDING_X * 2 + NODE_W * n + CONNECTOR_W * (n - 1)
    total_h   = content_h + FOOTER_H

    out: list[str] = []

    def ln(s: str = "") -> None:
        out.append(s)

    # ── header ────────────────────────────────────────────────────────────────
    ln(f'<svg xmlns="http://www.w3.org/2000/svg"')
    ln(f'     width="{total_w}" height="{total_h}"')
    ln(f'     viewBox="0 0 {total_w} {total_h}">')
    ln()

    # ── defs: one circular clip per node ─────────────────────────────────────
    ln("  <defs>")
    for i in range(n):
        cx = PADDING_X + i * (NODE_W + CONNECTOR_W) + NODE_W // 2
        cy = PADDING_Y + AVATAR_SIZE // 2
        ln(f'    <clipPath id="cp{i}">'
           f'<circle cx="{cx}" cy="{cy}" r="{AVATAR_SIZE // 2}"/>'
           f'</clipPath>')
    ln("  </defs>")
    ln()

    # ── background ────────────────────────────────────────────────────────────
    ln(f'  <rect width="{total_w}" height="{total_h}" rx="10"'
       f' fill="{BG}" stroke="{BORDER}" stroke-width="1"/>')
    ln()

    # ── connectors ────────────────────────────────────────────────────────────
    for i, edge in enumerate(edges):
        x1 = PADDING_X + i * (NODE_W + CONNECTOR_W) + NODE_W
        x2 = x1 + CONNECTOR_W
        y  = PADDING_Y + AVATAR_SIZE // 2
        mx = (x1 + x2) // 2

        ln(f'  <line x1="{x1}" y1="{y}" x2="{x2 - 10}" y2="{y}"'
           f' stroke="{ACCENT}" stroke-width="1.5" stroke-dasharray="4 2"/>')
        ln(f'  <polygon points="{x2-10},{y-5} {x2},{y} {x2-10},{y+5}"'
           f' fill="{ACCENT}"/>')
        ln(f'  <text x="{mx}" y="{y - 10}" text-anchor="middle"'
           f' font-family="{FONT}" font-size="10" fill="{ACCENT}">x{edge["weight"]}</text>')

    ln()

    # ── nodes ─────────────────────────────────────────────────────────────────
    for i, login in enumerate(nodes):
        cx      = PADDING_X + i * (NODE_W + CONNECTOR_W) + NODE_W // 2
        cy      = PADDING_Y + AVATAR_SIZE // 2
        label_y = cy + AVATAR_SIZE // 2 + 15
        is_root = login == root
        b64_src = avatars.get(login, placeholder_b64())

        # border ring
        ln(f'  <circle cx="{cx}" cy="{cy}" r="{AVATAR_SIZE // 2 + 2}"'
           f' fill="{ACCENT if is_root else BORDER}"/>')

        # avatar — fully embedded, no external fetch at render time
        ln(f'  <image href="{b64_src}"'
           f' x="{cx - AVATAR_SIZE // 2}" y="{cy - AVATAR_SIZE // 2}"'
           f' width="{AVATAR_SIZE}" height="{AVATAR_SIZE}"'
           f' clip-path="url(#cp{i})" preserveAspectRatio="xMidYMid slice"/>')

        # username
        ln(f'  <text x="{cx}" y="{label_y}" text-anchor="middle"'
           f' font-family="{FONT}" font-size="11"'
           f' fill="{ACCENT if is_root else LINK}">{truncate(login)}</text>')

        # ME badge on root
        if is_root:
            bx = cx + AVATAR_SIZE // 2 - 6
            by = cy + AVATAR_SIZE // 2 - 6
            ln(f'  <rect x="{bx - 12}" y="{by - 8}" width="24" height="12"'
               f' rx="6" fill="{ACCENT}"/>')
            ln(f'  <text x="{bx}" y="{by + 2}" text-anchor="middle"'
               f' font-family="{FONT}" font-size="7" font-weight="bold"'
               f' fill="white">ME</text>')

    ln()

    # ── footer ────────────────────────────────────────────────────────────────
    note = "Edge weight = shared mutual friends + 1" 
    ln(f'  <text x="{total_w // 2}" y="{total_h-14}" text-anchor="middle"'
       f' font-family="{FONT}" font-size="14" fill="{MUTED}">{note}</text>')
    ln("</svg>")
    return "\n".join(out)


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    data  = json.loads(Path(INPUT).read_text())
    nodes = data["nodes"]

    print(f"Downloading {len(nodes)} avatar(s)...")
    avatars: dict[str, str] = {}
    for login in nodes:
        print(f"  {login}", end=" ", flush=True)
        uri = fetch_avatar_b64(login)
        if uri:
            avatars[login] = uri
            print("ok")
        else:
            avatars[login] = placeholder_b64()
            print("failed (placeholder used)")

    svg = build_svg(data, avatars)
    Path(OUTPUT).write_text(svg)

    kb = len(svg.encode()) / 1024
    print(f"\nWritten {OUTPUT}  ({kb:.1f} KB, {len(nodes)} nodes, {data['hops']} hops)")


if __name__ == "__main__":
    main()