"""Central place for every constant. Tune these to your own campus."""
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
TREES_CSV = DATA_DIR / "trees.csv"
POP_CSV = DATA_DIR / "population_history.csv"
DB_PATH = DATA_DIR / "oxygen_bank.db"

CAMPUS_CENTER = (28.5449, 77.3330)  # approx Noida; change to your campus

# ---- Science constants (rough, editable) ----
EMISSION_FACTOR = 0.82          # kg CO2 per kWh (Indian grid, approx)
OTHER_KG_PER_PERSON = 250       # transport/waste kg CO2 per person per year
WATER_L_PER_PERSON_DAY = 70
RAINFALL_MM = 700
RUNOFF_COEFF = 0.8
HARVEST_L_PER_M2 = RAINFALL_MM * RUNOFF_COEFF   # 1 mm on 1 m2 = 1 litre

CO2_PER_MATURE_TREE = 25.0      # kg CO2 / year
CANOPY_PER_MATURE_TREE = 25.0   # m2 of shade
MATURITY_YEARS = 15
SPACE_PER_TREE_M2 = 25.0
SOLAR_KWH_PER_M2 = 150.0
GREEN_ROOF_CO2 = 1.5            # kg CO2 / m2 / year
SOLAR_SHADE_CREDIT = 0.5        # canopy panels give partial cooling credit

# ---- Withdrawal (development) effects ----
ENERGY_PER_BUILT_M2 = 30        # kWh / year per m2 built
BUILT_M2_PER_PERSON = 15
GREEN_LOSS_FRACTION = 0.5       # share of footprint that was green land
TREES_LOST_PER_BUILT_M2 = 0.01

# ---- Score targets (what counts as "100%") ----
CARBON_OFFSET_TARGET = 0.25     # offset 25% of emissions
WATER_HARVEST_TARGET = 0.30     # harvest 30% of water demand
GREEN_COVER_TARGET = 0.33       # 33% green cover
WEIGHTS = {"carbon": 0.35, "water": 0.30, "cooling": 0.35}
HEALTHY_MIN = 70
OVERDRAFT_BELOW = 40

# ---- Deposits: effect per unit + cost in INR ----
DEPOSITS = {
    "plant_trees": {"label": "Plant trees", "unit": "trees",
        "carbon": CO2_PER_MATURE_TREE, "water": 0.0, "green": CANOPY_PER_MATURE_TREE,
        "cost": 600, "ground_m2": SPACE_PER_TREE_M2, "roof_m2": 0},
    "green_roof": {"label": "Green roof", "unit": "m²",
        "carbon": GREEN_ROOF_CO2, "water": 0.0, "green": 1.0,
        "cost": 1800, "ground_m2": 0, "roof_m2": 1},
    "solar_canopy": {"label": "Solar canopy", "unit": "m² panel",
        "carbon": SOLAR_KWH_PER_M2 * EMISSION_FACTOR, "water": 0.0, "green": SOLAR_SHADE_CREDIT,
        "cost": 7000, "ground_m2": 0, "roof_m2": 1},
    "rainwater_harvest": {"label": "Rainwater harvesting", "unit": "m² catchment",
        "carbon": 0.0, "water": HARVEST_L_PER_M2 / 1000, "green": 0.0,
        "cost": 250, "ground_m2": 0, "roof_m2": 0},
    "shaded_area": {"label": "Shaded green area", "unit": "m²",
        "carbon": 0.0, "water": 0.0, "green": 1.0,
        "cost": 500, "ground_m2": 1, "roof_m2": 0},
}

WITHDRAWALS = {
    "tree_loss": {"label": "Tree loss", "unit": "trees"},
    "construction": {"label": "New construction", "unit": "m² built-up"},
    "energy_increase": {"label": "Energy increase", "unit": "kWh/year"},
    "population_increase": {"label": "Population increase", "unit": "people"},
}

# ---- Campus baseline (trees come from data/trees.csv) ----
BASELINE = dict(
    total_area_m2=400_000, lawn_m2=40_000, green_roof_m2=1_500, shaded_m2=2_000,
    solar_m2=2_500, rain_catchment_m2=30_000, energy_kwh=1_800_000,
    population=4_000, plantable_m2=50_000, roof_free_m2=40_000,
)
