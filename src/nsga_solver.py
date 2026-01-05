import random
from typing import List, Tuple

import networkx as nx
from deap import base, creator, tools  # algorithms şu an kullanılmıyor ama dursa da olur

from graph_builder import build_graph

# Geçersiz rotalar için ceza (süre, maliyet, aktarma)
PENALTY = 10_000.0

# -----------------------------
#  Global parametreler (fonksiyon içinde set edilecek)
# -----------------------------
START_NODE: str | None = None
GOAL_NODE: str | None = None
MAX_INTERMEDIATE_LEN: int = 4
GLOBAL_GRAPH: nx.DiGraph | None = None

# DEAP sınıfları bir kez oluşturulsun (tekrar importta hata vermesin)
try:
    creator.FitnessMulti
except AttributeError:
    creator.create("FitnessMulti", base.Fitness, weights=(-1.0, -1.0, -1.0))
    creator.create("Individual", list, fitness=creator.FitnessMulti)

toolbox = base.Toolbox()


# -----------------------------
#  Yardımcı fonksiyonlar
# -----------------------------
def random_path_middle_nodes(G: nx.DiGraph, max_len: int) -> List[str]:
    """
    Sadece ara düğümlerden oluşan bir liste üretir.
    Tam rota: [START_NODE] + middle_nodes + [GOAL_NODE]
    """
    global START_NODE, GOAL_NODE
    assert START_NODE is not None and GOAL_NODE is not None, "START_NODE/GOAL_NODE set edilmedi."

    nodes = list(G.nodes())
    # başlangıç ve hedef hariç
    if START_NODE in nodes:
        nodes.remove(START_NODE)
    if GOAL_NODE in nodes:
        nodes.remove(GOAL_NODE)

    length = random.randint(0, max_len)  # 0 ara düğüm de olabilir
    middle = []

    for _ in range(length):
        middle.append(random.choice(nodes))

    return middle


def build_full_path(middle_nodes: List[str]) -> List[str]:
    """Ara düğümlerden tam rota oluştur: [START_NODE] + middle + [GOAL_NODE]."""
    global START_NODE, GOAL_NODE
    assert START_NODE is not None and GOAL_NODE is not None
    return [START_NODE] + middle_nodes + [GOAL_NODE]


def evaluate_path(G: nx.DiGraph, path: List[str]) -> Tuple[float, float, float]:
    """
    Bir tam rotayı (node listesi) değerlendir:
      - Toplam süre
      - Toplam maliyet
      - Aktarma sayısı (mode değişim sayısı)
    Eğer rota geçersizse büyük ceza döner.
    """
    total_time = 0.0
    total_cost = 0.0
    transfers = 0

    last_mode = None

    for u, v in zip(path[:-1], path[1:]):
        if not G.has_edge(u, v):
            # Grafikte böyle bir kenar yoksa, ceza ver
            return PENALTY, PENALTY, PENALTY

        data = G[u][v]
        total_time += data["travel_time"]
        total_cost += data["cost"]

        mode = data["mode"]
        if last_mode is not None and mode != last_mode:
            transfers += 1
        last_mode = mode

    return total_time, total_cost, float(transfers)


# -----------------------------
#  DEAP - NSGA-II setup
# -----------------------------
def cx_middle(ind1, ind2):
    """Tek noktalı crossover: ara düğümler arasında."""
    global MAX_INTERMEDIATE_LEN

    if len(ind1) > 1 and len(ind2) > 1:
        cx_point1 = random.randint(1, len(ind1))
        cx_point2 = random.randint(1, len(ind2))
        new1 = ind1[:cx_point1] + ind2[cx_point2:]
        new2 = ind2[:cx_point2] + ind1[cx_point1:]
        # maksimum ara düğüm uzunluğu
        del new1[MAX_INTERMEDIATE_LEN:]
        del new2[MAX_INTERMEDIATE_LEN:]
        ind1[:] = new1
        ind2[:] = new2
    return ind1, ind2


def mut_middle(individual):
    """
    Mutasyon: üç tipten birini yap:
      - Rastgele bir ara düğümü değiştir
      - Ara düğüm ekle
      - Ara düğüm sil
    """
    global GLOBAL_GRAPH, START_NODE, GOAL_NODE, MAX_INTERMEDIATE_LEN
    G = GLOBAL_GRAPH
    assert G is not None

    all_nodes = [n for n in G.nodes() if n not in (START_NODE, GOAL_NODE)]

    choice = random.random()

    if choice < 0.33:
        # bir düğümü değiştir
        if len(individual) > 0:
            idx = random.randrange(len(individual))
            individual[idx] = random.choice(all_nodes)
    elif choice < 0.66:
        # yeni düğüm ekle
        if len(individual) < MAX_INTERMEDIATE_LEN:
            individual.append(random.choice(all_nodes))
    else:
        # düğüm sil
        if len(individual) > 0:
            idx = random.randrange(len(individual))
            del individual[idx]

    return (individual,)


