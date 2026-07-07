"""The world — a society that must feed itself, ages, dies, and breeds, whether
or not you are watching.

Each tick: bloom regrows in the wild; every living being decides and acts
(forage, grow, eat, give, seize, speak, mate, move, rest, or turn to you);
pregnancies advance and children are born; then the body's toll is taken —
metabolism, aging, and death. Out of need, risk, kinship, and a free field of
action, a history accumulates that no one scripted.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import config
from .agent import Agent
from .cognition import Cognition, Decision, RuleCognition
from .config import PLACES, SOCIAL_WANTS
from .language import Utterance
from .player import Player


@dataclass
class World:
    seed: int = 7
    tick: int = 0
    agents: dict[str, Agent] = field(default_factory=dict)
    monsters: list = field(default_factory=list)            # live monster entities
    bloom: dict[str, float] = field(default_factory=dict)   # wild stock per place
    feed: list[str] = field(default_factory=list)
    utterances: list[Utterance] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)
    fallen: list[dict] = field(default_factory=list)        # obituaries
    tally: dict[str, int] = field(default_factory=dict)     # lifetime event counts
    predator: str = ""                                      # where the beast prowls
    next_index: int = 0
    present: bool = False
    name: str = ""            # a named base/playthrough ("" = the scratch world)
    role: str = "play"        # "base" (immutable template) or "play" (mutable run)
    forked_from: str = ""     # the base a playthrough was forked from
    player: Player = field(default_factory=Player)   # you — your growing understanding
    cognition: Cognition = field(default_factory=RuleCognition, repr=False)

    def rifts(self) -> list:
        from . import rifts
        return rifts.open_rifts(self)

    # ---- construction -----------------------------------------------------
    @classmethod
    def seeded(cls, n_agents: int = 6, seed: int = 7,
               imported: list[dict] | None = None, weaver=None) -> "World":
        """Wake a village. `imported` characters (saved atoms) take the first
        founder slots as strangers here; fresh beings fill the rest up to
        `n_agents`. All of them are then woven into one web by `weaver`
        (the deterministic rule weaver by default)."""
        w = cls(seed=seed)
        idx = 0
        if imported:
            from . import character
            for atom in imported:
                a = character.from_atom(atom, f"a{idx}")
                w.agents[a.id] = a
                idx += 1
        while idx < n_agents:
            a = Agent.born(idx)
            w.agents[a.id] = a
            idx += 1
        w.next_index = idx
        for place, d in PLACES.items():
            w.bloom[place] = d["wild"] * config.WILD_MAX_SCALE * 0.5   # half-stocked at genesis
        w.predator = config.PREDATOR_PLACES[0]
        from . import genesis
        weave = weaver or genesis.RuleWeaver()
        bonds, frictions = weave.weave(w.agents.values(), seed)
        w._log(f"A world wakes with {idx} beings at {config.STARTING_PLACE}.")
        if imported:
            w._log(f"{len(imported)} of them came from other worlds, strangers here.")
        if bonds or frictions:
            w._log(f"They are no strangers: {bonds} bonds and {frictions} old "
                   f"frictions already run between them.")
        return w

    # ---- queries ----------------------------------------------------------
    def living(self) -> list[Agent]:
        return [a for a in self.agents.values() if a.alive]

    def co_located(self, agent: Agent) -> list[Agent]:
        return [a for a in self.agents.values()
                if a.alive and a.id != agent.id and a.location == agent.location]

    def tier_now(self, pivotal: bool = False) -> str:
        if self.present:
            return config.PIVOTAL if pivotal else config.REFLECTIVE
        return config.ROUTINE

    # ---- time -------------------------------------------------------------
    @property
    def day(self) -> int:
        return self.tick // config.TICKS_PER_DAY + 1

    @property
    def time_of_day(self) -> float:
        """0.0 at midnight through to 1.0 — the fraction of the day elapsed."""
        return (self.tick % config.TICKS_PER_DAY) / config.TICKS_PER_DAY

    def phase(self) -> str:
        t = self.time_of_day
        if t < 0.15:
            return "night"
        if t < 0.28:
            return "dawn"
        if t < 0.50:
            return "morning"
        if t < 0.72:
            return "afternoon"
        if t < 0.85:
            return "dusk"
        return "night"

    def _bump(self, key: str, n: int = 1) -> None:
        self.tally[key] = self.tally.get(key, 0) + n

    # ---- the loop ---------------------------------------------------------
    def _rng(self) -> random.Random:
        return random.Random(f"{self.seed}:{self.tick}")

    def step(self) -> None:
        self.tick += 1
        rng = self._rng()
        self._regrow(rng)
        self._roam_predator(rng)
        order = sorted(self.living(), key=lambda a: a.id)
        rng.shuffle(order)
        for agent in order:
            if agent.alive:
                self.cognition_decide_and_apply(agent, rng)
        self._gestate(rng)
        self._reap()
        if self.tick == 1 or self.tick % 10 == 0:
            from . import metrics
            self.history.append(metrics.snapshot(self))

    def cognition_decide_and_apply(self, agent: Agent, rng: random.Random) -> None:
        decision = self.cognition.decide(agent, self, rng)
        self._apply(agent, decision, rng)

    def run(self, ticks: int) -> None:
        for _ in range(ticks):
            if not self.living():
                self._log("The world falls silent. No one remains.")
                break
            self.step()

    def _regrow(self, rng: random.Random) -> None:
        for place, d in PLACES.items():
            if d["wild"] <= 0:
                continue
            ceiling = d["wild"] * config.WILD_MAX_SCALE
            self.bloom[place] = min(
                ceiling,
                self.bloom.get(place, 0.0) + d["wild"] * config.WILD_REGROW_SCALE * rng.uniform(0.5, 1.5),
            )

    def _roam_predator(self, rng: random.Random) -> None:
        """The beast prowls toward where beings gather in the wild — picking off
        the exposed, but wary of a true crowd."""
        crowds = [(p, sum(1 for a in self.living() if a.location == p))
                  for p in config.PREDATOR_PLACES]
        drawn = [(p, n) for p, n in crowds if n > 0]
        if drawn:
            most = max(n for _, n in drawn)
            self.predator = rng.choice([p for p, n in drawn if n == most])
        else:
            self.predator = rng.choice(config.PREDATOR_PLACES)

    # ---- applying a decision ---------------------------------------------
    def _apply(self, agent: Agent, d: Decision, rng: random.Random) -> None:
        agent.last_thought = d.thought
        k = d.kind
        if k == "move" and d.place and d.place != agent.location and d.place in PLACES:
            agent.location = d.place
            agent.memory.remember(self.tick, f"went to {d.place}")
        elif k == "forage":
            self._forage(agent, rng)
        elif k == "grow":
            self._grow(agent, rng)
        elif k == "eat":
            self._eat(agent)
        elif k == "give":
            self._transfer(agent, d.target, rng, hostile=False)
        elif k == "seize":
            self._transfer(agent, d.target, rng, hostile=True)
        elif k == "mate":
            self._mate(agent, d.target, rng)
        elif k == "speak" and d.target in self.agents:
            self._speak(agent, self.agents[d.target])
        elif k == "trade" and d.good:
            self.hand_goods(agent, d.target, d.good, rng)
        elif k == "work":
            self.do_craft(agent, agent.vocation, rng)
        elif k == "seek":
            self._speak_to_you(agent)
        else:
            agent.memory.remember(self.tick, "rested")
            if agent.location == config.STARTING_PLACE:
                agent.vitality = min(self._vcap(agent), agent.vitality + 0.01)  # home comforts

    # ---- ecology ----------------------------------------------------------
    def _forage(self, agent: Agent, rng: random.Random) -> None:
        d = PLACES[agent.location]
        stock = self.bloom.get(agent.location, 0.0)
        if d["wild"] <= 0 or stock <= 0.01:
            agent.memory.remember(self.tick, f"found no wild bloom at {agent.location}")
            return
        skill = agent.genome.forage_skill
        gathered = min(stock, d["wild"] * (0.4 + 0.6 * skill) * config.FORAGE_YIELD_SCALE)
        self.bloom[agent.location] = stock - gathered
        agent.bloom += gathered
        agent.memory.remember(self.tick, f"foraged {gathered:.1f} bloom at {agent.location}")
        self._bump("forage_trips")
        # the beast: deadly to the lone forager, survivable in a group
        if agent.location == self.predator:
            group = 1 + len(self.co_located(agent))
            if group >= config.PREDATOR_DRIVEN_OFF:
                agent.memory.remember(self.tick, "the beast circled, but we were enough to face it")
            elif rng.random() < config.PREDATOR_LETHAL * (1 - 0.4 * skill) / group:
                self._die(agent, "predator", f"was taken by the beast at {agent.location}")
                return
        if rng.random() < d["danger"] * (1 - 0.5 * skill):     # the terrain itself
            if rng.random() < config.FORAGE_LETHAL * d["danger"] * (1 - skill):
                self._die(agent, "forage", f"was lost foraging in {agent.location}")
            else:
                agent.vitality -= config.FORAGE_INJURY_COST
                agent.memory.remember(self.tick, f"was hurt foraging in {agent.location}")

    def _grow(self, agent: Agent, rng: random.Random) -> None:
        if not PLACES[agent.location]["arable"]:
            agent.memory.remember(self.tick, f"the ground at {agent.location} won't take seed")
            return
        skill = agent.genome.grow_skill
        soil = self.bloom.get(agent.location, 0.0)
        # exhausted soil or plain bad luck: the crop fails, and no one is told why
        if soil < config.GROW_SOIL_MIN or rng.random() >= config.GROW_BASE_SUCCESS + config.GROW_SKILL_BONUS * skill:
            agent.memory.remember(self.tick, "tended the ground, but it gave nothing — why?")
            self._bump("crop_failures")
            return
        y = min(soil, config.GROW_YIELD * (0.5 + skill))
        self.bloom[agent.location] = soil - y
        agent.bloom += y
        agent.memory.remember(self.tick, f"grew {y:.1f} bloom at {agent.location}")
        self._bump("harvests")

    def _eat(self, agent: Agent) -> None:
        if agent.bloom <= 0.01:
            agent.memory.remember(self.tick, "had nothing to eat")
            return
        amt = min(agent.bloom, config.EAT_PER_TICK)
        agent.bloom -= amt
        agent.vitality = min(self._vcap(agent), agent.vitality + amt * config.EAT_RESTORE)
        agent.memory.remember(self.tick, f"ate {amt:.1f} bloom")

    def _transfer(self, giver: Agent, target_id: str | None, rng: random.Random, *, hostile: bool) -> None:
        target = self.agents.get(target_id or "")
        if target is None or not target.alive or target.location != giver.location:
            giver.memory.remember(self.tick, "reached for someone who wasn't there")
            return
        if hostile:
            if target.bloom <= 0.01:
                giver.memory.remember(self.tick, f"tried to take from {target.name}, who had nothing")
                return
            taken = min(target.bloom, 1.5)
            target.bloom -= taken
            giver.bloom += taken
            target.vitality -= 0.15
            giver.warm_to(target.id, -2.0)
            target.warm_to(giver.id, -3.0)
            self._bump("seizures")
            giver.memory.remember(self.tick, f"seized {taken:.1f} bloom from {target.name}")
            target.memory.remember(self.tick, f"{giver.name} took bloom from me by force")
            self._log(f"{giver.name} seized bloom from {target.name}.")
            if target.vitality <= 0:
                self._die(target, "violence", f"was killed by {giver.name} over bloom")
        else:
            if giver.bloom <= 0.01:
                giver.memory.remember(self.tick, "had nothing to give")
                return
            given = min(giver.bloom, 1.0)
            giver.bloom -= given
            target.bloom += given
            giver.warm_to(target.id, 1.5)
            target.warm_to(giver.id, 2.0)
            self._bump("gifts")
            giver.memory.remember(self.tick, f"gave {given:.1f} bloom to {target.name}")
            target.memory.remember(self.tick, f"{giver.name} gave me bloom")
            self._log(f"{giver.name} gave bloom to {target.name}.")

    # ---- combat -----------------------------------------------------------
    def strike(self, attacker, defender, rng: random.Random) -> dict:
        """Resolve one blow between any two fighters — being or monster. Damage
        comes off the defender's vitality; a felled being dies and a felled monster
        is cleared, and the attacker earns xp (and may level up)."""
        from . import bestiary, combat
        dmg = combat.hit_damage(attacker, defender, rng)
        defender.vitality -= dmg
        slain = defender.vitality <= 0
        levels = 0
        if slain:
            if isinstance(defender, bestiary.Monster):
                defender.alive = False
                if defender in self.monsters:
                    self.monsters.remove(defender)
                reward = defender.xp_reward
                self._bump("monsters_felled")
                self._log(f"{getattr(attacker, 'name', 'a fighter')} felled a {defender.kind}.")
            else:
                self._die(defender, "violence", f"was slain by {getattr(attacker, 'name', 'a foe')}")
                reward = config.XP_PER_KILL * defender.level
            if hasattr(attacker, "xp"):
                levels = combat.award_xp(attacker, reward)
                if levels and hasattr(attacker, "memory"):
                    attacker.memory.remember(self.tick, f"grew stronger — level {attacker.level}")
                    self._log(f"{attacker.name} reached level {attacker.level}.")
        return {"ok": True, "damage": dmg, "slain": slain, "levels": levels}

    def attack(self, attacker_id: str, target_id: str, rng: random.Random) -> dict:
        """One being strikes another beside it — with the ill will it earns."""
        a = self.agents.get(attacker_id)
        t = self.agents.get(target_id)
        if a is None or t is None or not a.alive or not t.alive or t.location != a.location:
            return {"ok": False}
        a.warm_to(t.id, -3.0)
        t.warm_to(a.id, -4.0)
        self._bump("attacks")
        a.memory.remember(self.tick, f"struck {t.name}")
        t.memory.remember(self.tick, f"was struck by {a.name}")
        return self.strike(a, t, rng)

    def spawn_monster(self, kind: str, location: str, level: int = 1):
        """Add a monster of `kind` at a place (None if the kind is unknown)."""
        from . import bestiary
        if kind not in bestiary.BESTIARY:
            return None
        m = bestiary.spawn(kind, location, level)
        self.monsters.append(m)
        return m

    # ---- the trades -------------------------------------------------------
    def hand_goods(self, giver: Agent, taker_id: str | None, good: str,
                   rng: random.Random) -> dict:
        """Pass a surplus good to a neighbour whose trade can use it. Goodwill,
        like a gift — it warms the bond and makes the craft economy circulate."""
        taker = self.agents.get(taker_id or "")
        have = giver.goods.get(good, 0.0)
        if taker is None or not taker.alive or taker.location != giver.location or have < 0.5:
            giver.memory.remember(self.tick, "had nothing worth passing on")
            return {"ok": False}
        amt = min(have, 2.0)
        giver.goods[good] = have - amt
        taker.goods[good] = taker.goods.get(good, 0.0) + amt
        giver.warm_to(taker.id, 1.0)
        taker.warm_to(giver.id, 1.5)
        self._bump("trades")
        giver.memory.remember(self.tick, f"gave {amt:g} {good} to {taker.name}")
        taker.memory.remember(self.tick, f"{giver.name} gave me {amt:g} {good} for my work")
        self._log(f"{giver.name} handed {good} to {taker.name}.")
        return {"ok": True, "good": good, "amount": amt}

    def do_craft(self, agent: Agent, profession: str, rng: random.Random):
        """A being works a profession: turns effort (and inputs) into goods,
        maybe taking a mishap. Returns the Outcome (ok=False if it can't be done
        here). The goods economy — never touches bloom or hunger."""
        from . import crafts
        prof = crafts.PROFESSIONS.get(profession)
        if prof is None or not agent.alive:
            return crafts.Outcome(False, reason=f"no such trade: {profession}")
        outcome = crafts.perform(prof, skill=agent.genome.craft_skill,
                                  location=agent.location, goods=agent.goods, rng=rng)
        if not outcome.ok:
            agent.memory.remember(self.tick, outcome.reason)
            return outcome
        made = ", ".join(f"{amt:g} {g}" for g, amt in outcome.produced.items())
        agent.memory.remember(self.tick, f"worked {profession} — made {made}")
        self._bump(f"craft_{profession}")
        if outcome.fatal:
            self._die(agent, "mishap", f"was lost to a mishap while {profession}")
        elif outcome.hurt:
            agent.vitality -= config.CRAFT_INJURY_COST
            agent.memory.remember(self.tick, f"was hurt {profession}")
        return outcome

    def monsters_at(self, location: str) -> list:
        return [m for m in self.monsters if m.alive and m.location == location]

    def populate_zone(self, name: str, rng: random.Random, count: int | None = None) -> list:
        """Roll a zone's spawn table into live monsters here (empty if unknown)."""
        from . import zones
        if name not in zones.ZONES:
            return []
        spawned = zones.populate(name, rng, count)
        self.monsters.extend(spawned)
        return spawned

    # ---- procreation ------------------------------------------------------
    def _mate(self, agent: Agent, target_id: str | None, rng: random.Random) -> None:
        target = self.agents.get(target_id or "")
        if target is None or not target.alive or target.location != agent.location:
            agent.memory.remember(self.tick, "reached for a partner who wasn't there")
            return
        if not (self._fertile(agent) and self._fertile(target)):
            agent.memory.remember(self.tick, f"the time with {target.name} wasn't right")
            return
        if agent.affinity(target.id) < 0 or target.affinity(agent.id) < 0:
            agent.memory.remember(self.tick, f"reached for {target.name}, but there was no trust")
            return
        agent.gestation = config.GESTATION_TICKS
        agent.mate_id = target.id
        agent.warm_to(target.id, 3.0)
        target.warm_to(agent.id, 3.0)
        self._bump("matings")
        agent.memory.remember(self.tick, f"conceived a child with {target.name}")
        target.memory.remember(self.tick, f"conceived a child with {agent.name}")
        self._log(f"{agent.name} and {target.name} are expecting a child.")

    def _fertile(self, a: Agent) -> bool:
        return (a.is_adult and a.gestation == 0 and a.vitality >= config.MATE_MIN_VITALITY
                and a.age < a.genome.lifespan * config.FERTILE_UNTIL_FRACTION)

    def _gestate(self, rng: random.Random) -> None:
        for carrier in list(self.living()):
            if carrier.gestation <= 0:
                continue
            carrier.gestation -= 1
            if carrier.gestation == 0:
                self._birth(carrier, rng)

    def _birth(self, carrier: Agent, rng: random.Random) -> None:
        mate = self.agents.get(carrier.mate_id)
        if mate is None or not mate.alive:
            mate = carrier  # the other parent is gone; the line continues through one
        child_id = f"a{self.next_index}"
        self.next_index += 1
        child = Agent.child(child_id, carrier, mate, rng)
        self.agents[child_id] = child
        carrier.vitality -= config.BIRTH_COST
        carrier.mate_id = ""
        self._bump("births")
        carrier.memory.remember(self.tick, f"bore a child, {child.name}")
        self._log(f"{child.name} is born to {carrier.name}"
                  f"{'' if mate is carrier else ' and ' + mate.name} (generation {child.generation}).")
        if carrier.vitality <= 0:
            self._die(carrier, "childbirth", f"died bringing {child.name} into the world")

    # ---- speech (understanding is native for kin, earned for strangers) ----
    def _speak(self, speaker: Agent, listener: Agent) -> None:
        if listener.location != speaker.location or not listener.alive:
            return
        concept = speaker.wants.focus
        word = speaker.language.say(concept)
        self.utterances.append(Utterance(self.tick, speaker.id, listener.id, word, concept))
        speaker.memory.remember(self.tick, f'said "{word}" ({concept}) to {listener.name}')
        if listener.comprehends(word) is not None:
            self._understood(speaker, listener, concept)
            return
        if concept in PLACES.get(listener.location, {}).get("affords", ()):
            if listener.lexicon.observe(word, concept, config.GROUNDING_THRESHOLD):
                self._breakthrough(speaker, listener, concept, word)
            else:
                listener.memory.remember(self.tick, f'heard "{word}" from {speaker.name} — a guess forms')
        else:
            listener.memory.remember(self.tick, f'heard "{word}" from {speaker.name} — meaning unclear')

    def _understood(self, speaker: Agent, listener: Agent, concept: str) -> None:
        speaker.warm_to(listener.id, 0.5)
        listener.warm_to(speaker.id, 0.5)
        if concept in SOCIAL_WANTS:
            speaker.wants.satisfy()
            listener.wants.satisfy(0.25)
        listener.memory.remember(self.tick, f"understood {speaker.name}: {concept}")

    def _breakthrough(self, speaker: Agent, listener: Agent, concept: str, word: str) -> None:
        speaker.warm_to(listener.id, 1.5)
        listener.warm_to(speaker.id, 1.5)
        listener.memory.remember(self.tick, f'LEARNED "{word}" = {concept} (from {speaker.name})')
        self._log(f'{listener.name} learned that {speaker.name}\'s "{word}" means {concept}.')

    def _speak_to_you(self, speaker: Agent) -> None:
        concept = speaker.wants.focus
        word = speaker.language.say(concept)
        self.utterances.append(Utterance(self.tick, speaker.id, "glenn", word, concept))
        speaker.wants.satisfy(0.25)
        speaker.memory.remember(self.tick, f'turned to you, said "{word}" ({concept})')
        self._log(f'{speaker.name} → you: "{word}" ({concept})')

    # ---- the body's toll --------------------------------------------------
    def _vcap(self, a: Agent) -> float:
        senescence_age = a.genome.lifespan * config.SENESCENCE
        if a.age <= senescence_age:
            return 1.0
        span = a.genome.lifespan * (1 - config.SENESCENCE)
        return max(0.2, 1.0 - (a.age - senescence_age) / span * 0.8)

    def _reap(self) -> None:
        for a in list(self.living()):
            a.age += 1
            a.vitality = min(self._vcap(a), a.vitality - config.METABOLISM)
            if a.vitality <= 0:
                self._die(a, "hunger", "starved")
            elif a.age >= a.genome.lifespan:
                self._die(a, "age", "died of old age")

    def _die(self, a: Agent, cause: str, text: str) -> None:
        if not a.alive:
            return
        a.alive = False
        self._bump(f"deaths_{cause}")
        self.fallen.append({"id": a.id, "name": a.name, "cause": cause, "tick": self.tick,
                            "age": a.age, "generation": a.generation})
        self._log(f"{a.name} {text} (age {a.age}, gen {a.generation}).")
        for other in self.living():
            if other.affinity(a.id) > 5:
                other.memory.remember(self.tick, f"grieved {a.name}, who is gone")
        self.agents.pop(a.id, None)

    # ---- your levers (the gardener, not the god) --------------------------
    def aid(self, agent_id: str) -> dict:
        """The quest primitive. You sit with a family member: you ease their day,
        and where a kinmate is beside them you broker one of that kin's words to
        them (advancing THEIR understanding of each other). In helping them, your
        own understanding of their family deepens a small, trust-gated step — and
        when it crosses a milestone you *earn one of their words*, a prize. Enough
        of this, against their distrust, and you understand the family — a rift
        closed."""
        from . import rifts
        a = self.agents.get(agent_id)
        if a is None or not a.alive:
            return {"ok": False, "reason": "no one there to help"}
        from . import bonds
        fam = rifts.family_of(a)
        a.vitality = min(self._vcap(a), a.vitality + config.AID_BOON)
        a.memory.remember(self.tick, "the one who listens sat with me")
        brokered = self._broker_among_kin(a, fam)
        before = self.player.of(fam)
        prize = self.player.deepen(fam, config.UNDERSTAND_STEP)
        level = self.player.of(fam)
        closed = level >= 1.0 and before < 1.0
        # helping this person also deepens your bond with them
        b_before = bonds.tier(self.player.bond(a.id))
        bond = self.player.deepen_bond(a.id, bonds.growth(self.player.bond(a.id), bonds.attraction(a)))
        b_now = bonds.tier(bond)
        self._log(f"You sat with {a.name} of {fam} — you understand them "
                  f"better ({int(level * 100)}%).")
        if prize:
            self._log(f'You earned the {fam}\'s word for "{prize}" — trust, hard-won.')
        if b_now != b_before:
            self._log(f"You and {a.name} are {b_now} now.")
        if closed:
            self._log(f"You have come to understand the {fam} family completely.")
        return {"ok": True, "family": fam, "level": level, "closed": closed,
                "prize": prize, "brokered": brokered, "bond": bond, "bond_tier": b_now}

    def practice_trade(self, trade: str) -> dict:
        """Ply a trade yourself (the resolved stand-in for its mini-game): your
        skill in it grows through the doing, and you advance with every family
        whose trade it is — slowly, against their distrust, a word at a time. A
        surer hand earns a family's trust a little faster."""
        from . import crafts, rifts
        if trade not in crafts.PROFESSIONS and trade != "combat":
            return {"ok": False, "reason": f"no such trade: {trade}"}
        skill = self.player.practice(trade)
        advanced = []
        for fam in rifts.factions_of_trade(self, trade):
            before = self.player.of(fam)
            prize = self.player.deepen(fam, config.UNDERSTAND_STEP * (0.7 + 0.6 * skill))
            advanced.append({"family": fam, "level": self.player.of(fam),
                             "prize": prize, "closed": self.player.of(fam) >= 1.0 and before < 1.0})
        self._log(f"You practised {trade} — your skill is now {int(skill * 100)}%.")
        for adv in advanced:
            if adv["prize"]:
                self._log(f'The {adv["family"]}, whose trade this is, warm to you: '
                          f'you earned their word for "{adv["prize"]}".')
        return {"ok": True, "trade": trade, "skill": skill, "advanced": advanced}

    def marry(self, being_id: str) -> dict:
        """Wed a being you have come to love. Only when the bond has grown to
        betrothal, and only if you are not already wed."""
        from . import bonds
        a = self.agents.get(being_id)
        if a is None or not a.alive:
            return {"ok": False, "reason": "there is no one here by that name"}
        if self.player.spouse:
            spouse = self.agents.get(self.player.spouse)
            return {"ok": False, "reason": f"you are already wed to "
                    f"{spouse.name if spouse else 'someone'}"}
        if not a.is_adult:
            return {"ok": False, "reason": f"{a.name} is too young"}
        if not bonds.can_marry(self.player.bond(being_id)):
            return {"ok": False, "reason": f"you and {a.name} are only "
                    f"{bonds.tier(self.player.bond(being_id))} — a marriage must be grown to"}
        self.player.spouse = being_id
        self.player.bonds[being_id] = 1.0
        a.memory.remember(self.tick, "was wed to the one who understands")
        self._bump("marriages")
        self._log(f"You and {a.name} are wed.")
        return {"ok": True, "spouse": being_id, "name": a.name}

    def have_child(self, rng: random.Random) -> dict:
        """A child comes to you and the one you wed — a family, nothing more.
        Kept apart from the village's own procreation; this line runs through you."""
        if not self.player.spouse:
            return {"ok": False, "reason": "you have no one to raise a child with"}
        spouse = self.agents.get(self.player.spouse)
        if spouse is None or not spouse.alive:
            return {"ok": False, "reason": "the one you wed is gone"}
        from .agent import Agent
        from .genome import Genome
        from .language import PrivateLanguage
        you = Agent(id="you", name=self.player.name or "You",
                    genome=Genome.genesis(f"you:{self.name or 'scratch'}"),
                    language=PrivateLanguage.for_agent("you"), generation=0)
        child_id = f"a{self.next_index}"
        self.next_index += 1
        child = Agent.child(child_id, spouse, you, rng)
        child.parents = (spouse.id, "you")
        child.story = f"your child, with {spouse.name}"
        self.agents[child_id] = child
        self.player.children.append(child_id)
        self._bump("player_children")
        spouse.memory.remember(self.tick, f"a child, {child.name}, came to us")
        self._log(f"A child, {child.name}, comes to you and {spouse.name} (generation {child.generation}).")
        return {"ok": True, "child": child_id, "name": child.name, "generation": child.generation}

    def _broker_among_kin(self, a: Agent, fam: str) -> dict | None:
        """Teach a family member one word a kinmate beside them already speaks —
        the gardener helping kin reach each other."""
        from . import rifts
        for other in self.co_located(a):
            if rifts.family_of(other) != fam:
                continue
            for concept in config.CONCEPTS:
                word = other.language.say(concept)
                if a.comprehends(word) is None:
                    a.lexicon.teach(word, concept)
                    a.memory.remember(self.tick, f'you helped: "{word}" = {concept} (from {other.name})')
                    a.warm_to(other.id, 0.5)
                    other.warm_to(a.id, 0.5)
                    return {"learner": a.id, "from": other.id, "word": word, "concept": concept}
        return None

    def translate(self, symbol: str, for_agent_id: str) -> str:
        listener = self.agents.get(for_agent_id)
        if listener is None:
            return f"No such being: {for_agent_id}"
        for owner in self.agents.values():
            concept = owner.language.understand(symbol)
            if concept is not None:
                listener.lexicon.teach(symbol, concept)
                listener.memory.remember(self.tick, f'you taught: "{symbol}" = {concept}')
                self._log(f'You told {listener.name} that "{symbol}" means {concept}.')
                return f'{listener.name} now understands "{symbol}" = {concept}.'
        return f'No one in this world speaks "{symbol}".'

    def visit(self, agent_id: str) -> str:
        a = self.agents.get(agent_id)
        if a is None:
            gone = next((f for f in self.fallen if f["id"] == agent_id), None)
            if gone:
                return f'{gone["name"]} is gone — {gone["cause"]} at tick {gone["tick"]} (age {gone["age"]}).'
            return f"No such being: {agent_id}"
        g = a.genome
        learned = ", ".join(f'"{w}"={c}' for w, c in a.lexicon.known.items()) or "nothing yet"
        recent = "\n    ".join(a.memory.recent()) or "(no memories)"
        friends = sorted(a.relationships.items(), key=lambda kv: kv[1], reverse=True)
        bonds = ", ".join(f"{self.agents[i].name}({v:+.0f})"
                          for i, v in friends[:3] if i in self.agents) or "no one yet"
        preg = f", carrying a child ({a.gestation} ticks left)" if a.gestation else ""
        story_line = f"  story: {a.story}\n" if a.story else ""
        goods = ", ".join(f"{amt:g} {gd}" for gd, amt in a.goods.items() if amt >= 0.05) or "nothing"
        trade = f"{a.vocation}" if a.vocation else "no trade"
        return (
            f"{a.name} ({a.id}) — at {a.location}, generation {a.generation}\n"
            f"{story_line}"
            f"  body: {a.condition} (vitality {a.vitality:.2f}), "
            f"age {a.age // config.TICKS_PER_DAY}d of ~{g.lifespan // config.TICKS_PER_DAY}d, "
            f"holding {a.bloom:.1f} bloom{preg}\n"
            f"  trade: {trade} (level {a.level}); holds {goods}\n"
            f"  gifts: forage {g.forage_skill:.2f}, grow {g.grow_skill:.2f}, "
            f"craft {g.craft_skill:.2f}, bravery {g.bravery:.2f}\n"
            f"  wants: {a.wants.describe()}\n"
            f"  thought: {a.last_thought or '(quiet)'}\n"
            f"  closest to: {bonds}\n"
            f"  understands: {learned}\n"
            f"  lately:\n    {recent}"
        )

    def _log(self, text: str) -> None:
        self.feed.append(f"[t{self.tick}] {text}")
