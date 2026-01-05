import os
import sys
import streamlit as st
import pandas as pd
import altair as alt

# src klasörünü Python path'ine ekle
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

from graph_builder import build_graph
from astar_solver import solve_astar_constrained
from nsga_solver import run_nsga2

# --- GRAFİ YÜKLE ---
G = build_graph("data/nodes.csv", "data/edges.csv")

st.title("🚇 Multimodal Rota Belirleme ve Optimizasyon")

st.write(
    "Bu demo, Ankara için oluşturduğumuz küçük yapay multimodal harita üzerinde "
    "**A*** (kısıtlı tek amaçlı) ve **NSGA-II** (çok amaçlı) algoritmalarıyla rota "
    "bulmayı ve sonuçları karşılaştırmayı sağlar."
)

# --- ALGORİTMA SEÇİMİ ---
algo = st.radio("Algoritma", ["A* (kısıtlı)", "NSGA-II (çok amaçlı)"])

# --- KULLANICI GİRDİLERİ ---
col1, col2 = st.columns(2)

with col1:
    start = st.selectbox("Başlangıç noktası", list(G.nodes()), index=5)  # varsayılan N6
with col2:
    goal = st.selectbox("Hedef noktası", list(G.nodes()), index=7)       # varsayılan N8

st.subheader("🔧 Mod Seçimi (A* için geçerli)")
available_modes = ["metro", "bus", "train", "walk", "bike", "car"]

allowed_modes = st.multiselect(
    "Kullanılacak ulaşım modlarını seçin:",
    available_modes,
    default=available_modes,
)

st.subheader("⏱️ ⛽ Kısıt Ayarları (A* için)")
max_time = st.slider("Maksimum süre (dakika)", 1, 120, 120)
max_cost = st.slider("Maksimum maliyet (TL)", 0, 100, 100)

if st.button("Rota Bul"):
    if algo.startswith("A*"):
        st.info(f"A* ile **{start} → {goal}** rotası hesaplanıyor...")

        path, t, c = solve_astar_constrained(
            G,
            start,
            goal,
            allowed_modes=allowed_modes,
            max_cost=max_cost,
            max_time=max_time,
        )

        if path is None:
            st.error("❌ Bu kısıtlarla uygun bir rota bulunamadı.")
        else:
            st.success("✔ Rota bulundu! (A*)")
            st.write("**Rota:**", " → ".join(path))
            st.write(f"**Toplam süre:** {t:.1f} dakika")
            st.write(f"**Toplam maliyet:** {c:.1f} TL")

            st.subheader("📍 Adım Adım Yol")
            for i, node in enumerate(path):
                st.write(f"{i+1}. {node} — {G.nodes[node]['name']}")

    else:
        st.info(f"NSGA-II ile **{start} → {goal}** için Pareto-optimal rotalar aranıyor...")

        # NSGA-II şu anda sadece çok amaçlı çalışıyor; A* kısıtlarını kullanmıyor.
        sols = run_nsga2(
            G,
            start,
            goal,
            n_generations=40,
            pop_size=40,
            max_intermediate_len=4,
        )

        if not sols:
            st.error("❌ Geçerli (ceza almamış) çözüm üretilmedi. "
                     "Bu başlangıç–hedef çifti için graf üzerinde yol olmayabilir.")
        else:
            # DataFrame'e dök
            df = pd.DataFrame(
                [
                    {
                        "Rota": " → ".join(s["full_path"]),
                        "Süre (dk)": s["total_time"],
                        "Maliyet (TL)": s["total_cost"],
                        "Aktarma": int(s["transfers"]),
                    }
                    for s in sols
                ]
            )

            st.success(f"✔ {len(sols)} adet Pareto-optimal çözüm bulundu.")
            st.subheader("📊 Pareto Çözümler (NSGA-II)")
            st.dataframe(df, use_container_width=True)

            # --- Pareto scatter grafiği (Süre vs Maliyet) ---
            st.subheader("⚖️ Pareto Grafiği: Süre vs Maliyet")

            chart = (
                alt.Chart(df)
                .mark_circle(size=80)
                .encode(
                    x=alt.X("Süre (dk):Q", title="Toplam Süre (dk)"),
                    y=alt.Y("Maliyet (TL):Q", title="Toplam Maliyet (TL)"),
                    color=alt.Color("Aktarma:Q", title="Aktarma Sayısı"),
                    tooltip=["Rota", "Süre (dk)", "Maliyet (TL)", "Aktarma"],
                )
                .interactive()
            )

            st.altair_chart(chart, use_container_width=True)

            # Zaman açısından en iyi çözüm
            best_by_time = min(sols, key=lambda s: s["total_time"])
            st.subheader("⏱️ Süre açısından en iyi çözüm (NSGA-II)")
            st.write("**Rota:**", " → ".join(best_by_time["full_path"]))
            st.write(
                f"**Süre:** {best_by_time['total_time']:.1f} dk, "
                f"**Maliyet:** {best_by_time['total_cost']:.1f} TL, "
                f"**Aktarma:** {int(best_by_time['transfers'])}"
            )

            st.subheader("📍 Adım Adım Yol (En iyi süreli NSGA-II rotası)")
            for i, node in enumerate(best_by_time["full_path"]):
                st.write(f"{i+1}. {node} — {G.nodes[node]['name']}")
