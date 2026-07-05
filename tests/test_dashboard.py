from loam import dashboard
from loam.config import PLACES
from loam.world import World


def test_render_page_shows_the_world():
    w = World.seeded(n_agents=6, seed=7)
    w.run(20)
    page = dashboard.render_page(w)
    assert page.startswith("<!DOCTYPE html>")
    assert f"tick {w.tick}" in page
    for place in PLACES:
        assert place in page
    a = next(iter(w.agents.values()))
    assert a.name in page
    assert "shared tongue" in page and "bloom" in page


def test_refresh_meta_is_opt_in():
    w = World.seeded(n_agents=3, seed=7)
    assert 'http-equiv="refresh"' not in dashboard.render_page(w)
    assert 'content="3"' in dashboard.render_page(w, refresh=3)


def test_tribe_members_share_a_colour():
    w = World.seeded(n_agents=4, seed=7)
    # make a1 speak a0's whole tongue -> same tribe, same colour
    w.agents["a1"].language.word_of = dict(w.agents["a0"].language.word_of)
    colors = dashboard._tribe_colors(w)
    assert colors[w.agents["a0"].name] == colors[w.agents["a1"].name]
    assert colors[w.agents["a0"].name] != dashboard._LONE


def test_dashboard_surfaces_the_web():
    page = dashboard.render_page(World.seeded(n_agents=8, seed=7))
    assert "the ties that bind" in page
    assert 'class="bond"' in page or 'class="fric"' in page
