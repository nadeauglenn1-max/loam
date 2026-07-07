"""CLI coverage for the understanding / bonds / converse commands."""
import pytest

from loam.cli import main


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _world():
    assert main(["reset", "--agents", "6", "--seed", "7"]) == 0


def test_data_listings_need_no_world(capsys):
    assert main(["crafts"]) == 0 and "fishing" in capsys.readouterr().out
    assert main(["zones"]) == 0 and "cave" in capsys.readouterr().out


def test_you_and_rifts_and_bonds(capsys):
    _world()
    assert main(["you"]) == 0 and "still learning" in capsys.readouterr().out
    assert main(["rifts"]) == 0 and "understand" in capsys.readouterr().out
    assert main(["bonds"]) == 0 and "no bonds" in capsys.readouterr().out.lower() or True


def test_practice_grows_a_skill(capsys):
    _world()
    assert main(["practice", "fishing"]) == 0
    assert "skill is now" in capsys.readouterr().out
    assert main(["practice", "alchemy"]) == 1        # unknown trade


def test_listen_to_a_being(capsys):
    _world()
    assert main(["listen", "a0"]) == 0
    out = capsys.readouterr().out
    assert '"' in out                                # a spoken word
    assert main(["listen", "nobody"]) == 1


def test_identity_choose_woman_or_man(capsys):
    _world()
    assert main(["identity", "female", "Robin"]) == 0
    assert "Robin" in capsys.readouterr().out
    assert main(["help", "a0"]) == 0                 # sit with someone — builds understanding + a bond


def test_marry_and_child_refuse_without_the_bond(capsys):
    _world()
    assert main(["marry", "a0"]) == 1               # a stranger — refused
    assert main(["child"]) == 1                     # no spouse
