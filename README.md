# Multimodal Project (A\* / RAPTOR-benzeri / NSGA-II)

Bu repo, `nodes.csv` ve `edges.csv` ile tanımlanan **çok-modlu (multimodal) ulaşım ağında** rota bulma ve **çok amaçlı optimizasyon** denemeleri içerir.

- **Graf modeli:** `networkx.DiGraph`
- **Veri kaynağı:** `data/nodes.csv`, `data/edges.csv`
- **Algoritmalar:**
  - **A\*** (kısıtlı/kısıtsız rota arama) – süre odaklı, opsiyonel kısıtlar (mod, max süre, max maliyet)
  - **RAPTOR-benzeri** yaklaşım – round bazlı en erken varış zamanı araması (basitleştirilmiş)
  - **NSGA-II (DEAP)** – çok amaçlı optimizasyon (ör. süre + maliyet + aktarma)

> Not: `web/streamlit_app.py` dosyasında bir noktada `...` placeholder satırı var. Streamlit arayüzünü tamamlamak için o bölümün doldurulması gerekir.

---

## Proje Yapısı

```
multimodal_project/
  data/
    edges.csv
    nodes.csv
  notebooks/
    experiments.ipynb
  src/
    astar_solver.py
    graph_builder.py
    nsga_solver.py
    raptor_solver.py
    utils.py
    visualization.py
    __pycache__/
      astar_solver.cpython-310.pyc
      graph_builder.cpython-310.pyc
      nsga_solver.cpython-310.pyc
      raptor_solver.cpython-310.pyc
      utils.cpython-310.pyc
      visualization.cpython-310.pyc
  web/
    streamlit_app.py
```

### Klasörler

- `data/`  
  Düğümler ve kenarlar (yönlü) CSV formatında.
- `src/`  
  Graf oluşturma, algoritmalar, yardımcı fonksiyonlar ve görselleştirme.
- `web/`  
  Streamlit tabanlı demo arayüz.
- `notebooks/`  
  Deney/analiz notebook'u.

---

## Veri Formatı

### `data/nodes.csv`

Kolonlar:

- `node_id`: Düğüm ID (ör. `N1`)
- `name`: İsim/etiket
- `x`, `y`: Soyut koordinatlar (heuristic ve çizim için)
- `has_metro`, `has_bus`, `has_train`, `has_bike`: 0/1 bayrakları

Örnek:
- `N1, Kizilay, 0.0, 0.0, 1, 1, 0, 1`

### `data/edges.csv`

Kolonlar:

- `edge_id`: Kenar ID (ör. `E1`)
- `from`, `to`: yön (`from` → `to`)
- `mode`: ulaşım modu (`metro`, `bus`, `train`, `car`, `bike`, `walk` vb.)
- `travel_time_min`: süre (dakika)
- `cost_tl`: maliyet (TL)
- `distance_m`: mesafe (metre)
- `is_transfer`: aktarma kenarı mı? (0/1)

---



## Çalıştırma

### Grafı test et (CLI)

`src/graph_builder.py` içinde `__main__` bloğu var:

```bash
python src/graph_builder.py
```

Bu komut düğüm/kenar sayısını ve bazı örnekleri yazdırır.

### A\* ile rota bulma

`src/astar_solver.py` içinde basit test kullanılabilir. Genel kullanım:
- `solve_astar_simple(G, start, goal)`
- `solve_astar_constrained(G, start, goal, allowed_modes, max_cost, max_time)`

Örnek (dosyanın kendi `__main__` testine göre değişebilir):
```bash
python src/astar_solver.py
```

### RAPTOR-benzeri rota bulma

```bash
python src/raptor_solver.py
```

Çıktı olarak rota + süre/maliyet/aktarma + round sayısı basar.

### NSGA-II ile çok amaçlı çözüm üretme

```bash
python src/nsga_solver.py
```

Bu, `run_nsga2(...)` ile çözümler üretir; örnek `__main__` çıktısında en iyi birkaç çözümü listeler.

### Görselleştirme (Matplotlib)

```bash
python src/visualization.py
```

Bu dosya:
- grafı çizer
- seçilen bir path’i kalın çizgiyle vurgular
- `path_stats` ile istatistikleri alıp graf üstüne yazabilir

### Streamlit arayüz

```bash
streamlit run web/streamlit_app.py
```

> `web/streamlit_app.py` dosyasında `...` placeholder satırı var. Streamlit arayüzünün üst kısmı/kurulum kısmı bu bölümde eksik olabilir. Hata alırsan bu satırı kaldırıp arayüz akışını tamamlaman gerekir.

---

## Modüller

### `src/graph_builder.py`
- `build_graph(nodes_path, edges_path) -> nx.DiGraph`
  - node attribute’ları: `name, x, y, has_metro, has_bus, has_train, has_bike`
  - edge attribute’ları: `mode, travel_time, cost, distance, is_transfer`

### `src/utils.py`
- `load_default_graph()`
  - proje kökünden `data/` dizinini bulup grafı yükler
- `path_stats(G, path)`
  - toplam süre, maliyet, mesafe, aktarma sayısı, kullanılan mod listesi

### `src/astar_solver.py`
- `heuristic(G, u, v)`:
  - düğümlerin `(x,y)` koordinatlarına göre öklid mesafe temelli bir tahmin
- `solve_astar_simple(...)`
- `solve_astar_constrained(...)`
  - `allowed_modes`, `max_cost`, `max_time` ile kısıtlı arama

### `src/raptor_solver.py`
- `raptor_like(...)`
  - round bazlı en erken varış zamanlarını dener (basitleştirilmiş RAPTOR yaklaşımı)

### `src/nsga_solver.py`
- `run_nsga2(G, start, goal, n_generations, pop_size, middle_len, ...)`
  - DEAP kullanarak NSGA-II
  - amaçlar: (süre, maliyet, aktarma) gibi metrikleri aynı anda iyileştirmek

### `src/visualization.py`
- `draw_graph(G, ...)`
- `draw_path(G, path, ...)`

---
