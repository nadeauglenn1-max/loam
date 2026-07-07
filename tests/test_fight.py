"""The combat scene's timing — striking, the foe's blows, fleeing."""
from loam import bestiary, cast
from loam.game.combat import Fight


def _fight(skill, kind):
    w = cast.build_base(seed=7)
    w.player.skills["combat"] = skill
    return Fight(w, bestiary.spawn(kind, level=1))


def test_striking_a_weak_foe_to_the_finish_wins_and_teaches_you():
    f = _fight(0.6, "cave rat")
    before = f.world.player.skill("combat")
    for _ in range(40):
        f.cooldown = 0.0                       # let the test strike freely
        f.strike()
        if f.over:
            break
    assert f.over == "won" and f.reward > 0
    assert f.world.player.skill("combat") > before   # you learned by fighting
    assert f.world.tally.get("felled_by_you") == 1   # and the world remembers it
    assert any("felled" in line for line in f.world.feed)


def test_strike_respects_its_cooldown():
    f = _fight(0.5, "cave troll")              # a troll survives a single blow
    f.strike()
    assert f.cooldown > 0
    hp = f.foe.vitality
    f.strike()                                 # too soon — no blow lands
    assert f.foe.vitality == hp


def test_the_foe_strikes_on_its_cadence_and_can_beat_you():
    f = _fight(0.0, "cave troll")              # a novice against a troll
    before = f.you.vitality
    f.enemy_timer = 0.0
    f.update(0.016)
    assert f.you.vitality < before             # you took a blow
    for _ in range(30):
        f.enemy_timer = 0.0
        f.update(0.016)
        if f.over:
            break
    assert f.over == "lost"
    assert f.world.tally.get("beaten_back") == 1
    assert any("beat you back" in line for line in f.world.feed)


def test_fleeing_ends_the_fight():
    f = _fight(0.5, "wolf")
    f.flee()
    assert f.over == "fled"
    f.strike()                                 # nothing happens once it's over
    assert f.over == "fled"


def test_a_finished_fight_ignores_further_strikes():
    f = _fight(1.0, "cave rat")
    f.cooldown = 0.0
    f.strike()
    while not f.over:
        f.cooldown = 0.0
        f.strike()
    hp = f.foe.vitality
    f.strike()
    assert f.foe.vitality == hp
