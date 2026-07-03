"""Single source of truth: model tiers, geography, and the constants that give
the world its stakes — hunger, danger, aging, and heredity.

Balance numbers are tuned on free mock runs before any real-cognition run.
"""

# ---- Claude model tiers (verified 2026-07-02) ---------------------------------
HAIKU = "claude-haiku-4-5"    # $1 / $5  per Mtok — routine, 24/7 background
SONNET = "claude-sonnet-5"    # $3 / $15 per Mtok — reflection
OPUS = "claude-opus-4-8"      # $5 / $25 per Mtok — pivotal moments

ROUTINE = HAIKU
REFLECTIVE = SONNET
PIVOTAL = OPUS

API_KEY_ENV_VARS = ("LOAM_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY", "WITNESS_ANTHROPIC_API_KEY")

# ---- what a being can want / mean (the social & inner world) -------------------
SOCIAL_WANTS = ("company", "status", "trust")   # met by being understood
PLACE_WANTS = ("safety", "rest", "novelty")     # met by being somewhere
CONCEPTS = SOCIAL_WANTS + PLACE_WANTS           # the vocabulary of the tongue

# ---- the map: a larger world, each place with its own bounty and danger --------
# affords : which PLACE_WANTS it satisfies (and where those words are legible)
# danger  : chance-scale of harm while foraging here (0 = safe)
# wild    : richness of wild bloom (spawn/regrow rate and stock ceiling)
# arable  : whether bloom can be grown here
PLACES: dict[str, dict] = {
    "the hearth":    {"affords": ("safety", "rest"),            "danger": 0.00, "wild": 0.35, "arable": True},
    "the commons":   {"affords": ("company", "status", "trust"),"danger": 0.05, "wild": 0.30, "arable": True},
    "the meadow":    {"affords": ("novelty",),                  "danger": 0.12, "wild": 0.55, "arable": True},
    "the mire":      {"affords": (),                            "danger": 0.42, "wild": 0.85, "arable": False},
    "the thornwood": {"affords": (),                            "danger": 0.55, "wild": 1.05, "arable": False},
    "the deepwood":  {"affords": ("novelty",),                  "danger": 0.80, "wild": 1.45, "arable": False},
}

PLACE_FOR: dict[str, str] = {
    want: next(p for p, d in PLACES.items() if want in d["affords"])
    for want in PLACE_WANTS
}

STARTING_PLACE = "the hearth"     # a world begins at home

# ---- language ----------------------------------------------------------------
GROUNDING_THRESHOLD = 3           # legible hearings before a word is learned alone
LANGUAGE_DRIFT = 0.35             # fraction of a child's words freshly coined vs inherited

# ---- bloom: the resource beings must eat to live -------------------------------
METABOLISM = 0.028                # vitality lost per tick just by living
EAT_RESTORE = 0.24               # vitality restored per unit of bloom eaten
EAT_PER_TICK = 1.0               # max bloom a being eats in one meal

# A place's bloom is a finite, regrowing commons. Both foraging (dangerous) and
# growing (safe) draw from it, so crowding depletes the land and caps population.
WILD_MAX_SCALE = 9.0             # a place's bloom ceiling = wild * this
WILD_REGROW_SCALE = 0.9          # bloom regrown per tick = wild * this (sets carrying capacity)

# foraging — rich but dangerous
FORAGE_YIELD_SCALE = 2.0         # bloom gathered = wild * (0.4 + 0.6*skill) * this, capped by stock
FORAGE_INJURY_COST = 0.22        # vitality lost to an injury
FORAGE_LETHAL = 0.14             # chance an injury is fatal (× danger, × 1-skill)

# growing — safe but uncertain, and it exhausts the soil it draws from
GROW_BASE_SUCCESS = 0.5          # success chance floor (skill adds up to +0.4)
GROW_SKILL_BONUS = 0.4
GROW_YIELD = 1.2                 # harvest = min(soil left, this * (0.5 + skill))
GROW_SOIL_MIN = 0.3              # below this the land gives nothing — a crop "fails"

# ---- life & death ------------------------------------------------------------
NEWBORN_VITALITY = 0.6
ADULT_AGE = 60                   # fertile only after this age (in ticks)
SENESCENCE = 0.80                # past lifespan * this, vitality ceiling starts falling

# ---- procreation -------------------------------------------------------------
MATE_MIN_VITALITY = 0.72         # both partners must be genuinely well to breed
GESTATION_TICKS = 55             # a pregnancy's length
BIRTH_COST = 0.38                # vitality the carrier spends bearing a child
FERTILE_UNTIL_FRACTION = 0.7     # fertile until age reaches lifespan * this

# ---- genetics ----------------------------------------------------------------
LIFESPAN_MEAN = 620
LIFESPAN_SPREAD = 180            # ± range around the mean at genesis
SKILL_MUTATION = 0.15            # std-dev of skill drift from parent to child
APPETITE_MUTATION = 0.2          # std-dev of want-appetite drift
LIFESPAN_MUTATION = 90           # ± drift of lifespan from parent blend
