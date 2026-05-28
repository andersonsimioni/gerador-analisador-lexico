from src.regex_parser import parse_definitions_file


def main() -> None:
    definitions = parse_definitions_file("examples/lexical_definitions.txt")

    for definition in definitions:
        print(f"{definition.name}: {definition.expression}")
        print("tokens:", [(token.kind, token.value) for token in definition.tokens])
        print("root:", definition.root.kind)
        print("nullable:", definition.root.nullable)
        print("firstpos:", sorted(definition.root.firstpos))
        print("lastpos:", sorted(definition.root.lastpos))
        print("positions:", definition.positions)
        print("followpos:", {key: sorted(value) for key, value in definition.followpos.items()})
        print()


if __name__ == "__main__":
    main()
