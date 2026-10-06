"""Core ecological model: state, transactions (withdraw/deposit) and Eco-Balance Score."""
from dataclasses import dataclass, replace
import pandas as pd
import config as C


@dataclass
class CampusState:
    total_area_m2: float
    tree_count: float
    tree_carbon_kg: float
    canopy_m2: float
    lawn_m2: float
    green_roof_m2: float
    shaded_m2: float
    solar_m2: float
    rain_catchment_m2: float
    energy_kwh: float
    population: float
    plantable_m2: float
    roof_free_m2: float


def load_baseline() -> CampusState:
    trees = pd.read_csv(C.TREES_CSV)
    return CampusState(
        tree_count=len(trees),
        tree_carbon_kg=float(trees.co2_kg_per_year.sum()),
        canopy_m2=float(trees.canopy_m2.sum()),
        **C.BASELINE,
    )


def apply_transaction(s: CampusState, category: str, qty: float) -> CampusState:
    """Return a NEW state after one deposit or withdrawal."""
    qty = float(qty)
    if category == "plant_trees":
        return replace(s, tree_count=s.tree_count + qty,
                       tree_carbon_kg=s.tree_carbon_kg + qty * C.CO2_PER_MATURE_TREE,
                       canopy_m2=s.canopy_m2 + qty * C.CANOPY_PER_MATURE_TREE,
                       plantable_m2=max(0, s.plantable_m2 - qty * C.SPACE_PER_TREE_M2))
    if category == "green_roof":
        return replace(s, green_roof_m2=s.green_roof_m2 + qty,
                       roof_free_m2=max(0, s.roof_free_m2 - qty))
    if category == "solar_canopy":
        return replace(s, solar_m2=s.solar_m2 + qty,
                       roof_free_m2=max(0, s.roof_free_m2 - qty))
    if category == "rainwater_harvest":
        return replace(s, rain_catchment_m2=s.rain_catchment_m2 + qty)
    if category == "shaded_area":
        return replace(s, shaded_m2=s.shaded_m2 + qty,
                       plantable_m2=max(0, s.plantable_m2 - qty))
    if category == "tree_loss":
        n = min(qty, s.tree_count)
        avg_c = s.tree_carbon_kg / s.tree_count if s.tree_count else 0
        avg_can = s.canopy_m2 / s.tree_count if s.tree_count else 0
        return replace(s, tree_count=s.tree_count - n,
                       tree_carbon_kg=max(0, s.tree_carbon_kg - n * avg_c),
                       canopy_m2=max(0, s.canopy_m2 - n * avg_can))
    if category == "construction":
        green_loss = qty * C.GREEN_LOSS_FRACTION
        s = replace(s, energy_kwh=s.energy_kwh + qty * C.ENERGY_PER_BUILT_M2,
                    population=s.population + qty / C.BUILT_M2_PER_PERSON,
                    lawn_m2=max(0, s.lawn_m2 - green_loss),
                    plantable_m2=max(0, s.plantable_m2 - green_loss))
        return apply_transaction(s, "tree_loss", qty * C.TREES_LOST_PER_BUILT_M2)
    if category == "energy_increase":
        return replace(s, energy_kwh=s.energy_kwh + qty)
    if category == "population_increase":
        return replace(s, population=s.population + qty)
    raise ValueError(f"Unknown category: {category}")


def _pillar(value, target):
    score = min(100.0, 100.0 * value / target) if target > 0 else 100.0
    return {"value": value, "target": target, "score": score}


def compute_metrics(s: CampusState) -> dict:
    emissions = s.energy_kwh * C.EMISSION_FACTOR + s.population * C.OTHER_KG_PER_PERSON
    offsets = (s.tree_carbon_kg + s.green_roof_m2 * C.GREEN_ROOF_CO2
               + s.solar_m2 * C.SOLAR_KWH_PER_M2 * C.EMISSION_FACTOR)

    water_demand = s.population * C.WATER_L_PER_PERSON_DAY * 365 / 1000   # m3/yr
    harvest = s.rain_catchment_m2 * C.HARVEST_L_PER_M2 / 1000             # m3/yr

    green = (s.canopy_m2 + s.lawn_m2 + s.green_roof_m2 + s.shaded_m2
             + s.solar_m2 * C.SOLAR_SHADE_CREDIT)

    pillars = {
        "carbon": _pillar(offsets, C.CARBON_OFFSET_TARGET * emissions),
        "water": _pillar(harvest, C.WATER_HARVEST_TARGET * water_demand),
        "cooling": _pillar(green, C.GREEN_COVER_TARGET * s.total_area_m2),
    }
    score = sum(C.WEIGHTS[k] * pillars[k]["score"] for k in pillars)
    if score >= C.HEALTHY_MIN:
        status = "Healthy"
    elif score >= C.OVERDRAFT_BELOW:
        status = "Warning"
    else:
        status = "Ecological Overdraft"
    return {
        "pillars": pillars, "eco_score": score, "status": status,
        "emissions_kg": emissions, "offsets_kg": offsets,
        "water_demand_m3": water_demand, "green_cover_pct": 100 * green / s.total_area_m2,
    }
