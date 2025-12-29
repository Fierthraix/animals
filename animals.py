#!/usr/bin/env python3
"""
animal_chain_graph.py

Generate and display a directed graph for the “animal‑name chain” game.

Usage
-----
    python animal_chain_graph.py animals.txt      # read from file
    cat animals.txt | python animal_chain_graph.py   # or pipe from stdin
"""

import sys
import re
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List


def normalise(name: str) -> str:
    """Keep letters only, lower‑case them (so 'Black Swan' → 'blackswan')."""
    return re.sub(r"[^a-z]", "", name.lower())


def read_animals(source: str | None = None) -> List[str]:
    if source is None:
        raw = sys.stdin.read().strip().splitlines()
    else:
        raw = Path(source).read_text(encoding="utf‑8").splitlines()
    # strip empty lines, preserve original spelling for labels
    animals = [line.strip() for line in raw if line.strip()]
    return animals


def build_graph(animals: List[str]) -> nx.DiGraph:
    g = nx.DiGraph()
    g.add_nodes_from(animals)

    # Pre‑compute first / last letters (letters only, lower‑case)
    first = {a: normalise(a)[0] for a in animals}
    last  = {a: normalise(a)[-1] for a in animals}

    for a in animals:
        for b in animals:
            if a != b and last[a] == first[b]:
                g.add_edge(a, b)
    return g


def draw_graph(g: nx.DiGraph) -> None:
    """
    Draw using a spring layout; for large lists you may prefer
    `pos = nx.nx_pydot.graphviz_layout(g, prog="dot")`
    """
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(g, seed=42)
    nx.draw_networkx(
        g,
        pos,
        with_labels=True,
        arrows=True,
        node_size=700,
        font_size=9,
        arrowstyle="-|>",
        linewidths=0.5,
    )
    plt.axis("off")
    plt.tight_layout()
    plt.show()


def main() -> None:
    source = sys.argv[1] if len(sys.argv) > 1 else None
    animals = read_animals(source)
    if not animals:
        print("No animals found!", file=sys.stderr)
        sys.exit(1)

    g = build_graph(animals)
    draw_graph(g)


if __name__ == "__main__":
    main()
