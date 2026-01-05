import os
from typing import List, Dict, Any

import networkx as nx

from graph_builder import build_graph


# Proje kök dizinini ve data klasörünü bul
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def load_default_graph() -> nx.DiGraph:
    """data/nodes.csv ve data/edges.csv'den varsayılan grafı yükler."""
    nodes_path = os.path.join(DATA_DIR, "nodes.csv")
    edges_path = os.path.join(DATA_DIR, "edges.csv")
    return build_graph(nodes_path, edges_path)


def path_stats(G: nx.DiGraph, path: List[str]) -> Dict[str, Any]:
    """
    Verilen rota için:
      - toplam süre
      - toplam maliyet
      - toplam mesafe
      - aktarma sayısı (mod değiştikçe +1)
      - kullanılan modlar listesini döndürür.
    """
    if not path or len(path) < 2:
        return {
            "total_time": 0.0,
            "total_cost": 0.0,
            "total_distance": 0.0,
            "transfers": 0,
            "modes": [],
        }

    total_time = 0.0
    total_cost = 0.0
    total_distance = 0.0
    transfers = 0
    modes = []

    last_mode = None

    for u, v in zip(path[:-1], path[1:]):
        if not G.has_edge(u, v):
            raise ValueError(f"Grafikte {u} -> {v} kenarı yok.")

        data = G[u][v]
        total_time += data["travel_time"]
        total_cost += data["cost"]
        total_distance += data["distance"]

        mode = data["mode"]
        modes.append(mode)

        if last_mode is not None and mode != last_mode:
            transfers += 1
        last_mode = mode

    return {
        "total_time": total_time,
        "total_cost": total_cost,
        "total_distance": total_distance,
        "transfers": transfers,
        "modes": modes,
    }
