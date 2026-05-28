import unittest
from pathlib import Path

from src.regex_parser import parse_definitions_file, parse_definitions_text


class RegexParserTest(unittest.TestCase):
    def test_parse_lexical_definitions(self) -> None:
        text = """
        id: [a-zA-Z]([a-zA-Z] | [0-9])*
        num: [1-9]([0-9])* | 0
        """

        definitions = parse_definitions_text(text)

        self.assertEqual([definition.name for definition in definitions], ["id", "num"])
        self.assertEqual(definitions[0].tokens[0].kind, "CHAR_CLASS")
        self.assertEqual(definitions[0].tokens[1].kind, "CONCAT")
        self.assertEqual(definitions[0].tokens[2].kind, "LPAREN")
        self.assertEqual(definitions[0].tokens[-1].kind, "STAR")
        self.assertEqual(definitions[1].tokens[-1].value, "0")

    def test_insert_concat_tokens_between_adjacent_terms(self) -> None:
        definitions = parse_definitions_text("id: ab(c | d)*")

        token_pairs = [(token.kind, token.value) for token in definitions[0].tokens]

        self.assertEqual(
            token_pairs,
            [
                ("LITERAL", "a"),
                ("CONCAT", ""),
                ("LITERAL", "b"),
                ("CONCAT", ""),
                ("LPAREN", "("),
                ("LITERAL", "c"),
                ("UNION", "|"),
                ("LITERAL", "d"),
                ("RPAREN", ")"),
                ("STAR", "*"),
            ],
        )

    def test_build_syntax_tree_for_concat(self) -> None:
        definition = parse_definitions_text("x: ab")[0]

        self.assertEqual(definition.root.kind, "CONCAT")
        self.assertFalse(definition.root.nullable)
        self.assertEqual(definition.root.firstpos, frozenset({1}))
        self.assertEqual(definition.root.lastpos, frozenset({2}))
        self.assertEqual(definition.positions, {1: "a", 2: "b"})
        self.assertEqual(definition.followpos, {1: {2}, 2: set()})

    def test_build_syntax_tree_for_union_and_star(self) -> None:
        definition = parse_definitions_text("x: (a | b)*c")[0]

        self.assertEqual(definition.root.kind, "CONCAT")
        self.assertFalse(definition.root.nullable)
        self.assertEqual(definition.root.firstpos, frozenset({1, 2, 3}))
        self.assertEqual(definition.root.lastpos, frozenset({3}))
        self.assertEqual(definition.positions, {1: "a", 2: "b", 3: "c"})
        self.assertEqual(definition.followpos, {1: {1, 2, 3}, 2: {1, 2, 3}, 3: set()})

    def test_build_syntax_tree_for_optional_and_plus(self) -> None:
        definition = parse_definitions_text("x: a?b+")[0]

        self.assertEqual(definition.root.kind, "CONCAT")
        self.assertFalse(definition.root.nullable)
        self.assertEqual(definition.root.firstpos, frozenset({1, 2}))
        self.assertEqual(definition.root.lastpos, frozenset({2}))
        self.assertEqual(definition.positions, {1: "a", 2: "b"})
        self.assertEqual(definition.followpos, {1: {2}, 2: {2}})

    def test_epsilon_node_is_nullable_and_has_no_position(self) -> None:
        definition = parse_definitions_text("x: &")[0]

        self.assertEqual(definition.root.kind, "EPSILON")
        self.assertTrue(definition.root.nullable)
        self.assertEqual(definition.root.firstpos, frozenset())
        self.assertEqual(definition.root.lastpos, frozenset())
        self.assertEqual(definition.positions, {})
        self.assertEqual(definition.followpos, {})

    def test_parse_example_file_with_many_definitions(self) -> None:
        definitions = parse_definitions_file(Path("examples/lexical_definitions.txt"))
        names = [definition.name for definition in definitions]

        self.assertEqual(
            names,
            [
                "id",
                "num",
                "whitespace",
                "plus",
                "minus",
                "mult",
                "div",
                "assign",
                "equal",
                "less",
                "greater",
                "open_paren",
                "close_paren",
                "line_comment",
                "true_keyword",
                "false_keyword",
                "epsilon_test",
            ],
        )

    def test_parse_escaped_regex_operators_as_literals(self) -> None:
        text = """
        plus: \\+
        mult: \\*
        open_paren: \\(
        close_paren: \\)
        """

        definitions = parse_definitions_text(text)

        token_pairs = [
            [(token.kind, token.value) for token in definition.tokens]
            for definition in definitions
        ]

        self.assertEqual(token_pairs[0], [("LITERAL", "+")])
        self.assertEqual(token_pairs[1], [("LITERAL", "*")])
        self.assertEqual(token_pairs[2], [("LITERAL", "(")])
        self.assertEqual(token_pairs[3], [("LITERAL", ")")])

    def test_parse_common_language_tokens(self) -> None:
        text = """
        id: [a-zA-Z]([a-zA-Z] | [0-9])*
        integer: [1-9]([0-9])* | 0
        whitespace: ([ ] | [\\t] | [\\n])+
        equal: ==
        line_comment: //(a | b | [0-9] | [ ])*
        epsilon_test: &
        """

        definitions = parse_definitions_text(text)
        tokens_by_name = {definition.name: definition.tokens for definition in definitions}

        self.assertEqual(tokens_by_name["whitespace"][-1].kind, "PLUS")
        self.assertEqual([token.kind for token in tokens_by_name["equal"]], ["LITERAL", "CONCAT", "LITERAL"])
        self.assertEqual([token.value for token in tokens_by_name["equal"]], ["=", "", "="])
        self.assertEqual(tokens_by_name["epsilon_test"][0].kind, "EPSILON")

    def test_ignore_empty_lines_and_comments(self) -> None:
        text = """
        # comment

        er1: a?(a | b)+
        """

        definitions = parse_definitions_text(text)

        self.assertEqual(len(definitions), 1)
        self.assertEqual(definitions[0].name, "er1")

    def test_raise_error_for_invalid_definition(self) -> None:
        with self.assertRaises(ValueError):
            parse_definitions_text("id [a-z]")

    def test_raise_error_for_open_char_class(self) -> None:
        with self.assertRaises(ValueError):
            parse_definitions_text("id: [a-z")


if __name__ == "__main__":
    unittest.main()
