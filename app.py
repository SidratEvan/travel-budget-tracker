import json
from pathlib import Path
import streamlit as st
import pandas as pd

from src.cost import (
    total_cost,
    adjust_for_sensitivity,
    flight_cost,
    drive_breakdown,
    local_drive_breakdown,
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

# Primary transport (city-to-city)
t1, t2 = st.columns([1, 2])
with t1:
    mode = st.selectbox("Primary transport", ["Flight", "Bus", "Drive"])

# Destination mobility (inside city) — shown for all modes
with t2:
    if mode == "Drive":
        st.caption("You arrive by car, so destination mobility is covered by your own car (no extra local cost).")
        local_option = "Use own car"
        own_car = True
        rental = False
    else:
        local_option = st.radio(
            "Destination mobility (inside the city)",
            ["None", "Public transit", "Rent a car", "Use own car"],
            index=1,
            horizontal=True,
            help="Choose how you'll move around once you arrive."
        )
        own_car = False
        rental = False

# Flight/Bus don’t care about own_car/rental for primary, but Drive does:
if mode == "Drive":
    # For intercity Drive, choose own vs rental:
    drv = st.radio(
        "Driving option for the trip",
        ["Own car", "Rent a car"],
        index=0,
        horizontal=True
    )
    own_car = (drv == "Own car")
    rental = (drv == "Rent a car")

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

    # total cost includes primary transport + local mobility + stay + food (+ paid later)
    breakdown = total_cost(
        d,
        days=days,
        nights=nights,
        travelers=travelers,
        mode=mode,
        own_car=own_car,
        rental=rental,
        airline=None,          # cheapest airline auto
        local_option=local_option,
        paid_activities=0
    )
    if breakdown["total"] <= budget:
        results.append((d, breakdown))

# sort by cheapest first
results.sort(key=lambda x: x[1]["total"])

# ---------- Show results ----------
st.subheader("Suggestions")
if not results:
    st.info("No trips fit this budget. Try increasing budget, changing transport, or reducing days.")
else:
    for d, b in results:
        with st.container(border=True):
            st.markdown(f"### {d['city']} — **Total: ${b['total']:.0f}**")

            c1, c2, c3 = st.columns([2, 2, 3])

            # ---- Cost breakdown + transport info ----
            with c1:
                st.write("**Cost breakdown**")
                st.caption(f"Primary transport: ${b['transport']:.0f}")
                st.caption(f"Local mobility: ${b['local']:.0f}")
                st.caption(f"Stay: ${b['stay']:.0f}  |  Food: ${b['food']:.0f}  |  Paid: ${b['paid']:.0f}")

                # Airlines (informational)
                if mode == "Flight":
                    flights = d.get("flights", [])
                    if flights:
                        cheapest = min(flights, key=lambda f: f["estCost"])["airline"]
                        st.write("**Airlines (one-way est.)**")
                        for f in flights:
                            tag = " (cheapest)" if f["airline"] == cheapest else ""
                            st.caption(f"• {f['airline']}: ${f['estCost']}{tag}")

                # Intercity driving details
                if mode == "Drive" and d.get("drive"):
                    fuel, rent_amt = drive_breakdown(d, days, own_car=own_car, rental=rental)
                    km = d.get("distanceKm", 0)
                    st.write("**Intercity driving**")
                    st.caption(f"Round-trip distance: ~{km} km")
                    if own_car:
                        st.caption(f"Fuel: ${fuel:.0f}  |  Rental: $0 (own car)")
                    else:
                        st.caption(f"Fuel: ${fuel:.0f}  |  Rental: ${rent_amt:.0f} ({days} days)")

                # Local mobility details (applies to Flight/Bus; Drive already covered)
                if mode != "Drive":
                    if local_option in ("Rent a car", "Use own car"):
                        lfuel, lrent = local_drive_breakdown(d, days, local_option)
                        st.write("**Local mobility details**")
                        st.caption(f"Local fuel (~30 km/day): ${lfuel:.0f}")
                        st.caption(f"Local rental: ${lrent:.0f}")

            # ---- What-if sensitivity table ----
            with c2:
                st.write("**What-if (±$)**")
                deltas = [-200, -100, -20, -10, +10, +20, +100, +200]
                rows = []
                for dv in deltas:
                    adj = adjust_for_sensitivity(b, dv)
                    rows.append(
                        {
                            "Δ": dv,
                            "Total": f"${adj['total']:.0f}",
                            "Stay": f"${adj['stay']:.0f}",
                            "Paid": f"${adj['paid']:.0f}"
                        }
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

st.caption("Primary transport + destination mobility + stay + food. All numbers are rule-of-thumb for demo; APIs can be added later.")
