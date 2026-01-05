import pandas as pd
import networkx as nx


def build_graph(nodes_path: str, edges_path: str) -> nx.DiGraph:
    """nodes.csv ve edges.csv dosyalarından yönlü bir grafik (DiGraph) oluşturur."""
    nodes = pd.read_csv(nodes_path)
    edges = pd.read_csv(edges_path)

    G = nx.DiGraph()

    # Düğümleri ekle
    for _, r in nodes.iterrows():
        G.add_node(
            r["node_id"],
            name=r["name"],
            x=float(r["x"]),
            y=float(r["y"]),
            has_metro=int(r["has_metro"]),
            has_bus=int(r["has_bus"]),
            has_train=int(r["has_train"]),
            has_bike=int(r["has_bike"]),
        )

    # Kenarları ekle (ve ters yönü de otomatik oluştur)
    for _, e in edges.iterrows():
        u = e["from"]
        v = e["to"]

        attrs = dict(
            mode=e["mode"],
            travel_time=float(e["travel_time_min"]),
            cost=float(e["cost_tl"]),
            distance=float(e["distance_m"]),
            is_transfer=int(e["is_transfer"]),
        )

        # İleri yön
        G.add_edge(u, v, **attrs)

        # Ters yön: aynı mod ve aynı süre/maliyet varsayımıyla simetrik kabul ediyoruz
        if not G.has_edge(v, u):
            G.add_edge(v, u, **attrs)

    return G


if __name__ == "__main__":
    G = build_graph("data/nodes.csv", "data/edges.csv")

    print("Düğüm sayısı:", G.number_of_nodes())
    print("Kenar sayısı:", G.number_of_edges())

    print("\nDüğümler:")
    for n, data in G.nodes(data=True):
        print(n, data)

    print("\nKenarlar:")
    for u, v, data in G.edges(data=True):
        print(u, "->", v, data)
