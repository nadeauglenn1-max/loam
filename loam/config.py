"""Single source of truth: model tiering, geography, and the constants that
give the world its texture.

The attention/compute economy: cheap cognition keeps the world alive 24/7;
expensive cognition is spent only on pivotal moments (or when you're present).
"""

# ---- Claude model tiers (verified 2026-07-02) ---------------------------------
HAIKU = "claude-haiku-4-5"    # $1 / $5  per Mtok — routine, 24/7 background
SONNET = "claude-sonnet-5"    # $3 / $15 per Mtok — reflection
OPUS = "claude-opus-4-8"      # $5 / $25 per Mtok — pivotal moments

ROUTINE = HAIKU       # an ordinary tick, no one watching
REFLECTIVE = SONNET   # a turning point in a life
PIVOTAL = OPUS        # you're present, or the moment is rare

# Env var names checked (in order) for a live API key when running --real.
API_KEY_ENV_VARS = ("LOAM_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY", "WITNESS_ANTHROPIC_API_KEY")

# ---- what an agent can want ---------------------------------------------------
CONCEPTS = ("company", "food", "safety", "status", "novelty", "rest", "trust")

# Physical wants are met by *being somewhere*; social wants by *being understood*.
PHYSICAL = ("food", "safety", "rest", "novelty")
SOCIAL = ("company", "status", "trust")

# ---- the geography: a handful of places, each affording certain concepts ------
# An agent at a place can have any want that place affords met (physical), and a
# listener there can *ground* a heard word whose meaning that place makes legible.
PLACES: dict[str, tuple[str, ...]] = {
    "the spring": ("food",),
    "the hollow": ("safety", "rest"),
    "the commons": ("company", "status", "trust"),
    "the edge": ("novelty",),
}

# Reverse map: which place best affords a given concept (where a want pulls you).
PLACE_FOR: dict[str, str] = {
    concept: place
    for place, concepts in PLACES.items()
    for concept in concepts
}

STARTING_PLACE = "the commons"   # everyone begins where beings gather

# ---- learning ----------------------------------------------------------------
# Grounded co-occurrences (heard-in-legible-context) before a word is learned
# without your help. Physical words ground where the need is visible; abstract
# ones are harder — which is exactly where your translation matters most.
GROUNDING_THRESHOLD = 3
