from typing import List, Optional

import matplotlib.pyplot as plt
import networkx as nx

from utils import load_default_graph, path_stats


def draw_graph(G: nx.DiGraph, ax=None, show_labels: bool = True):
    """Grafı (soyut koordinatlara göre) çizer."""
    if ax is None:
        fig, ax = plt.subplots()

    pos = {n: (G.nodes[n]["x"], G.nodes[n]["y"]) for n in G.nodes()}

    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.4)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=300)

    if show_labels:
        labels = {n: G.nodes[n]["name"] for n in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, ax=ax)

    ax.set_axis_off()
    ax.set_title("Multimodal Ağ (soyut koordinatlar)")

    return ax


def draw_path(G: nx.DiGraph, path: List[str], ax=None):
    """Verilen rotayı graf üzerinde kalın çizgiyle gösterir."""
    if ax is None:
        fig, ax = plt.subplots()

    ax = draw_graph(G, ax=ax, show_labels=True)

    pos = {n: (G.nodes[n]["x"], G.nodes[n]["y"]) for n in G.nodes()}

    # rota kenarlarını çiz
    path_edges = list(zip(path[:-1], path[1:]))
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=path_edges,
        width=3.0,
        edge_color="red",
        ax=ax,
    )

    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=path,
        node_size=350,
        node_color="orange",
        ax=ax,
    )

    stats = path_stats(G, path)
    ax.set_title(
        f"Rota: {' -> '.join(path)}\n"
        f"Süre: {stats['total_time']} dk, "
        f"Maliyet: {stats['total_cost']} TL, "
        f"Aktarma: {stats['transfers']}"
    )

    return ax


if __name__ == "__main__":
    # Küçük test: A* ile rota bul ve görselleştir
    from astar_solver import solve_astar_simple

    G = load_default_graph()
    path, t, c = solve_astar_simple(G, "N6", "N8")

    ax = draw_path(G, path)
    plt.show()
