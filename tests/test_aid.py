"""The quest primitive — helping a family advances them and your understanding."""
from loam import cast, config, rifts
from loam.world import World


def _village():
    w = cast.build_base(seed=7)
    w.role, w.name = "play", "story"
    return w


def test_sitting_with_someone_only_trickles_understanding():
    w = _village()
    sela = next(a for a in w.agents.values() if a.name == "Sela")   # a Thorn
    assert w.player.of("Thorn") == 0.0
    r = w.aid(sela.id)
    assert r["ok"] and r["family"] == "Thorn"
    # H is cheap now — the real understanding is earned by clearing their trouble
    assert w.player.of("Thorn") == config.AID_UNDERSTAND_STEP * config.DISTRUST_FLOOR
    assert w.player.of("Thorn") < config.UNDERSTAND_STEP * config.DISTRUST_FLOOR


def test_enough_help_understands_a_family_and_closes_its_rift():
    w = _village()
    thorns = [a.id for a in w.agents.values() if rifts.family_of(a) == "Thorn"]
    closed = False
    for _ in range(200):                                            # understanding is slow now
        if w.player.understands("Thorn"):
            break
        r = w.aid(thorns[0])
        closed = closed or r["closed"]
    assert w.player.understands("Thorn") and closed
    assert "Thorn" not in {rf.family for rf in w.rifts()}           # rift gone
    w.player.deepen("Thorn", 0.2)
    assert w.player.of("Thorn") == 1.0                             # stays capped


def test_words_come_as_prizes_at_milestones_not_every_step():
    w = _village()
    sela = next(a for a in w.agents.values() if a.name == "Sela")
    prizes = 0
    for _ in range(200):
        if w.player.understands("Thorn"):
            break
        if w.aid(sela.id)["prize"]:
            prizes += 1
    # you earn one word per concept in their tongue — prizes, not a handout each step
    assert 0 < prizes <= len(config.CONCEPTS)
    assert len(w.player.earned("Thorn")) == prizes


def test_helping_advances_them_by_brokering_a_kinmate_word():
    w = _village()
    # put two Thorn kin together somewhere and clear what the learner grasps
    thorns = [a for a in w.agents.values() if rifts.family_of(a) == "Thorn"]
    a, b = thorns[0], thorns[1]
    a.location = b.location
    a.lexicon.known.clear()
    r = w.aid(a.id)
    assert r["brokered"] is not None                               # a word passed between kin
    assert a.comprehends(r["brokered"]["word"]) == r["brokered"]["concept"]


def test_helping_no_one_is_a_no_op():
    w = _village()
    assert not w.aid("nobody")["ok"]
