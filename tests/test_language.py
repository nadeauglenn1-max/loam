from loam.config import GROUNDING_THRESHOLD
from loam.language import CONCEPTS, Lexicon, PrivateLanguage, coin_word


def test_coined_words_are_deterministic():
    assert coin_word("a1", "food") == coin_word("a1", "food")
    # Different agents (almost surely) coin different words for the same concept.
    assert coin_word("a1", "food") != coin_word("a2", "food")


def test_private_language_round_trips_every_concept():
    lang = PrivateLanguage.for_agent("a3")
    for c in CONCEPTS:
        word = lang.say(c)
        assert lang.understand(word) == c


def test_foreign_word_is_opaque_until_learned():
    speaker = PrivateLanguage.for_agent("a1")
    word = speaker.say("safety")
    listener = PrivateLanguage.for_agent("a2")
    assert listener.understand(word) is None  # not this tongue


def test_grounded_repetition_eventually_teaches():
    lex = Lexicon()
    word = "kalo"
    learned = False
    for _ in range(GROUNDING_THRESHOLD):
        learned = lex.observe(word, "trust", GROUNDING_THRESHOLD)
    assert learned is True
    assert lex.knows(word)
    assert lex.known[word] == "trust"


def test_translation_teaches_immediately():
    lex = Lexicon()
    lex.teach("mizi", "company")
    assert lex.knows("mizi")
    assert lex.known["mizi"] == "company"


def test_child_inherits_most_of_a_parents_tongue():
    import random

    from loam.config import LANGUAGE_DRIFT
    parent = PrivateLanguage.for_agent("a0")
    child = PrivateLanguage.inherit(parent, "a9", random.Random(0))
    shared = sum(1 for c in CONCEPTS if child.word_of[c] == parent.word_of[c])
    # most words inherited (drift only replaces a minority)
    assert shared >= len(CONCEPTS) * (1 - LANGUAGE_DRIFT) - 1
    # a fully inherited word is understood natively by both
    for c in CONCEPTS:
        if child.word_of[c] == parent.word_of[c]:
            assert parent.understand(child.word_of[c]) == c


def test_no_drift_yields_the_parent_tongue():
    import random
    parent = PrivateLanguage.for_agent("a0")
    child = PrivateLanguage.inherit(parent, "a9", random.Random(0), drift=0.0)
    assert child.word_of == parent.word_of
