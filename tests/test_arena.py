"""The fight, resolved — the pure combat model behind the scene."""
import random

from loam import arena, bestiary, cast


def _player(w, skill=0.0):
    w.player.skills["combat"] = skill
    return w.player


def test_a_novice_is_weak_and_skill_makes_a_stronger_fighter():
    w = cast.build_base(seed=7)
    novice = arena.player_fighter(_player(w, 0.0))
    veteran = arena.player_fighter(_player(w, 1.0))
    assert veteran.combat_attack > novice.combat_attack
    assert veteran.combat_defense > novice.combat_defense
    assert veteran.max_vitality > novice.max_vitality


def test_a_blow_hurts_and_bracing_softens_it():
    w = cast.build_base(seed=7)
    you = arena.player_fighter(_player(w, 0.5))
    rat = bestiary.spawn("cave rat")
    open_dmg = arena.resolve_blow(rat, arena.player_fighter(_player(w, 0.5)), random.Random(1))
    braced_dmg = arena.resolve_blow(rat, arena.player_fighter(_player(w, 0.5)), random.Random(1), bracing=True)
    assert braced_dmg < open_dmg
    # a blow depletes vitality and can down a fighter
    you.vitality = 0.05
    arena.resolve_blow(rat, you, random.Random(0))
    assert you.vitality == 0.0 and you.condition == "beaten"


def test_winning_a_fight_grows_your_combat_skill():
    w = cast.build_base(seed=7)
    p = _player(w, 0.0)
    rose = arena.reward_win(p, foe_level=3)
    assert p.skill("combat") > 0.0 and rose > 0


def test_condition_reads_the_wounds():
    f = arena.Fighter("You", 0.5, 0.5, 1.0, 1.0)
    assert f.condition == "steady"
    f.vitality = 0.5
    assert f.condition == "hurt"
    f.vitality = 0.1
    assert f.condition == "reeling"
