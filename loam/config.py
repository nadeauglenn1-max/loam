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

# ---- genesis: the web a village is born into ---------------------------------
# A village does not wake as strangers. Before the first tick its founders are
# already tangled — old friends, kin, a debt owed, a rivalry unsettled. Cognition
# reads these bonds from tick one, so the story starts warm. A web is a property
# of a village: a pair or trio (used only to isolate mechanics in tests) stays a
# clean slate.
WEB_MIN_VILLAGE = 4               # fewer founders than this and no web is woven
WEB_TIES_PER_BEING = 1.6          # ties woven ≈ this × number of founders
WEB_BOND_FRACTION = 0.65          # share of ties that are warmth rather than friction
WEB_BOND_RANGE = (2.5, 7.0)       # affinity magnitude of a bond at genesis
WEB_TENSION_RANGE = (2.5, 6.0)    # affinity magnitude of a friction at genesis
WEB_ASYMMETRY = 0.4               # how unequal the two sides of a tie may be (0 = equal)

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

# ---- time: a day is a set span; the explore client paces it in real time ------
# The sim's atomic step is a decision-tick; TICKS_PER_DAY of them make one day.
# In the terminal the world runs as fast as it can; the explore client paces a
# full day to SECONDS_PER_DAY of real time, so a short session is a day or two,
# not generations. (This is a pacing/clock layer — it does not touch the tuned
# survival balance below.)
TICKS_PER_DAY = 24            # decision-ticks in a day (a tick ≈ an hour)
SECONDS_PER_DAY = 1800        # a day = 30 real minutes in the explore client

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
BRAVERY_MUTATION = 0.12          # std-dev of courage drift — what selection tunes
LIFESPAN_MUTATION = 90           # ± drift of lifespan from parent blend

# ---- the predator ------------------------------------------------------------
# A beast that roams the dangerous places, hunting whoever forages there. Lone
# foragers are easy prey; a group can share the risk and drive it off. The point
# is not death for its own sake — it is the pressure that selects for courage
# that is calibrated: brave enough to eat, not so reckless as to be eaten.
# The beast roams every place that holds food — leaving only the hearth as
# refuge, and the hearth cannot feed a crowd. With no free safe haven, the two
# death-pressures (the beast prunes the reckless, hunger prunes the timid)
# balance, and courage evolves to a calibrated middle instead of collapsing to
# cowardice. (Verified: with a free refuge, bravery floors and the world dwindles.)
PREDATOR_PLACES = ("the meadow", "the mire", "the thornwood", "the deepwood")
PREDATOR_LETHAL = 0.5            # base kill chance when it catches a lone forager
PREDATOR_DRIVEN_OFF = 3          # this many foragers together drive it off (no kill)

# ---- combat & leveling -------------------------------------------------------
# Health is a being's vitality (one bar). Attack/defense are heritable genome
# aptitudes; level and earned xp raise a fighter's effective power. Resolution is
# deterministic given the rng, so the engine is free, testable, and shared by
# villagers, monsters, and the player alike.
ATTACK_DAMAGE = 0.34            # vitality an even-matched clean hit takes
COMBAT_VARIANCE = 0.30         # ± swing on a hit
LEVEL_POWER_GAIN = 0.12        # each level past 1 adds this fraction to attack/defense
XP_PER_LEVEL = 3              # xp to reach the next level = this × current level
XP_PER_KILL = 2              # xp for a defeat = this × the foe's level

# ---- understanding: the story spine ------------------------------------------
# You begin understanding no one, and no family trusts a stranger. Understanding
# is won SLOWLY, against that distrust — a word of theirs is a prize, not a gift.
# Each act deepens your understanding a small step, gated by how far you've come
# (they give little at first, more as trust builds); crossing a milestone earns
# you one of their words. Advancing a family's TRADE is how you advance with them.
UNDERSTAND_STEP = 0.06        # base understanding gained per act (before the distrust gate)
DISTRUST_FLOOR = 0.5          # a stranger earns this fraction of a step; trust lifts it to full
AID_BOON = 0.05              # vitality your help restores to the one you sit with
SKILL_STEP = 0.08            # how fast a trade-skill grows with use (faster while a novice)

# ---- zones -------------------------------------------------------------------
# A zone is a dangerous area with a spawn table (see zones.py). Building a cave
# or dungeon is adding a data row; this is how many monsters a zone holds when
# it is populated, before anyone thins them out.
ZONE_SPAWN_DEFAULT = 3

# ---- professions & goods -----------------------------------------------------
# A profession is a recipe: it draws on a hand's skill (craft_skill), at a place,
# to turn inputs into goods — sometimes at some risk. Fishing, mining, smithing,
# husbandry and the rest are all data rows in crafts.py; adding a trade is adding
# a row. These goods are a wealth-and-equipment economy that rides *beside* the
# tuned survival ecology (bloom/hunger) — a smithed weapon sharpens combat; it is
# not a shortcut around hunger, so the balance below is untouched.
CRAFT_BASE_YIELD = 0.55       # yield multiplier at zero skill…
CRAFT_SKILL_YIELD = 0.9       # …plus this much at full skill (and tools help)
CRAFT_INJURY_COST = 0.14      # vitality lost to a mishap at a risky trade
CRAFT_LETHAL = 0.05           # chance a mishap is truly grave (× risk × 1-skill)
