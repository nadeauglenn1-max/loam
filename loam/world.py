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


@dataclass
class World:
    seed: int = 7
    tick: int = 0
    agents: dict[str, Agent] = field(default_factory=dict)
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
    cognition: Cognition = field(default_factory=RuleCognition, repr=False)

    # ---- construction -----------------------------------------------------
    @classmethod
    def seeded(cls, n_agents: int = 6, seed: int = 7) -> "World":
        w = cls(seed=seed)
        for i in range(n_agents):
            a = Agent.born(i)
            w.agents[a.id] = a
        w.next_index = n_agents
        for place, d in PLACES.items():
            w.bloom[place] = d["wild"] * config.WILD_MAX_SCALE * 0.5   # half-stocked at genesis
        w.predator = config.PREDATOR_PLACES[0]
        from . import genesis
        bonds, frictions = genesis.weave_web(w.agents.values(), seed)
        w._log(f"A world wakes with {n_agents} beings at {config.STARTING_PLACE}.")
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
        return (
            f"{a.name} ({a.id}) — at {a.location}, generation {a.generation}\n"
            f"  body: {a.condition} (vitality {a.vitality:.2f}), age {a.age}/{g.lifespan}, "
            f"holding {a.bloom:.1f} bloom{preg}\n"
            f"  gifts: forage {g.forage_skill:.2f}, grow {g.grow_skill:.2f}, bravery {g.bravery:.2f}\n"
            f"  wants: {a.wants.describe()}\n"
            f"  thought: {a.last_thought or '(quiet)'}\n"
            f"  closest to: {bonds}\n"
            f"  understands: {learned}\n"
            f"  lately:\n    {recent}"
        )

    def _log(self, text: str) -> None:
        self.feed.append(f"[t{self.tick}] {text}")
