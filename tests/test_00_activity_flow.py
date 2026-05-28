import unittest


class ActivityFlowTest(unittest.TestCase):
    def test_person_1_flow(self) -> None:
        from tests.test_finite_automaton import FiniteAutomatonTest
        from tests.test_regex_parser import RegexParserTest

        ordered_cases = [
            RegexParserTest,
            FiniteAutomatonTest,
        ]

        result = unittest.TestResult()
        loader = unittest.TestLoader()

        for test_case in ordered_cases:
            suite = loader.loadTestsFromTestCase(test_case)
            suite.run(result)

        if not result.wasSuccessful():
            messages = []
            for test, error in result.failures + result.errors:
                messages.append(f"{test.id()}\n{error}")
            self.fail("\n\n".join(messages))


if __name__ == "__main__":
    unittest.main()