def evaluate_individual(individual):
    """DEAP evaluate fonksiyonu: birey -> (time, cost, transfers)."""
    global GLOBAL_GRAPH
    assert GLOBAL_GRAPH is not None
    full_path = build_full_path(individual)
    return evaluate_path(GLOBAL_GRAPH, full_path)


def setup_toolbox(G: nx.DiGraph, start: str, goal: str, max_intermediate_len: int = 4):
    """Toolbox içindeki global parametreleri ayarla."""
    global GLOBAL_GRAPH, START_NODE, GOAL_NODE, MAX_INTERMEDIATE_LEN

    GLOBAL_GRAPH = G
    START_NODE = start
    GOAL_NODE = goal
    MAX_INTERMEDIATE_LEN = max_intermediate_len

    def _init_ind():
        middle = random_path_middle_nodes(G, MAX_INTERMEDIATE_LEN)
        return creator.Individual(middle)

    toolbox.register("individual", _init_ind)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    toolbox.register("mate", cx_middle)
    toolbox.register("mutate", mut_middle)
    toolbox.register("select", tools.selNSGA2)
    toolbox.register("evaluate", evaluate_individual)


# -----------------------------
#  Ana NSGA-II çalıştırma fonksiyonu
# -----------------------------
def run_nsga2(
    G: nx.DiGraph,
    start: str,
    goal: str,
    n_generations: int = 40,
    pop_size: int = 40,
    max_intermediate_len: int = 4,
):
    """
    Verilen start-goal için NSGA-II'yi çalıştır ve
    ceza almamış (geçerli) Pareto front çözümlerini döndür.
    """
    setup_toolbox(G, start, goal, max_intermediate_len)

    pop = toolbox.population(n=pop_size)
    hof = tools.ParetoFront()

    # İlk popülasyonun uygunluklarını hesapla
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    # Evrim döngüsü
    for gen in range(1, n_generations + 1):
        offspring = toolbox.select(pop, len(pop))
        offspring = list(map(toolbox.clone, offspring))

        # crossover
        for ind1, ind2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < 0.9:
                toolbox.mate(ind1, ind2)
                del ind1.fitness.values
                del ind2.fitness.values

        # mutasyon
        for ind in offspring:
            if random.random() < 0.3:
                toolbox.mutate(ind)
                del ind.fitness.values

        # uygunluğu hesaplanmamış bireyler
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        pop = offspring
        hof.update(pop)

        if gen % 10 == 0 or gen == 1 or gen == n_generations:
            print(f"Generation {gen} tamamlandı, hof boyutu: {len(hof)}")

    # Pareto front çözümlerini çıkar
    solutions = []
    for ind in hof:
        full_path = build_full_path(ind)
        t, c, tr = evaluate_path(G, full_path)
        solutions.append(
            {
                "middle_nodes": list(ind),
                "full_path": full_path,
                "total_time": t,
                "total_cost": c,
                "transfers": tr,
            }
        )

    # Ceza almış (geçersiz) rotaları filtrele
    valid_solutions = [
        s for s in solutions
        if s["total_time"] < PENALTY and s["total_cost"] < PENALTY
    ]

    return valid_solutions


# -----------------------------
#  Test / Örnek kullanım
# -----------------------------
if __name__ == "__main__":
    G = build_graph("data/nodes.csv", "data/edges.csv")
    start, goal = "N6", "N8"

    print(f"NSGA-II çalıştırılıyor ({start} -> {goal})...")
    sols = run_nsga2(G, start, goal, n_generations=40, pop_size=40)

    sols_sorted = sorted(
        sols,
        key=lambda s: (s["total_time"], s["total_cost"], s["transfers"])
    )

    print("\nEn iyi çözümlerden bazıları (zaman / maliyet / aktarma):\n")
    for i, s in enumerate(sols_sorted[:10], start=1):
        print(f"Çözüm {i}:")
        print("  Rota:", " -> ".join(s["full_path"]))
        print(
            f"  Süre: {s['total_time']} dk, "
            f"Maliyet: {s['total_cost']} TL, "
            f"Aktarma: {int(s['transfers'])}"
        )
        print()
