"""Single source of truth for model tiering — the attention/compute economy.

Cheap cognition keeps the world alive 24/7; expensive cognition is a scarce
resource the world spends only on pivotal moments (or when you're present).
"""

# Claude model IDs (verified 2026-07-02).
HAIKU = "claude-haiku-4-5"    # $1 / $5  per Mtok — routine, 24/7 background
SONNET = "claude-sonnet-5"    # $3 / $15 per Mtok — reflection
OPUS = "claude-opus-4-8"      # $5 / $25 per Mtok — pivotal moments

# Cognition tiers -> model. The world resolves a tier per decision (see world.py).
ROUTINE = HAIKU       # an ordinary tick, no one watching
REFLECTIVE = SONNET   # a turning point in an agent's life
PIVOTAL = OPUS        # you're present, or the moment is rare

# Env var names checked (in order) for a live API key when running --real.
API_KEY_ENV_VARS = ("LOAM_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY", "WITNESS_ANTHROPIC_API_KEY")

# How many grounded co-occurrences before an agent learns a foreign symbol on
# its own (without your translation). Language earned the slow way.
GROUNDING_THRESHOLD = 3
