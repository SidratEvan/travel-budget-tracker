# ---------- Primary transport costs (city-to-city) ----------

def flight_cost(dest, travelers, chosen_airline=None):
    flights = dest.get("flights", [])
    if not flights:
        return None
    if chosen_airline:
        for f in flights:
            if f["airline"] == chosen_airline:
                return f["estCost"] * travelers
    cheapest = min(flights, key=lambda f: f["estCost"])
    return cheapest["estCost"] * travelers

def bus_cost(dest, travelers):
    bus = dest.get("bus")
    return (bus["estCost"] * travelers) if bus else None

def drive_breakdown(dest, days, own_car=False, rental=False):
    """Intercity driving: round-trip fuel + optional rental/day (1 car per group)."""
    d = dest.get("drive", {})
    km = float(dest.get("distanceKm", 0))          # round-trip distance
    l_per_100 = float(d.get("carLper100km", 8.0))
    fuel_price = float(d.get("fuelPricePerL", 1.6))

    liters = (km / 100.0) * l_per_100
    fuel = liters * fuel_price

    rent = 0.0
    if rental and not own_car:
        rent = float(d.get("rentalPerDay", 0)) * days

    return round(fuel, 2), round(rent, 2)

def drive_cost(dest, days, own_car=False, rental=False):
    fuel, rent = drive_breakdown(dest, days, own_car=own_car, rental=rental)
    return fuel + rent

def transport_cost(dest, mode, travelers, days, own_car=False, rental=False, airline=None):
    if mode == "Flight":
        return flight_cost(dest, travelers, chosen_airline=airline)
    if mode == "Bus":
        return bus_cost(dest, travelers)
    if mode == "Drive":
        return drive_cost(dest, days, own_car=own_car, rental=rental)
    return 0.0

# ---------- Destination (local) mobility costs ----------

def local_drive_breakdown(dest, days, option, local_km_per_day=30.0):
    """
    Local mobility inside the destination city.
    option: "None", "Public transit", "Rent a car", "Use own car"
    - For car options, estimate local fuel on ~30 km/day.
    - Rent a car adds rentalPerDay * days (1 car per group).
    """
    d = dest.get("drive", {})
    l_per_100 = float(d.get("carLper100km", 8.0))
    fuel_price = float(d.get("fuelPricePerL", 1.6))

    if option in ("None", "Public transit"):
        return 0.0, 0.0  # fuel, rental

    # local driving estimate
    local_km = float(local_km_per_day) * days
    liters = (local_km / 100.0) * l_per_100
    fuel = liters * fuel_price

    rent = 0.0
    if option == "Rent a car":
        rent = float(d.get("rentalPerDay", 0)) * days

    return round(fuel, 2), round(rent, 2)

def local_mobility_cost(dest, days, option):
    fuel, rent = local_drive_breakdown(dest, days, option)
    return fuel + rent

# ---------- Total + sensitivity ----------

def total_cost(
    dest, days, nights, travelers,
    mode, own_car=False, rental=False, airline=None,
    local_option="None", paid_activities=0
):
    # primary (intercity) transport
    primary = transport_cost(dest, mode, travelers, days, own_car, rental, airline) or 0.0
    # local mobility (inside city)
    local = 0.0
    if mode == "Drive":
        # already have a car at destination; treat local as zero to avoid double-charging
        local = 0.0
    else:
        local = local_mobility_cost(dest, days, local_option) or 0.0

    stay = dest["stay"]["perNight"] * nights * travelers
    food = dest["food"]["perDay"] * days * travelers
    paid = max(0, paid_activities)

    return {
        "transport": round(primary, 2),
        "local": round(local, 2),
        "stay": round(stay, 2),
        "food": round(food, 2),
        "paid": round(paid, 2),
        "total": round(primary + local + stay + food + paid, 2),
    }

def adjust_for_sensitivity(breakdown, delta):
    """
    +/- budget effect:
      +$ -> add to 'paid' first (experiences), then 'stay'
      -$ -> cut 'paid' first, then trim 'stay' (never below 0)
    """
    b = breakdown.copy()
    if delta > 0:
        add = delta
        bump = min(40, add)
        b["paid"] += bump
        add -= bump
        if add > 0:
            b["stay"] += add
    else:
        cut = abs(delta)
        if b["paid"] >= cut:
            b["paid"] -= cut
            cut = 0
        else:
            cut -= b["paid"]
            b["paid"] = 0
        if cut > 0:
            b["stay"] = max(0, b["stay"] - cut)

    b["total"] = round(b["transport"] + b["local"] + b["stay"] + b["food"] + b["paid"], 2)
    return b
