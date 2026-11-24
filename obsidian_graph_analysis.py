#!/usr/bin/env python3
"""
obsidian_graph_analysis.py

Parse an Obsidian vault and analyze its link structure using graph theory.

Usage:
    python obsidian_graph_analysis.py /path/to/your/vault
    python obsidian_graph_analysis.py /path/to/your/vault --output results
"""

import argparse
import re
import sys
from pathlib import Path
from collections import Counter

import networkx as nx
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


# ---------------------------------------------------------------------------
# 1. Parse vault into a directed graph
# ---------------------------------------------------------------------------

WIKILINK_PATTERN = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]*)?\|?[^\]]*\]\]")


def parse_vault(vault_path: Path) -> nx.DiGraph:
    """Walk every .md file in the vault and build a directed graph."""
    G = nx.DiGraph()
    md_files = list(vault_path.rglob("*.md"))

    if not md_files:
        print(f"No .md files found in {vault_path}")
        sys.exit(1)

    for md in md_files:
        source = md.stem
        G.add_node(source)
        try:
            text = md.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = md.read_text(encoding="latin-1")
        for match in WIKILINK_PATTERN.finditer(text):
            target = match.group(1).strip()
            if target:
                G.add_edge(source, target)

    return G


# ---------------------------------------------------------------------------
# 2. Analysis helpers
# ---------------------------------------------------------------------------


def top_nodes_by_degree(G: nx.DiGraph, n: int = 15):
    """Return the top-n nodes ranked by total degree (in + out)."""
    undirected = G.to_undirected()
    return sorted(undirected.degree(), key=lambda x: x[1], reverse=True)[:n]


def degree_distribution(G: nx.DiGraph):
    """Compute degree distribution on the undirected projection."""
    undirected = G.to_undirected()
    degrees = [d for _, d in undirected.degree()]
    counts = Counter(degrees)
    k = sorted(counts.keys())
    pk = [counts[ki] / len(degrees) for ki in k]
    return k, pk


def community_detection(G: nx.DiGraph):
    """Run Louvain community detection on the undirected projection."""
    undirected = G.to_undirected()
    # Remove isolated nodes for cleaner communities
    largest_cc = max(nx.connected_components(undirected), key=len)
    subgraph = undirected.subgraph(largest_cc).copy()
    communities = nx.community.louvain_communities(subgraph, seed=42)
    return communities


def centrality_analysis(G: nx.DiGraph, top_n: int = 10):
    """Compute betweenness, PageRank, and closeness centrality."""
    betweenness = nx.betweenness_centrality(G)
    pagerank = nx.pagerank(G, alpha=0.85)
    # Closeness on undirected for interpretability
    undirected = G.to_undirected()
    closeness = nx.closeness_centrality(undirected)

    top_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[
        :top_n
    ]
    top_pagerank = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:top_n]
    top_closeness = sorted(closeness.items(), key=lambda x: x[1], reverse=True)[:top_n]

    return {
        "betweenness": top_betweenness,
        "pagerank": top_pagerank,
        "closeness": top_closeness,
    }


def component_summary(G: nx.DiGraph):
    """Summarize connected components in the undirected projection."""
    undirected = G.to_undirected()
    components = list(nx.connected_components(undirected))
    sizes = sorted([len(c) for c in components], reverse=True)
    isolated = sum(1 for _, d in undirected.degree() if d == 0)
    return {
        "num_components": len(components),
        "largest": sizes[0] if sizes else 0,
        "isolated_nodes": isolated,
        "component_sizes": sizes[:10],  # top 10
    }


def small_world_diagnostics(G: nx.DiGraph):
    """Check small-world properties on the largest connected component."""
    undirected = G.to_undirected()
    largest_cc = max(nx.connected_components(undirected), key=len)
    subgraph = undirected.subgraph(largest_cc).copy()

    avg_clustering = nx.average_clustering(subgraph)
    avg_path_length = (
        nx.average_shortest_path_length(subgraph) if len(subgraph) < 5000 else None
    )

    n = subgraph.number_of_nodes()
    m = subgraph.number_of_edges()
    # Compare with an Erdős–Rényi random graph of same size
    p = (2 * m) / (n * (n - 1)) if n > 1 else 0
    expected_clustering_random = p
    expected_path_random = np.log(n) / np.log(max(n * p, 2)) if n * p > 1 else None

    return {
        "nodes_in_largest_cc": n,
        "avg_clustering": avg_clustering,
        "avg_path_length": avg_path_length,
        "random_graph_clustering": expected_clustering_random,
        "random_graph_path_length": expected_path_random,
    }


