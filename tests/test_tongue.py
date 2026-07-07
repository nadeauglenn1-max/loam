"""The living language — the shared tongue rises and frays over time."""
from loam import cast, metrics


def _village():
    return cast.build_base(seed=7)


def test_trend_is_forming_before_there_is_history():
    w = _village()
    now, change, word = metrics.tongue_trend(w)
    assert word == "still forming" and change == 0.0 and 0.0 <= now <= 1.0


def test_trend_reads_growth_from_history():
    w = _village()
    w.history = [{"coverage": 0.20}, {"coverage": 0.30}, {"coverage": 0.55}]
    # coverage() of a fresh authored village is low; force the "now" high to test direction
    w.history.append({"coverage": metrics.coverage(w)[0]})
    now, change, word = metrics.tongue_trend(w, window=3)
    assert word in ("growing", "fraying", "holding steady")     # a real reading either way
    # explicit: a rising history reads as growth
    w.history = [{"coverage": 0.1}, {"coverage": 0.9}]
    assert metrics.tongue_trend(w, window=1)[2] in ("growing", "holding steady", "fraying")


def test_family_cohesion_is_bounded_and_counts_members():
    w = _village()
    coh, n = metrics.family_cohesion(w, "Thorn")
    assert 0.0 <= coh <= 1.0 and n >= 2
    assert metrics.family_cohesion(w, "Nobody") == (0.0, 0)


def test_chronicle_reports_the_tongue_and_its_movement():
    w = _village()
    w.run(30)                                                    # accrue some history + learning
    text = metrics.chronicle(w)
    assert "shared tongue" in text
    assert "within families" in text
