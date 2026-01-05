from typing import List, Tuple, Dict, Optional

import math
import networkx as nx

from utils import load_default_graph, path_stats


TRANSIT_MODES = {"metro", "bus", "train", "car", "bike", "walk"}


def raptor_like(
    G: nx.DiGraph,
    start: str,
    goal: str,
    max_rounds: int = 3,
) -> Tuple[Optional[List[str]], Optional[Dict]]:
    """
    Çok basitleştirilmiş bir RAPTOR benzeri algoritma.

    Fikir:
      - Sadece toplu taşıma modlarını (metro, bus, train) kullan.
      - Round sayısı = maksimum aktarma sayısı gibi düşünülebilir.
      - Her round'da, bir önceki round'da iyileşen düğümlerden çıkan
        seyahat sürelerini gevşeterek "daha az aktarmalı" yolları bul.

    Bu implementasyon:
      - Zaman pencere / sefer saatleri yerine sadece kenar süresini kullanır.
      - Yine de "round-based" mantığı ve "maksimum aktarma sayısı" fikrini gösterir.
    """

    # Her node için her round'da en iyi bulunan süre
    INF = math.inf
    rounds = [
        {node: INF for node in G.nodes()}
        for _ in range(max_rounds + 1)
    ]

    # Önceki düğümleri tutarak path reconstruct edeceğiz
    prev: List[Dict[str, Tuple[str, int]]] = [
        {} for _ in range(max_rounds + 1)
    ]

    rounds[0][start] = 0.0

    for r in range(1, max_rounds + 1):
        # Bir önceki round sonuçlarını kopyala
        rounds[r] = rounds[r - 1].copy()

        # Bu round'da iyileşen düğümler (başlangıçta tüm düğümler)
        for u in G.nodes():
            if rounds[r - 1][u] == INF:
                continue  # önceki round'da hiç ulaşılmadıysa, buradan çıkma

            time_u = rounds[r - 1][u]

            # sadece toplu taşıma kenarlarını dikkate al
            for v in G.successors(u):
                data = G[u][v]
                if data["mode"] not in TRANSIT_MODES:
                    continue

                new_time = time_u + data["travel_time"]

                if new_time < rounds[r][v]:
                    rounds[r][v] = new_time
                    prev[r][v] = (u, r - 1)

    # goal için en iyi round'u seç
    best_r = None
    best_time = INF
    for r in range(max_rounds + 1):
        t = rounds[r][goal]
        if t < best_time:
            best_time = t
            best_r = r

    if best_r is None or best_time == INF:
        return None, None  # hedefe toplu taşımayla ulaşılamıyor

    # path reconstruct
    path = [goal]
    curr_node = goal
    curr_r = best_r

    while curr_node != start and curr_r > 0:
        if curr_node not in prev[curr_r]:
            # path kopuk ise
            break
        u, prev_r = prev[curr_r][curr_node]
        path.append(u)
        curr_node = u
        curr_r = prev_r

    if curr_node != start:
        # güvenlik için
        return None, None

    path.reverse()
    stats = path_stats(G, path)
    stats["rounds_used"] = best_r

    return path, stats


if __name__ == "__main__":
    G = load_default_graph()
    start, goal = "N1", "N8"  

    path, stats = raptor_like(G, start, goal, max_rounds=3)

    if path is None:
        print("RAPTOR-benzeri algoritma ile uygun rota bulunamadı.")
    else:
        print("Rota (RAPTOR-like):", " -> ".join(path))
        print(
            f"Süre: {stats['total_time']} dk, "
            f"Maliyet: {stats['total_cost']} TL, "
            f"Aktarma: {stats['transfers']}, "
            f"Kullanılan round: {stats['rounds_used']}"
        )
