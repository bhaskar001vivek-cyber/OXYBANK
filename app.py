"""Oxygen Bank - Streamlit dashboard.  Run:  streamlit run app.py"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config as C
import data_gen
import ledger
import model
import recommender
import simulator

st.set_page_config(page_title="Oxygen Bank", page_icon="🌳", layout="wide")

if not C.TREES_CSV.exists():
    data_gen.generate()
ledger.init_db()


def current_state():
    return ledger.replay(model.load_baseline(), ledger.get_transactions())


def gauge(score, status):
    color = "#2e7d32" if score >= C.HEALTHY_MIN else "#f9a825" if score >= C.OVERDRAFT_BELOW else "#c62828"
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score, title={"text": f"Eco-Balance Score · {status}"},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": color},
               "steps": [{"range": [0, C.OVERDRAFT_BELOW], "color": "#ffcdd2"},
                         {"range": [C.OVERDRAFT_BELOW, C.HEALTHY_MIN], "color": "#fff9c4"},
                         {"range": [C.HEALTHY_MIN, 100], "color": "#c8e6c9"}]}))
    fig.update_layout(height=280, margin=dict(t=60, b=10, l=20, r=20))
    return fig


st.sidebar.title("🌳 Oxygen Bank")
page = st.sidebar.radio("Go to", ["Dashboard", "Tree Map", "Ledger", "Recommendations", "2050 Simulator"])
state = current_state()
metrics = model.compute_metrics(state)

# ------------------------------------------------------------------ Dashboard
if page == "Dashboard":
    st.title("Campus Eco-Balance")
    if metrics["status"] == "Ecological Overdraft":
        st.error("⚠️ Campus is in ECOLOGICAL OVERDRAFT. Make deposits.")
    elif metrics["status"] == "Warning":
        st.warning("Campus is in the warning zone.")
    else:
        st.success("Campus ecological account is healthy.")

    c1, c2 = st.columns([1, 1])
    c1.plotly_chart(gauge(metrics["eco_score"], metrics["status"]), use_container_width=True)
    with c2:
        for name, label in [("carbon", "Carbon"), ("water", "Water"), ("cooling", "Cooling / Green cover")]:
            sc = metrics["pillars"][name]["score"]
            st.write(f"**{label}** — {sc:.0f}/100")
            st.progress(min(1.0, sc / 100))

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Trees", f"{int(state.tree_count):,}")
    k2.metric("Population", f"{int(state.population):,}")
    k3.metric("Emissions (t CO₂/yr)", f"{metrics['emissions_kg'] / 1000:,.0f}")
    k4.metric("Green cover", f"{metrics['green_cover_pct']:.1f}%")

# ------------------------------------------------------------------ Tree map
elif page == "Tree Map":
    st.title("Tree Inventory")
    trees = pd.read_csv(C.TREES_CSV)
    st.map(trees, latitude="lat", longitude="lon", size=6)
    st.bar_chart(trees.species.value_counts())
    st.dataframe(trees.head(50), use_container_width=True)

# ------------------------------------------------------------------ Ledger
elif page == "Ledger":
    st.title("Transaction Ledger")
    kind = st.radio("Type", ["Withdrawal", "Deposit"], horizontal=True)
    options = C.WITHDRAWALS if kind == "Withdrawal" else C.DEPOSITS
    with st.form("txn"):
        cat = st.selectbox("Category", list(options), format_func=lambda k: options[k]["label"])
        qty = st.number_input("Quantity", min_value=1.0, value=10.0, step=1.0)
        note = st.text_input("Note (optional)")
        if st.form_submit_button("Record transaction"):
            ledger.add_transaction(kind.lower(), cat, qty, note)
            st.rerun()
    st.caption("Units: " + ", ".join(f"{v['label']} = {v['unit']}" for v in options.values()))

    df = ledger.get_transactions()
    st.subheader("History")
    st.dataframe(df, use_container_width=True)
    if st.button("Reset ledger"):
        ledger.reset()
        st.rerun()

# ------------------------------------------------------------------ Recommendations
elif page == "Recommendations":
    st.title("Deposit Recommender")
    st.write("Finds the cheapest mix of deposits to reach your target score.")
    target = st.slider("Target Eco-Balance Score", 40, 100, 70)
    max_trees = st.slider("Max trees we can plant", 0, 5000, 1500, step=50)
    max_rain = st.slider("Max rainwater catchment (m²)", 0, 100000, 30000, step=1000)

    if st.button("Calculate plan"):
        st.session_state["plan"] = recommender.recommend(state, target, max_trees, max_rain)

    res = st.session_state.get("plan")
    if res:
        if not res["ok"]:
            st.error("No feasible plan with these limits.")
        elif not res["plan"]:
            st.success("No deposits needed — target already met.")
        else:
            st.dataframe(pd.DataFrame(res["plan"]), use_container_width=True)
            st.metric("Total cost (₹)", f"{res['total_cost']:,.0f}")
            a, b = st.columns(2)
            a.metric("Score before", f"{res['before']['eco_score']:.1f}")
            b.metric("Score after", f"{res['after']['eco_score']:.1f}",
                     delta=f"{res['after']['eco_score'] - res['before']['eco_score']:.1f}")
            if st.button("✅ Add plan to ledger as deposits"):
                for item in res["plan"]:
                    ledger.add_transaction("deposit", item["category"], item["quantity"], "Recommended plan")
                st.session_state.pop("plan")
                st.rerun()

# ------------------------------------------------------------------ Simulator
else:
    st.title("2050 Simulator")
    hist = pd.read_csv(C.POP_CSV)
    fitted = simulator.fit_growth_rate(hist.year, hist.population)
    st.caption(f"Growth rate fitted from historical population: {fitted * 100:.1f}%/year")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Growth")
        r = st.slider("Population growth rate (%/yr)", 0.0, 12.0, round(fitted * 100, 1), 0.1) / 100
        cap = st.slider("Max campus population", 5000, 50000, 20000, step=1000)
    with c2:
        st.subheader("Oxygen Bank policy (per year)")
        trees = st.slider("Trees planted", 0, 500, 150, step=10)
        solar = st.slider("Solar canopy (m²)", 0, 2000, 300, step=50)
        roof = st.slider("Green roof (m²)", 0, 2000, 200, step=50)
        rain = st.slider("Rainwater catchment (m²)", 0, 5000, 800, step=100)

    bau = simulator.simulate(state, r=r, capacity=cap)
    plan = simulator.simulate(state, r=r, capacity=cap, trees_per_year=trees,
                              solar_m2_per_year=solar, green_roof_m2_per_year=roof, rain_m2_per_year=rain)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bau.year, y=bau.eco_score, name="Business as usual", line=dict(color="#c62828")))
    fig.add_trace(go.Scatter(x=plan.year, y=plan.eco_score, name="With Oxygen Bank", line=dict(color="#2e7d32")))
    fig.add_hline(y=C.OVERDRAFT_BELOW, line_dash="dash", annotation_text="Overdraft line")
    fig.add_hline(y=C.HEALTHY_MIN, line_dash="dot", annotation_text="Healthy line")
    fig.update_layout(yaxis=dict(range=[0, 100], title="Eco-Balance Score"), height=400)
    st.plotly_chart(fig, use_container_width=True)

    od = simulator.first_overdraft_year(bau)
    m1, m2, m3 = st.columns(3)
    m1.metric("BAU score in 2050", f"{bau.eco_score.iloc[-1]:.0f}")
    m2.metric("Plan score in 2050", f"{plan.eco_score.iloc[-1]:.0f}")
    m3.metric("Overdraft year (BAU)", od if od else "None")
    st.metric("Total plan cost by 2050 (₹)", f"{plan.cum_cost_inr.iloc[-1]:,.0f}")
    st.dataframe(plan[plan.year.isin([2030, 2040, 2050])].round(1), use_container_width=True)
