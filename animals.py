#!/usr/bin/env python3
"""
Build an interactive directed letter graph from animal names.

Usage
-----
    python animals.py animals.txt
    python animals.py animals.txt --controls
    python animals.py animals.txt --output my_graph.html
    cat animals.txt | python animals.py
"""

from __future__ import annotations

import argparse
import math
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import networkx as nx
from pyvis.network import Network


DEFAULT_OUTPUT = Path("animals_graph.html")


def normalise(name: str) -> str:
    """Keep letters only, lower-case them for graph matching."""
    return re.sub(r"[^a-z]", "", name.lower())


def canonicalise(name: str) -> str:
    """Normalize whitespace for display labels while preserving file casing."""
    return " ".join(name.split())


def read_animals(source: str | None = None) -> list[str]:
    if source is None:
        raw = sys.stdin.read().splitlines()
    else:
        raw = Path(source).read_text(encoding="utf-8").splitlines()

    animals: list[str] = []
    seen: set[str] = set()

    for line in raw:
        cleaned = line.strip()
        if not cleaned:
            continue

        display_name = canonicalise(cleaned)
        normalized = normalise(display_name)
        if not normalized or display_name in seen:
            continue

        seen.add(display_name)
        animals.append(display_name)

    return animals


def format_edge_tooltip(names: list[str], start: str, end: str) -> str:
    joined = "<br>".join(names)
    return f"<b>{start.upper()} -> {end.upper()}</b><br>{joined}"


def build_graph(animals: list[str]) -> nx.DiGraph:
    graph = nx.DiGraph()
    grouped_animals: dict[tuple[str, str], list[str]] = defaultdict(list)

    for animal in animals:
        normalized = normalise(animal)
        if not normalized:
            continue

        start = normalized[0]
        end = normalized[-1]
        graph.add_node(start)
        graph.add_node(end)
        grouped_animals[(start, end)].append(animal)

    for (start, end), names in grouped_animals.items():
        graph.add_edge(
            start,
            end,
            animals=names,
            count=len(names),
            title=format_edge_tooltip(names, start, end),
        )

    return graph


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Visualize animal names as an interactive directed graph where each "
            "name connects its first normalized letter to its last normalized letter."
        )
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Text file with one animal name per line. If omitted, read from stdin.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=(
            "HTML file to write. Default: %(default)s. The browser view is opened "
            "from this file unless --no-show is used."
        ),
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Write the HTML graph but do not open it in a browser.",
    )
    parser.add_argument(
        "--controls",
        action="store_true",
        help="Show PyVis physics/layout controls in the page.",
    )
    return parser.parse_args()


def build_static_positions(graph: nx.DiGraph) -> dict[str, tuple[float, float]]:
    nodes = sorted(graph.nodes())
    if not nodes:
        return {}

    radius = 900.0
    total = len(nodes)
    positions: dict[str, tuple[float, float]] = {}

    for index, node in enumerate(nodes):
        angle = (2 * math.pi * index / total) - (math.pi / 2)
        positions[node] = (
            math.cos(angle) * radius,
            math.sin(angle) * radius,
        )

    return positions


def build_network(graph: nx.DiGraph, show_controls: bool) -> Network:
    net = Network(
        height="85vh",
        width="100%",
        directed=True,
        notebook=False,
        bgcolor="#fcfbf7",
        font_color="#111827",
        cdn_resources="remote",
    )
    positions = build_static_positions(graph)

    net.toggle_drag_nodes(True)
    net.toggle_physics(False)
    net.toggle_hide_edges_on_drag(False)
    net.toggle_hide_nodes_on_drag(False)
    net.set_options(
        """
        {
          "interaction": {
            "hover": true,
            "multiselect": true,
            "navigationButtons": true,
            "keyboard": {
              "enabled": true,
              "bindToWindow": false
            }
          },
          "layout": {
            "improvedLayout": false
          },
          "edges": {
            "arrows": {
              "to": {
                "enabled": true,
                "scaleFactor": 0.7
              }
            },
            "color": {
              "color": "#3b82f6",
              "highlight": "#1d4ed8"
            },
            "font": {
              "size": 12,
              "align": "middle"
            },
            "smooth": {
              "enabled": true,
              "type": "dynamic"
            }
          },
          "nodes": {
            "color": {
              "background": "#f59e0b",
              "border": "#92400e",
              "highlight": {
                "background": "#fbbf24",
                "border": "#78350f"
              }
            },
            "font": {
              "size": 28,
              "face": "Georgia"
            },
            "shape": "dot"
          },
          "physics": {
            "enabled": false
          }
        }
        """
    )

    for node in sorted(graph.nodes()):
        x, y = positions[node]
        incoming = sum(graph.edges[edge]["count"] for edge in graph.in_edges(node))
        outgoing = sum(graph.edges[edge]["count"] for edge in graph.out_edges(node))
        degree_weight = incoming + outgoing
        net.add_node(
            node,
            label=node.upper(),
            size=24 + degree_weight * 2,
            title=(
                f"<b>{node.upper()}</b><br>"
                f"Starts {outgoing} animal name(s)<br>"
                f"Ends {incoming} animal name(s)"
            ),
            x=x,
            y=y,
            physics=False,
        )

    for start, end, data in graph.edges(data=True):
        count = data["count"]
        net.add_edge(
            start,
            end,
            label=str(count),
            title=data["title"],
            width=1 + count * 0.6,
            value=count,
        )

    if show_controls:
        net.show_buttons(filter_=["physics", "layout", "interaction"])

    return net


def write_html(network: Network, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    network.write_html(str(output_path), notebook=False, open_browser=False)
    return output_path.resolve()


def open_in_browser(path: Path) -> None:
    commands = [
        ["xdg-open", str(path)],
        ["open", str(path)],
        ["gio", "open", str(path)],
    ]

    for command in commands:
        if shutil.which(command[0]) is None:
            continue
        try:
            subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"Opened interactive graph: {path}")
            return
        except OSError:
            continue

    raise SystemExit(
        f"Graph written to {path}, but no browser launcher was found."
    )


def render_graph(graph: nx.DiGraph, output_path: Path, show_graph: bool, show_controls: bool) -> None:
    network = build_network(graph, show_controls=show_controls)
    html_path = write_html(network, output_path)
    print(f"Wrote interactive graph to {html_path}")

    if show_graph:
        open_in_browser(html_path)


def main() -> None:
    args = parse_args()
    animals = read_animals(args.input)
    if not animals:
        print("No valid animal names found.", file=sys.stderr)
        raise SystemExit(1)

    graph = build_graph(animals)
    if graph.number_of_edges() == 0:
        print("No valid letter connections found.", file=sys.stderr)
        raise SystemExit(1)

    render_graph(
        graph,
        output_path=args.output,
        show_graph=not args.no_show,
        show_controls=args.controls,
    )


if __name__ == "__main__":
    main()