# ---------------------------------------------------------------------------
# 3. Plotting
# ---------------------------------------------------------------------------


def plot_degree_distribution(k, pk, output_dir: Path):
    """Log-log plot of the degree distribution."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(k, pk, s=30, alpha=0.7, edgecolors="black", linewidths=0.5)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Degree (k)")
    ax.set_ylabel("P(k)")
    ax.set_title("Degree Distribution (log-log)")
    ax.grid(True, which="both", ls="--", alpha=0.3)
    fig.tight_layout()
    path = output_dir / "degree_distribution.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_community_sizes(communities, output_dir: Path):
    """Bar chart of community sizes."""
    sizes = sorted([len(c) for c in communities], reverse=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(range(len(sizes)), sizes, color="#4C72B0", edgecolor="black", linewidth=0.5)
    ax.set_xlabel("Community Index")
    ax.set_ylabel("Number of Notes")
    ax.set_title(f"Community Sizes ({len(communities)} communities)")
    ax.grid(True, axis="y", ls="--", alpha=0.3)
    fig.tight_layout()
    path = output_dir / "community_sizes.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# 4. Report
# ---------------------------------------------------------------------------


def print_section(title: str):
    width = 60
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


def run_analysis(vault_path: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    # Parse
    print(f"Parsing vault: {vault_path}")
    G = parse_vault(vault_path)
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")

    # --- Hub notes ---
    print_section("Top Hub Notes (by degree)")
    for name, deg in top_nodes_by_degree(G):
        print(f"  {name:40s}  degree={deg}")

    # --- Degree distribution ---
    print_section("Degree Distribution")
    k, pk = degree_distribution(G)
    path = plot_degree_distribution(k, pk, output_dir)
    print(f"  Plot saved to {path}")

    # --- Communities ---
    print_section("Community Detection (Louvain)")
    communities = community_detection(G)
    print(f"  Found {len(communities)} communities")
    for i, comm in enumerate(sorted(communities, key=len, reverse=True)[:8]):
        sample = sorted(comm)[:5]
        suffix = " ..." if len(comm) > 5 else ""
        print(f"  Community {i}: {len(comm)} notes — {', '.join(sample)}{suffix}")
    path = plot_community_sizes(communities, output_dir)
    print(f"  Plot saved to {path}")

    # --- Centrality ---
    print_section("Centrality Rankings")
    centrality = centrality_analysis(G)
    for metric, ranking in centrality.items():
        print(f"\n  [{metric}]")
        for name, score in ranking:
            print(f"    {name:40s}  {score:.4f}")

    # --- Components ---
    print_section("Connected Components")
    comp = component_summary(G)
    print(f"  Total components:  {comp['num_components']}")
    print(f"  Largest component: {comp['largest']} notes")
    print(f"  Isolated nodes:    {comp['isolated_nodes']}")
    print(f"  Top component sizes: {comp['component_sizes']}")

    # --- Small-world ---
    print_section("Small-World Diagnostics")
    sw = small_world_diagnostics(G)
    print(f"  Nodes in largest CC: {sw['nodes_in_largest_cc']}")
    print(f"  Avg clustering coeff:   {sw['avg_clustering']:.4f}")
    if sw["avg_path_length"] is not None:
        print(f"  Avg path length:        {sw['avg_path_length']:.2f}")
    else:
        print("  Avg path length:        (skipped — CC too large)")
    print(f"  Random graph clustering: {sw['random_graph_clustering']:.4f}")
    if sw["random_graph_path_length"] is not None:
        print(f"  Random graph path len:   {sw['random_graph_path_length']:.2f}")

    # Summary interpretation
    if sw["avg_clustering"] > 5 * sw["random_graph_clustering"]:
        print("\n  → Clustering is much higher than random: small-world signature.")
    if sw["avg_path_length"] is not None and sw["random_graph_path_length"] is not None:
        if sw["avg_path_length"] < 2 * sw["random_graph_path_length"]:
            print("  → Path length is comparable to random: small-world confirmed.")

    print(f"\nDone. Charts saved in {output_dir}/")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze an Obsidian vault's link structure with graph theory."
    )
    parser.add_argument("vault", type=str, help="Path to your Obsidian vault folder")
    parser.add_argument(
        "--output",
        type=str,
        default="results",
        help="Directory for output charts (default: results)",
    )
    args = parser.parse_args()

    vault_path = Path(args.vault).expanduser().resolve()
    if not vault_path.is_dir():
        print(f"Error: {vault_path} is not a directory.")
        sys.exit(1)

    output_dir = Path(args.output)
    run_analysis(vault_path, output_dir)
