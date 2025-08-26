import json
from pathlib import Path
import streamlit as st
import pandas as pd

from src.cost import (
    total_cost,
    adjust_for_sensitivity,
    flight_cost,
    drive_breakdown,
)

# ---------- Page setup ----------
st.set_page_config(page_title="Travel Budget Planner", page_icon="🌍", layout="wide")
st.title("🌍 Travel Budget Planner")

# ---------- Inputs ----------
top = st.container()
with top:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        budget = st.number_input("Budget (CAD)", min_value=0, value=500, step=10)
    with c2:
        days = st.number_input("Days", min_value=1, max_value=14, value=3)
    with c3:
        travelers = st.number_input("Travelers", min_value=1, max_value=6, value=1)
    with c4:
        depart = st.selectbox("Departure City", ["Saskatoon", "Regina", "Calgary"])

nights = max(0, days - 1)

# Transport mode + drive options
t1, t2 = st.columns([1, 2])
with t1:
    mode = st.selectbox("Transport mode", ["Flight", "Bus", "Drive"])

own_car = False
rental = False
with t2:
    if mode == "Drive":
        drive_choice = st.radio(
            "Driving option",
            ["Own car", "Rent a car"],
            index=0,
            horizontal=True,
            help="Own car → fuel only. Rent a car → fuel + rental per day."
        )
        own_car = (drive_choice == "Own car")
        rental = (drive_choice == "Rent a car")
    else:
        st.caption("Driving options apply only when Transport mode = Drive.")

# ---------- Load data ----------
data_path = Path("data/destinations.json")
if not data_path.exists():
    st.error("Missing data/destinations.json")
    st.stop()

try:
    destinations = json.loads(data_path.read_text(encoding="utf-8"))
except json.JSONDecodeError as e:
    st.error(f"destinations.json is invalid JSON: {e}")
    st.stop()

# ---------- Compute suggestions ----------
results = []
for d in destinations:
    if d.get("from") != depart:
        continue

    breakdown = total_cost(
        d,
        days=days,
        nights=nights,
        travelers=travelers,
        mode=mode,
        own_car=own_car,
        rental=rental,
        airline=None,          # auto-pick cheapest airline for now
        paid_activities=0
    )
    if breakdown["total"] <= budget:
        results.append((d, breakdown))

# sort by cheapest first
results.sort(key=lambda x: x[1]["total"])

# ---------- Show results ----------
st.subheader("Suggestions")
if not results:
    st.info("No trips fit this budget. Try increasing budget, changing transport mode, or reducing days.")
else:
    for d, b in results:
        with st.container(border=True):
            st.markdown(f"### {d['city']} — **Total: ${b['total']:.0f}**")

            c1, c2, c3 = st.columns([2, 2, 3])

            # ---- Cost breakdown + airlines/driving info ----
            with c1:
                st.write("**Cost breakdown**")
                st.caption(f"Transport: ${b['transport']:.0f}")
                st.caption(f"Stay: ${b['stay']:.0f}  |  Food: ${b['food']:.0f}  |  Paid: ${b['paid']:.0f}")

                if mode == "Flight":
                    flights = d.get("flights", [])
                    if flights:
                        cheapest = min(flights, key=lambda f: f["estCost"])["airline"]
                        st.write("**Airlines (one-way est.)**")
                        for f in flights:
                            tag = " (cheapest)" if f["airline"] == cheapest else ""
                            st.caption(f"• {f['airline']}: ${f['estCost']}{tag}")

                if mode == "Drive" and d.get("drive"):
                    fuel, rent_amt = drive_breakdown(d, days, own_car=own_car, rental=rental)
                    km = d.get("distanceKm", 0)
                    st.write("**Driving details**")
                    st.caption(f"Round-trip distance: ~{km} km")
                    if own_car:
                        st.caption(f"Fuel: ${fuel:.0f}  |  Rental: $0  (own car)")
                    else:
                        st.caption(f"Fuel: ${fuel:.0f}  |  Rental: ${rent_amt:.0f}  (for {days} days)")

            # ---- What-if sensitivity table ----
            with c2:
                st.write("**What-if (±$)**")
                deltas = [-200, -100, -20, -10, +10, +20, +100, +200]
                rows = []
                for dv in deltas:
                    adj = adjust_for_sensitivity(b, dv)
                    rows.append(
                        {"Δ": dv, "Total": f"${adj['total']:.0f}", "Stay": f"${adj['stay']:.0f}", "Paid": f"${adj['paid']:.0f}"}
                    )
                st.dataframe(pd.DataFrame(rows), width="stretch", height=220)

            # ---- Simple day-by-day plan ----
            with c3:
                st.write("**Day-by-day plan**")
                acts = d.get("activities", [])
                plan_rows = []
                ai = 0
                for day in range(1, days + 1):
                    a1 = acts[ai % len(acts)]["name"] if acts else "City walk"
                    a2 = acts[(ai + 1) % len(acts)]["name"] if acts else "Local park"
                    plan_rows.append(
                        {"Day": day, "Morning": "Breakfast", "Activity 1": a1,
                         "Lunch": "Lunch", "Activity 2": a2, "Dinner": "Dinner"}
                    )
                    ai += 2
                st.dataframe(pd.DataFrame(plan_rows), width="stretch", height=220)

st.caption("All estimates use local rule-of-thumb data. Future: live prices via APIs and per-airline selection.")
