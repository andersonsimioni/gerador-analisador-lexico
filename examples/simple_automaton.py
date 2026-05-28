from src.automata import FiniteAutomaton


def build_binary_ending_with_one() -> FiniteAutomaton:
    automaton = FiniteAutomaton("binary_ending_with_one")

    automaton.add_state("q0", initial=True)
    automaton.add_state("q1", final=True)

    automaton.add_transition("q0", "0", "q0")
    automaton.add_transition("q0", "1", "q1")
    automaton.add_transition("q1", "0", "q0")
    automaton.add_transition("q1", "1", "q1")

    return automaton


def main() -> None:
    automaton = build_binary_ending_with_one()
    samples = ["0", "1", "10", "101", "111", "1000"]

    for sample in samples:
        result = "aceita" if automaton.accepts(sample) else "rejeita"
        print(f"{sample}: {result}")


if __name__ == "__main__":
    main()
