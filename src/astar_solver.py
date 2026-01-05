import math
import heapq
import networkx as nx
from graph_builder import build_graph


def heuristic(G: nx.DiGraph, u: str, v: str) -> float:
    """Düğümler arasındaki öklid mesafeden basit süre tahmini (dakika) üretir."""
    ux, uy = G.nodes[u]["x"], G.nodes[u]["y"]
    vx, vy = G.nodes[v]["x"], G.nodes[v]["y"]
    d = math.sqrt((ux - vx) ** 2 + (uy - vy) ** 2)

    if d == 0:
        return 0.0

    # Uydurma bir katsayı, ama h(n) pozitif ve orantılı olsun yeter.
    return d / 0.03


def solve_astar_simple(G: nx.DiGraph, start: str, goal: str):
    """Yalın: sadece travel_time'a göre NetworkX A* kullan."""
    path = nx.astar_path(
        G,
        start,
        goal,
        heuristic=lambda u, v: heuristic(G, u, v),
        weight="travel_time",
    )
    total_time = sum(G[u][v]["travel_time"] for u, v in zip(path[:-1], path[1:]))
    total_cost = sum(G[u][v]["cost"] for u, v in zip(path[:-1], path[1:]))
    return path, total_time, total_cost


def solve_astar_constrained(
    G: nx.DiGraph,
    start: str,
    goal: str,
    allowed_modes=None,
    max_cost: float | None = None,
    max_time: float | None = None,
):
    """
    Kısıtlı A*: travel_time'ı minimize eder, ancak:
      - allowed_modes içinde olmayan modları kullanmaz
      - max_cost ve/veya max_time sınırlarını aşmaz.

    Path yoksa (kısıtlardan dolayı) None döner.
    """
    if allowed_modes is None:
        # Hiç verilmezse tüm modlara izin ver
        allowed_modes = {"metro", "bus", "train", "walk", "bike", "car"}
    else:
        allowed_modes = set(allowed_modes)

    # (f, g_time, node, cost_so_far, path)
    # f = g_time + h
    h0 = heuristic(G, start, goal)
    open_list = [(h0, 0.0, start, 0.0, [start])]

    # visited[(node)] = en iyi bulunan (time, cost)
    visited = {start: (0.0, 0.0)}

    while open_list:
        f, time_so_far, node, cost_so_far, path = heapq.heappop(open_list)

        if node == goal:
            return path, time_so_far, cost_so_far

        for neighbor in G.successors(node):
            edge_data = G[node][neighbor]
            mode = edge_data["mode"]
            if mode not in allowed_modes:
                continue

            travel_time = edge_data["travel_time"]
            cost = edge_data["cost"]

            new_time = time_so_far + travel_time
            new_cost = cost_so_far + cost

            # Kısıt kontrolleri
            if (max_time is not None) and (new_time > max_time):
                continue
            if (max_cost is not None) and (new_cost > max_cost):
                continue

            # Daha önce bu node'a çok daha iyi (zaman & maliyet) ile gelmişsek,
            # bu durumu genişletmeye gerek yok.
            if neighbor in visited:
                best_time, best_cost = visited[neighbor]
                if (new_time >= best_time) and (new_cost >= best_cost):
                    continue

            visited[neighbor] = (new_time, new_cost)
            h_val = heuristic(G, neighbor, goal)
            f_new = new_time + h_val
            heapq.heappush(
                open_list, (f_new, new_time, neighbor, new_cost, path + [neighbor])
            )

    # Açık liste boşaldı ve hedefe ulaşan kısıtlı bir yol yok
    return None, None, None


if __name__ == "__main__":
    G = build_graph("data/nodes.csv", "data/edges.csv")

    print("=== Basit A* (sadece süre) ===")
    p, t, c = solve_astar_simple(G, "N6", "N8")
    print("Rota:", " -> ".join(p))
    print(f"Toplam süre: {t} dk, toplam maliyet: {c} TL\n")

    print("=== Kısıtlı A* örnekleri ===")

    # Örnek 1: Sadece toplu taşıma (car ve bike yok), maliyet sınırı yok, süre sınırı yok
    p, t, c = solve_astar_constrained(
        G,
        "N6",
        "N8",
        allowed_modes={"bus", "metro", "train", "walk"},
        max_cost=None,
        max_time=None,
    )
    print("\n[1] Sadece toplu taşıma (car, bike yok):")
    print("Rota:", " -> ".join(p) if p else "Rota yok")
    print(f"Süre: {t} dk, Maliyet: {c} TL")

    # Örnek 2: Özel araç kullanma (car yok), maliyet <= 20 TL
    p, t, c = solve_astar_constrained(
        G,
        "N6",
        "N8",
        allowed_modes={"bus", "metro", "train", "walk", "bike"},
        max_cost=20.0,
        max_time=None,
    )
    print("\n[2] max_cost = 20 TL, car yok:")
    if p:
        print("Rota:", " -> ".join(p))
        print(f"Süre: {t} dk, Maliyet: {c} TL")
    else:
        print("Uygun rota bulunamadı (kısıtlardan dolayı).")

    # Örnek 3: Süre sınırı (max_time = 30 dk), tüm modlar serbest
    p, t, c = solve_astar_constrained(
        G,
        "N6",
        "N8",
        allowed_modes={"metro", "bus", "train", "walk", "bike", "car"},
        max_cost=None,
        max_time=30.0,
    )
    print("\n[3] max_time = 30 dk, tüm modlar serbest:")
    if p:
        print("Rota:", " -> ".join(p))
        print(f"Süre: {t} dk, Maliyet: {c} TL")
    else:
        print("Uygun rota bulunamadı (kısıtlardan dolayı).")
