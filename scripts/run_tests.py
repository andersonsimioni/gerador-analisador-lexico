import sys
import unittest
from pathlib import Path


class VerboseResult(unittest.TextTestResult):
    def startTest(self, test: unittest.TestCase) -> None:
        super().startTest(test)
        self.stream.write(f"\n[TEST] {_test_name(test)}\n")
        self.stream.flush()

    def addSuccess(self, test: unittest.TestCase) -> None:
        super().addSuccess(test)
        self.stream.write(f"[OK] {_test_name(test)}\n")
        self.stream.flush()

    def addFailure(self, test: unittest.TestCase, err) -> None:
        super().addFailure(test, err)
        self.stream.write(f"[FAIL] {_test_name(test)}\n")
        self.stream.flush()

    def addError(self, test: unittest.TestCase, err) -> None:
        super().addError(test, err)
        self.stream.write(f"[ERROR] {_test_name(test)}\n")
        self.stream.flush()


class VerboseRunner(unittest.TextTestRunner):
    resultclass = VerboseResult


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root))

    suite = unittest.defaultTestLoader.discover("tests")
    result = VerboseRunner(verbosity=0).run(suite)
    return 0 if result.wasSuccessful() else 1


def _test_name(test: unittest.TestCase) -> str:
    class_name = test.__class__.__name__.replace("Test", "")
    method_name = test._testMethodName.replace("test_", "").replace("_", " ")
    return f"{class_name}: {method_name}"


if __name__ == "__main__":
    raise SystemExit(main())
