# Obsidian Knowledge Graph Analysis with Graph Theory

Obsidian's graph view looks complex as your vault grows, but the underlying structure is surprisingly simple. When note A links to note B, it creates a directed edge A → B — a textbook **directed graph**. Obsidian's graph view often renders these as undirected, but the raw link data is directional.

Because the structure maps directly onto $G = (V, E)$, we can apply graph theory to extract meaningful patterns from any vault.

## What You Can Extract

### Degree Distribution

In most knowledge vaults, the distribution of links per note follows a **power law**: a few hub notes attract the majority of connections while most notes have only a handful. This is natural — MOC (Map of Content) pages and index notes act as hubs by design.

### Clustering Coefficient

The clustering coefficient measures whether your neighbors are also neighbors of each other. High values in a region suggest a tightly knit **topic cluster**. For example, if your AI-related notes are densely interconnected, that cluster will show a high coefficient.

### Community Detection

Algorithms like **Louvain** or modularity-based methods can automatically group notes into communities — even without tags. The link structure alone reveals which notes belong to the same topic.

### Centrality Metrics

| Metric | What It Finds |
|---|---|
| **Betweenness Centrality** | Bridge notes connecting different topic clusters |
| **PageRank** | Notes that are important because important notes link to them |
| **Closeness Centrality** | Notes that are closest (on average) to every other note |

### Isolated Notes & Connected Components

Counting isolated nodes and connected components gives you a quick health check on how well-integrated your vault is.

## Typical Patterns You'll Find

- **Small-world property** — Most note pairs are reachable within 3–5 hops, with high clustering but short average path length.
- **Scale-free tendency** — A handful of hub notes dominate overall connectivity.
- **Structural holes** — Gaps between clusters where adding a bridge note can spark cross-topic connections.

## Usage

Since Obsidian vaults are just Markdown files with `[[wikilinks]]`, you can parse them into a NetworkX graph and run all of the above analyses directly.

```bash
pip install networkx matplotlib numpy scipy
```

```bash
python obsidian_graph_analysis.py /path/to/your/vault
```

The script will output:
- Top hub notes by degree
- Degree distribution plot (log-log scale to check for power law)
- Community detection results (Louvain)
- Centrality rankings (betweenness, PageRank, closeness)
- Connected component summary
- Small-world diagnostics (average path length, clustering coefficient)

## A Fun Aside: Graph Theory in *Good Will Hunting*

Both blackboard problems in the opening of *Good Will Hunting* (1997) are graph theory problems.

**Problem 1** combines graph theory with linear algebra. Given a 4-node graph, the task is to find its adjacency matrix, compute the matrix of 3-step walks ($A^3$), and derive the generating function for walks between nodes. The key insight is that the $(i,j)$ entry of $A^n$ counts the number of $n$-step walks from node $i$ to node $j$.

**Problem 2** is the more famous one: *draw all homeomorphically irreducible trees on 10 nodes* — trees with no degree-2 vertices (no node that merely lets an edge pass through). The answer is exactly **10** such trees, though Will only draws 8 in the film before being interrupted.

Despite the movie's dramatic framing ("it took the department two years"), both problems are standard textbook exercises that anyone with a solid graph theory background can solve systematically.

The tree concept from Problem 2 connects directly back to Obsidian: a **tree** is a connected acyclic graph, and many note clusters in a vault naturally form tree structures — especially the hierarchical branches that extend from a MOC down to leaf notes.

## Recommended Reading

For a rigorous introduction to graph theory, Springer's GTM series has solid options. There are also many accessible introductions available if you search around.

## License

MIT
