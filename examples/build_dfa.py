from src.automata import build_dfa_from_regex
from src.regex_parser import parse_definitions_text


def main() -> None:
    definition = parse_definitions_text("id: [a-zA-Z]([a-zA-Z] | [0-9])*")[0]
    automaton = build_dfa_from_regex(definition)

    for text in ["a", "a1", "Alpha123", "1a"]:
        result = "accepted" if automaton.accepts(text) else "rejected"
        print(f"{text}: {result}")


if __name__ == "__main__":
    main()
