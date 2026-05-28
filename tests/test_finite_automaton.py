import unittest

from src.automata import EPSILON, FiniteAutomaton


class FiniteAutomatonTest(unittest.TestCase):
    def test_dfa_accepts_binary_strings_ending_with_one(self) -> None:
        automaton = FiniteAutomaton()
        automaton.add_state("q0", initial=True)
        automaton.add_state("q1", final=True)
        automaton.add_transition("q0", "0", "q0")
        automaton.add_transition("q0", "1", "q1")
        automaton.add_transition("q1", "0", "q0")
        automaton.add_transition("q1", "1", "q1")

        self.assertTrue(automaton.accepts("1"))
        self.assertTrue(automaton.accepts("101"))
        self.assertFalse(automaton.accepts("0"))
        self.assertFalse(automaton.accepts("1000"))

    def test_nfa_accepts_using_epsilon_transition(self) -> None:
        automaton = FiniteAutomaton()
        automaton.add_state("start", initial=True)
        automaton.add_state("word")
        automaton.add_state("end", final=True)
        automaton.add_transition("start", EPSILON, "word")
        automaton.add_transition("word", "a", "word")
        automaton.add_transition("word", "b", "end")

        self.assertTrue(automaton.accepts("b"))
        self.assertTrue(automaton.accepts("aaab"))
        self.assertFalse(automaton.accepts("aaa"))

    def test_match_returns_reached_final_states(self) -> None:
        automaton = FiniteAutomaton()
        automaton.add_state("q0", initial=True)
        automaton.add_state("q1", final=True)
        automaton.add_transition("q0", "a", "q1")

        self.assertEqual(automaton.match("a"), {"q1"})

    def test_nfa_accepts_when_any_branch_reaches_final_state(self) -> None:
        automaton = FiniteAutomaton()
        automaton.add_state("q0", initial=True)
        automaton.add_state("dead")
        automaton.add_state("middle")
        automaton.add_state("end", final=True)

        automaton.add_transition("q0", "a", "dead")
        automaton.add_transition("q0", "a", "middle")
        automaton.add_transition("dead", "b", "dead")
        automaton.add_transition("middle", "b", "end")

        self.assertTrue(automaton.accepts("ab"))
        self.assertFalse(automaton.accepts("a"))

    def test_epsilon_closure_handles_cycles_without_infinite_loop(self) -> None:
        automaton = FiniteAutomaton()
        automaton.add_state("q0", initial=True)
        automaton.add_state("q1")
        automaton.add_state("q2", final=True)

        automaton.add_transition("q0", EPSILON, "q1")
        automaton.add_transition("q1", EPSILON, "q0")
        automaton.add_transition("q1", EPSILON, "q2")

        self.assertEqual(automaton.epsilon_closure({"q0"}), {"q0", "q1", "q2"})
        self.assertTrue(automaton.accepts(""))

    def test_long_input_with_loop_does_not_grow_state_set(self) -> None:
        automaton = FiniteAutomaton()
        automaton.add_state("even", initial=True, final=True)
        automaton.add_state("odd")
        automaton.add_transition("even", "a", "odd")
        automaton.add_transition("odd", "a", "even")

        self.assertTrue(automaton.accepts("a" * 1000))
        self.assertFalse(automaton.accepts("a" * 999))

    def test_match_can_return_multiple_final_states(self) -> None:
        automaton = FiniteAutomaton()
        automaton.add_state("q0", initial=True)
        automaton.add_state("word", final=True)
        automaton.add_state("keyword", final=True)
        automaton.add_transition("q0", "a", "word")
        automaton.add_transition("q0", "a", "keyword")

        self.assertEqual(automaton.match("a"), {"word", "keyword"})

    def test_trace_shows_state_set_after_each_symbol(self) -> None:
        automaton = FiniteAutomaton()
        automaton.add_state("q0", initial=True)
        automaton.add_state("q1")
        automaton.add_state("q2", final=True)
        automaton.add_transition("q0", "a", "q1")
        automaton.add_transition("q1", "b", "q2")

        self.assertEqual(
            automaton.trace("ab"),
            [
                ("", {"q0"}),
                ("a", {"q1"}),
                ("b", {"q2"}),
            ],
        )

    def test_alphabet_ignores_epsilon(self) -> None:
        automaton = FiniteAutomaton()
        automaton.add_state("q0", initial=True)
        automaton.add_state("q1", final=True)
        automaton.add_transition("q0", EPSILON, "q1")
        automaton.add_transition("q1", "a", "q1")
        automaton.add_transition("q1", "b", "q1")

        self.assertEqual(automaton.alphabet(), {"a", "b"})

    def test_as_table_returns_transition_rows(self) -> None:
        automaton = FiniteAutomaton()
        automaton.add_state("q0", initial=True)
        automaton.add_state("q1", final=True)
        automaton.add_transition("q0", "a", "q1")

        self.assertEqual(
            automaton.as_table(),
            [{"source": "q0", "symbol": "a", "target": "q1"}],
        )

    def test_accepts_raises_error_without_initial_state(self) -> None:
        automaton = FiniteAutomaton()
        automaton.add_state("q0", final=True)

        with self.assertRaises(ValueError):
            automaton.accepts("")


if __name__ == "__main__":
    unittest.main()
