import re
import unittest

from src.automata import build_dfa_from_regex
from src.regex_parser import parse_definitions_text, with_end_marker


class RegexToDfaTest(unittest.TestCase):
    def assert_regex_language(
        self,
        definition_text: str,
        accepted: list[str],
        rejected: list[str],
    ) -> None:
        definition = parse_definitions_text(definition_text)[0]
        automaton = build_dfa_from_regex(definition)

        for text in accepted:
            self.assertTrue(
                automaton.accepts(text),
                msg=f"{definition.name} should accept {text!r}",
            )

        for text in rejected:
            self.assertFalse(
                automaton.accepts(text),
                msg=f"{definition.name} should reject {text!r}",
            )

    def assert_is_dfa(self, definition_text: str) -> None:
        definition = parse_definitions_text(definition_text)[0]
        automaton = build_dfa_from_regex(definition)
        seen: set[tuple[str, str]] = set()

        self.assertIsNotNone(automaton.initial_state)
        self.assertNotIn("&", automaton.alphabet())

        for transition in automaton.transitions:
            key = (transition.source, transition.symbol)
            self.assertNotIn(key, seen)
            seen.add(key)

    def assert_matches_python_regex(
        self,
        definition_text: str,
        python_regex: str,
        samples: list[str],
    ) -> None:
        definition = parse_definitions_text(definition_text)[0]
        automaton = build_dfa_from_regex(definition)

        for sample in samples:
            expected = re.fullmatch(python_regex, sample) is not None
            self.assertEqual(
                automaton.accepts(sample),
                expected,
                msg=f"{definition.name} failed for input {sample!r}",
            )

    def test_build_dfa_for_simple_concat(self) -> None:
        definition = parse_definitions_text("word: ab")[0]
        automaton = build_dfa_from_regex(definition)

        self.assertTrue(automaton.accepts("ab"))
        self.assertFalse(automaton.accepts(""))
        self.assertFalse(automaton.accepts("a"))
        self.assertFalse(automaton.accepts("abc"))

    def test_simple_concat_conversion_table_is_clear(self) -> None:
        definition = parse_definitions_text("word: ab")[0]
        automaton = build_dfa_from_regex(definition)

        self.assertEqual(automaton.initial_state, "S0")
        self.assertEqual(automaton.final_states(), {"S2"})
        self.assertEqual(
            automaton.as_table(),
            [
                {"source": "S0", "symbol": "a", "target": "S1"},
                {"source": "S1", "symbol": "b", "target": "S2"},
            ],
        )

    def test_build_dfa_for_union(self) -> None:
        definition = parse_definitions_text("letter: a | b")[0]
        automaton = build_dfa_from_regex(definition)

        self.assertTrue(automaton.accepts("a"))
        self.assertTrue(automaton.accepts("b"))
        self.assertFalse(automaton.accepts("ab"))
        self.assertFalse(automaton.accepts("c"))

    def test_union_conversion_uses_one_final_state_for_equal_followpos(self) -> None:
        definition = parse_definitions_text("letter: a | b")[0]
        automaton = build_dfa_from_regex(definition)

        self.assertEqual(automaton.initial_state, "S0")
        self.assertEqual(automaton.final_states(), {"S1"})
        self.assertEqual(
            automaton.as_table(),
            [
                {"source": "S0", "symbol": "a", "target": "S1"},
                {"source": "S0", "symbol": "b", "target": "S1"},
            ],
        )

    def test_build_dfa_for_star(self) -> None:
        definition = parse_definitions_text("many_a: a*")[0]
        automaton = build_dfa_from_regex(definition)

        self.assertTrue(automaton.accepts(""))
        self.assertTrue(automaton.accepts("a"))
        self.assertTrue(automaton.accepts("aaaa"))
        self.assertFalse(automaton.accepts("b"))

    def test_build_dfa_for_plus_and_optional(self) -> None:
        definition = parse_definitions_text("repeat_b: a?b+")[0]
        automaton = build_dfa_from_regex(definition)

        self.assertTrue(automaton.accepts("b"))
        self.assertTrue(automaton.accepts("ab"))
        self.assertTrue(automaton.accepts("abbb"))
        self.assertFalse(automaton.accepts("a"))
        self.assertFalse(automaton.accepts(""))

    def test_build_dfa_for_char_classes(self) -> None:
        definition = parse_definitions_text("id: [a-zA-Z]([a-zA-Z] | [0-9])*")[0]
        automaton = build_dfa_from_regex(definition)

        self.assertTrue(automaton.accepts("a"))
        self.assertTrue(automaton.accepts("a1"))
        self.assertTrue(automaton.accepts("Alpha123"))
        self.assertFalse(automaton.accepts("1a"))
        self.assertFalse(automaton.accepts(""))

    def test_build_dfa_for_explicit_epsilon(self) -> None:
        definition = parse_definitions_text("empty: &")[0]
        automaton = build_dfa_from_regex(definition)

        self.assertTrue(automaton.accepts(""))
        self.assertFalse(automaton.accepts("a"))

    def test_generated_dfa_recognizes_number_regex_language(self) -> None:
        self.assert_regex_language(
            "num: [1-9]([0-9])* | 0",
            accepted=["0", "1", "9", "10", "42", "3444"],
            rejected=["", "00", "01", "a", "12a"],
        )

    def test_generated_dfa_recognizes_identifier_regex_language(self) -> None:
        self.assert_regex_language(
            "id: [a-zA-Z]([a-zA-Z] | [0-9])*",
            accepted=["a", "A", "a1", "teste2", "Alpha123", "a43teste"],
            rejected=["", "1a", "_abc", "a_1", "abc!"],
        )

    def test_generated_dfa_recognizes_keyword_regex_language(self) -> None:
        self.assert_regex_language(
            "true_keyword: true",
            accepted=["true"],
            rejected=["", "tru", "truee", "false", "True"],
        )

    def test_generated_dfa_recognizes_comment_regex_language(self) -> None:
        self.assert_regex_language(
            "comment: //(a | b | c | [0-9] | [ ])*",
            accepted=["//", "//a", "//abc", "//a b c 123"],
            rejected=["/", "/a", "//x", "//a_b"],
        )

    def test_generated_dfas_are_deterministic(self) -> None:
        definitions = [
            "word: ab",
            "letter: a | b",
            "many_a: a*",
            "repeat_b: a?b+",
            "id: [a-zA-Z]([a-zA-Z] | [0-9])*",
            "num: [1-9]([0-9])* | 0",
            "comment: //(a | b | c | [0-9] | [ ])*",
        ]

        for definition_text in definitions:
            with self.subTest(definition=definition_text):
                self.assert_is_dfa(definition_text)

    def test_complex_regex_for_strings_ending_with_abb(self) -> None:
        self.assert_regex_language(
            "ending_abb: (a | b)*abb",
            accepted=["abb", "aabb", "babb", "abababb", "bbbbabb"],
            rejected=["", "ab", "abba", "abaa", "baab", "ababab"],
        )

    def test_complex_nested_groups_with_optional_and_plus(self) -> None:
        self.assert_regex_language(
            "nested: (a | b)c?(d | e)+",
            accepted=["ad", "ace", "bcd", "bdede", "acddd"],
            rejected=["", "a", "ac", "acdcd", "ccd", "abdd"],
        )

    def test_complex_identifier_with_keyword_like_prefixes(self) -> None:
        self.assert_regex_language(
            "name: [a-zA-Z]([a-zA-Z] | [0-9])*(_([a-zA-Z] | [0-9])+)?",
            accepted=["a", "abc", "abc123", "abc_1", "A9_z3"],
            rejected=["", "1abc", "_abc", "abc_", "abc__1", "abc-1"],
        )

    def test_complex_integer_or_decimal_number(self) -> None:
        self.assert_regex_language(
            "number: ([1-9]([0-9])* | 0)(\\.([0-9])+)?",
            accepted=["0", "1", "42", "1000", "0.5", "10.25", "999.000"],
            rejected=["", "00", "01", ".5", "5.", "5.a", "a5"],
        )

    def test_complex_operator_family(self) -> None:
        self.assert_regex_language(
            "operator: (= | == | < | <= | > | >= | !=)",
            accepted=["=", "==", "<", "<=", ">", ">=", "!="],
            rejected=["", "===", "=>", "<<", "!", "!=="],
        )

    def test_long_input_stress_for_star_loop(self) -> None:
        definition = parse_definitions_text("many: (a | b)*abb")[0]
        automaton = build_dfa_from_regex(definition)

        self.assertTrue(automaton.accepts(("ab" * 500) + "abb"))
        self.assertFalse(automaton.accepts(("ab" * 500) + "aba"))

    def test_compare_complex_regex_with_python_re_samples(self) -> None:
        samples = [
            "",
            "a",
            "b",
            "ab",
            "abc",
            "abcccd",
            "acd",
            "bd",
            "bccd",
            "abccd",
            "abccccd",
            "abcccc",
            "z",
        ]

        self.assert_matches_python_regex(
            "sample: (a | b)c*d?",
            r"(a|b)c*d?",
            samples,
        )

    def test_compare_identifier_regex_with_python_re_samples(self) -> None:
        samples = [
            "",
            "a",
            "A",
            "z9",
            "Z999",
            "abc123",
            "1abc",
            "_abc",
            "abc_",
            "abc!",
        ]

        self.assert_matches_python_regex(
            "id: [a-zA-Z]([a-zA-Z] | [0-9])*",
            r"[a-zA-Z]([a-zA-Z]|[0-9])*",
            samples,
        )

    def test_augmented_tree_adds_end_marker_followpos(self) -> None:
        definition = parse_definitions_text("word: ab")[0]
        augmented = with_end_marker(definition)

        self.assertEqual(augmented.positions, {1: "a", 2: "b", 3: "#"})
        self.assertEqual(augmented.root.firstpos, frozenset({1}))
        self.assertEqual(augmented.root.lastpos, frozenset({3}))
        self.assertEqual(augmented.followpos, {1: {2}, 2: {3}, 3: set()})


if __name__ == "__main__":
    unittest.main()
