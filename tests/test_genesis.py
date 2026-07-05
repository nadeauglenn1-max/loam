"""The web a village is born into — bonds and frictions before the first tick."""
from loam import config, genesis, persistence
from loam.world import World


def _rels(w: World) -> dict[str, dict[str, float]]:
    return {i: dict(a.relationships) for i, a in w.agents.items()}


def test_a_village_wakes_already_tangled():
    w = World.seeded(n_agents=8, seed=7)
    assert any(a.relationships for a in w.agents.values())   # no one is an island


def test_web_has_both_bonds_and_frictions():
    w = World.seeded(n_agents=10, seed=7)
    affinities = [v for a in w.agents.values() for v in a.relationships.values()]
    assert any(v > 0 for v in affinities)   # warmth
    assert any(v < 0 for v in affinities)   # friction


def test_web_plants_founding_memories_at_tick_zero():
    w = World.seeded(n_agents=8, seed=7)
    assert any(m.startswith("[t0]")
               for a in w.agents.values() for m in a.memory.events)


def test_web_is_deterministic_in_the_seed():
    assert _rels(World.seeded(n_agents=8, seed=7)) == _rels(World.seeded(n_agents=8, seed=7))


def test_a_different_seed_weaves_a_different_web():
    assert _rels(World.seeded(n_agents=8, seed=7)) != _rels(World.seeded(n_agents=8, seed=99))


def test_a_pair_stays_a_clean_slate():
    # below WEB_MIN_VILLAGE no web is woven — tiny fixtures isolate mechanics
    w = World.seeded(n_agents=2, seed=7)
    assert all(not a.relationships for a in w.agents.values())


def test_weave_web_is_safe_for_the_lonely():
    assert genesis.weave_web([], seed=1) == (0, 0)


def test_ties_are_mutual_and_share_a_sign():
    w = World.seeded(n_agents=8, seed=7)
    for a in w.agents.values():
        for other_id, aff in a.relationships.items():
            back = w.agents[other_id].affinity(a.id)
            assert (aff > 0) == (back > 0)   # both sides feel the same kind of tie


def test_ties_may_be_asymmetric_in_strength():
    # with several founders, at least one tie is felt more on one side than the
    # other — the asymmetry that keeps a relationship a story
    w = World.seeded(n_agents=12, seed=7)
    assert any(abs(a.affinity(o)) != abs(w.agents[o].affinity(a.id))
               for a in w.agents.values() for o in a.relationships)


def test_the_web_survives_a_save_and_load(tmp_path):
    w = World.seeded(n_agents=8, seed=7)
    path = tmp_path / "world.json"
    persistence.save(w, path)
    w2 = persistence.load(path)
    for i, a in w.agents.items():
        assert w2.agents[i].relationships == a.relationships


def test_a_larger_village_is_woven_proportionally():
    small = sum(len(a.relationships) for a in World.seeded(n_agents=6, seed=7).agents.values())
    big = sum(len(a.relationships) for a in World.seeded(n_agents=20, seed=7).agents.values())
    assert big > small   # more founders, more ties
