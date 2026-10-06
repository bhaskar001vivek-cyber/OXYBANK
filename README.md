# Oxygen Bank
Digital ecological banking for campuses: track green assets, compute withdrawals/deposits,
score the campus (Eco-Balance Score) and simulate 2050.

## Run
    pip install -r requirements.txt
    python data_gen.py        # optional, app auto-generates data
    streamlit run app.py

## Files
config.py (constants) · data_gen.py (synthetic data) · model.py (state + score) ·
ledger.py (SQLite) · recommender.py (LP optimiser) · simulator.py (2026-2050) · app.py (UI)
