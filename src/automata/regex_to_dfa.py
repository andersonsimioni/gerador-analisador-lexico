from __future__ import annotations

from src.regex_parser import RegexDefinition, with_end_marker

from .finite_automaton import FiniteAutomaton


def build_dfa_from_regex(definition: RegexDefinition) -> FiniteAutomaton:
    augmented = with_end_marker(definition)
    marker_position = _find_marker_position(augmented.positions)
    symbols = sorted({symbol for symbol in augmented.positions.values() if symbol != "#"})

    automaton = FiniteAutomaton(definition.name)
    state_names: dict[frozenset[int], str] = {}
    pending: list[frozenset[int]] = []

    def add_state(positions: frozenset[int]) -> str:
        if positions not in state_names:
            name = f"S{len(state_names)}"
            state_names[positions] = name
            pending.append(positions)
            automaton.add_state(
                name,
                initial=len(state_names) == 1,
                final=marker_position in positions,
            )
        return state_names[positions]

    add_state(augmented.root.firstpos)

    while pending:
        current_positions = pending.pop(0)
        current_state = state_names[current_positions]

        for symbol in symbols:
            target_positions = _move(current_positions, symbol, augmented)
            if not target_positions:
                continue

            target_state = add_state(frozenset(target_positions))
            automaton.add_transition(current_state, symbol, target_state)

    return automaton


def _move(positions: frozenset[int], symbol: str, definition: RegexDefinition) -> set[int]:
    target: set[int] = set()
    for position in positions:
        if definition.positions[position] == symbol:
            target.update(definition.followpos[position])
    return target


def _find_marker_position(positions: dict[int, str]) -> int:
    for position, symbol in positions.items():
        if symbol == "#":
            return position
    raise ValueError("Augmented tree has no final marker '#'.")
