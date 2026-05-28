from __future__ import annotations

from dataclasses import dataclass

EPSILON = "&"


@dataclass(frozen=True, order=True)
class State:
    name: str
    is_final: bool = False

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Transition:
    source: str
    symbol: str
    target: str

    @property
    def is_epsilon(self) -> bool:
        return self.symbol == EPSILON


class FiniteAutomaton:
    def __init__(self, name: str = "automaton") -> None:
        self.name = name
        self.states: dict[str, State] = {}
        self.initial_state: str | None = None
        self.transitions: list[Transition] = []

    def add_state(self, name: str, *, initial: bool = False, final: bool = False) -> State:
        current = self.states.get(name)
        state = State(name=name, is_final=final or (current.is_final if current else False))
        self.states[name] = state

        if initial:
            self.initial_state = name

        return state

    def add_transition(self, source: str, symbol: str, target: str) -> Transition:
        if source not in self.states:
            self.add_state(source)
        if target not in self.states:
            self.add_state(target)

        transition = Transition(source=source, symbol=symbol, target=target)
        self.transitions.append(transition)
        return transition

    def alphabet(self) -> set[str]:
        return {transition.symbol for transition in self.transitions if not transition.is_epsilon}

    def final_states(self) -> set[str]:
        return {state.name for state in self.states.values() if state.is_final}

    def next_states(self, state_names: set[str], symbol: str) -> set[str]:
        return {
            transition.target
            for transition in self.transitions
            if transition.source in state_names and _symbol_matches(transition.symbol, symbol)
        }

    def epsilon_closure(self, state_names: set[str]) -> set[str]:
        closure = set(state_names)
        pending = list(state_names)

        while pending:
            state = pending.pop()
            for transition in self.transitions:
                if transition.source == state and transition.is_epsilon and transition.target not in closure:
                    closure.add(transition.target)
                    pending.append(transition.target)

        return closure

    def accepts(self, text: str) -> bool:
        return bool(self.match(text))

    def match(self, text: str) -> set[str]:
        self._validate_ready()

        current = self.epsilon_closure({self.initial_state or ""})
        for symbol in text:
            current = self.epsilon_closure(self.next_states(current, symbol))
            if not current:
                return set()

        return current & self.final_states()

    def trace(self, text: str) -> list[tuple[str, set[str]]]:
        self._validate_ready()

        current = self.epsilon_closure({self.initial_state or ""})
        steps = [("", current)]

        for symbol in text:
            current = self.epsilon_closure(self.next_states(current, symbol))
            steps.append((symbol, current))

        return steps

    def as_table(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for transition in self.transitions:
            rows.append(
                {
                    "source": transition.source,
                    "symbol": transition.symbol,
                    "target": transition.target,
                }
            )
        return rows

    def _validate_ready(self) -> None:
        if self.initial_state is None:
            raise ValueError("Automaton has no initial state.")
        if self.initial_state not in self.states:
            raise ValueError(f"Unknown initial state: {self.initial_state}")


def _symbol_matches(expected: str, actual: str) -> bool:
    if expected == actual:
        return True
    if len(actual) == 1 and expected.startswith("[") and expected.endswith("]"):
        return _matches_char_class(expected, actual)
    return False


def _matches_char_class(char_class: str, char: str) -> bool:
    content = char_class[1:-1]
    index = 0

    while index < len(content):
        start, index = _read_class_char(content, index)
        if index + 1 < len(content) and content[index] == "-":
            end, index = _read_class_char(content, index + 1)
            if start <= char <= end:
                return True
            continue
        if char == start:
            return True

    return False


def _read_class_char(content: str, index: int) -> tuple[str, int]:
    if content[index] != "\\":
        return content[index], index + 1

    if index + 1 >= len(content):
        return "\\", index + 1

    escaped = content[index + 1]
    if escaped == "t":
        return "\t", index + 2
    if escaped == "n":
        return "\n", index + 2
    return escaped, index + 2
