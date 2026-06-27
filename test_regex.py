from pathlib import Path
import sys
import traceback


BASE_DIR = Path(__file__).resolve().parent
AUTOMATO_DIR = BASE_DIR / "automato"


class TestRunner:
    def __init__(self):
        self.total = 0
        self.passed = 0

    def check(self, name, condition, details=""):
        self.total += 1
        if condition:
            self.passed += 1
            print(f"[OK] {name}")
            return

        print(f"[FALHOU] {name}")
        if details:
            print(details)

    def regex_case(self, modules, regex, examples):
        try:
            automato = build_automato_from_regex(modules, regex)
        except Exception:
            for word, expected in examples:
                self.check(f"regex {regex!r}.reconhece({word!r}) == {expected}", False, traceback.format_exc())
            return

        for word, expected in examples:
            name = f"regex {regex!r}.reconhece({word!r}) == {expected}"
            try:
                result = automato.reconhece(word)
                self.check(name, result == expected, f"obtido: {result!r}")
            except Exception:
                self.check(name, False, traceback.format_exc())

    def summary(self):
        failed = self.total - self.passed
        print("\n== Resumo ==")
        print(f"Passou: {self.passed}/{self.total}")
        print(f"Falhou: {failed}/{self.total}")


def add_automato_to_path():
    sys.path.insert(0, str(AUTOMATO_DIR))


def load_modules(runner):
    print("\n== Imports ==")
    modules = {}

    for module_name in ["definicoes", "transicao", "estado", "automato"]:
        try:
            modules[module_name] = __import__(module_name)
            runner.check(f"import {module_name}", True)
        except Exception:
            runner.check(f"import {module_name}", False, traceback.format_exc())
            return None

    return modules


def build_automato_from_regex(modules, regex):
    Automato = modules["automato"].Automato

    if hasattr(Automato, "parse_regex"):
        automato = Automato.parse_regex(regex)
        if automato is None:
            raise ValueError("Automato.parse_regex(regex) retornou None")
        return automato

    raise AttributeError("Esperado Automato.parse_regex(regex) estatico retornando um Automato")


def run_regex_tests(runner, modules):
    cases = [
        # Debug primeiro: simbolos compostos usados como transicoes do AFD.
        ("[a-z]", [("a", True), ("m", True), ("z", True), ("A", False), ("aa", False)]),
        ("[0-9]", [("0", True), ("7", True), ("9", True), ("a", False), ("10", False)]),
        ("[a-c]", [("a", True), ("b", True), ("c", True), ("d", False), ("", False)]),
        ("[x-z]", [("x", True), ("y", True), ("z", True), ("w", False), ("xy", False)]),
        ("[a-zA-Z]", [("a", True), ("Z", True), ("m", True), ("5", False), ("az", False)]),
        ("[a-zA-Z0-9]", [("a", True), ("Z", True), ("5", True), ("_", False), ("a5", False)]),
        (r"\*", [("*", True), ("", False), ("a", False), ("**", False)]),
        (r"\|", [("|", True), ("", False), ("a", False), ("||", False)]),
        (r"\(", [("(", True), (")", False), ("", False), ("((", False)]),
        (r"\[", [("[", True), ("]", False), ("", False), ("[[", False)]),
        (r"\\", [("\\", True), ("", False), ("\\\\", False), ("/", False)]),
        (r"a\*b", [("a*b", True), ("ab", False), ("aaab", False), ("a**b", False)]),
        (r"\(ab\)", [("(ab)", True), ("ab", False), ("(a)", False), ("(ab", False)]),
        # Casos chatos para depurar primeiro: concat implicito, precedencia,
        # parenteses externos, literais escapados e padroes.
        ("a(a|b)*b", [("ab", True), ("aab", True), ("abb", True), ("aa", False), ("ba", False)]),
        ("a(b|c)*d", [("ad", True), ("abd", True), ("acbcd", True), ("ab", False), ("da", False)]),
        ("(a)(b)", [("ab", True), ("a", False), ("b", False), ("", False)]),
        ("(a|b)c", [("ac", True), ("bc", True), ("c", False), ("abc", False)]),
        ("a(b|c)", [("ab", True), ("ac", True), ("a", False), ("abc", False)]),
        ("a|bc", [("a", True), ("bc", True), ("b", False), ("abc", False)]),
        ("ab|c", [("ab", True), ("c", True), ("a", False), ("abc", False)]),
        ("a*b", [("b", True), ("ab", True), ("aaaab", True), ("a", False)]),
        ("ab*", [("a", True), ("ab", True), ("abbbb", True), ("", False)]),
        ("(a|b)*c", [("c", True), ("ac", True), ("bbac", True), ("ca", False)]),
        ("a(b|c)*d", [("ad", True), ("abd", True), ("acbcd", True), ("ab", False)]),
        ("((a|b)c)*", [("", True), ("ac", True), ("bc", True), ("acbc", True), ("a", False)]),
        ("[a-z][0-9]", [("a0", True), ("m5", True), ("z9", True), ("A1", False)]),
        ("[a-z]*", [("", True), ("abcxyz", True), ("ABC", False), ("abc1", False)]),
        (r"a\*b", [("a*b", True), ("ab", False), ("aaab", False), ("a**b", False)]),
        (r"\(ab\)", [("(ab)", True), ("ab", False), ("(a)", False), ("(ab", False)]),
        ("(a|&)*b", [("b", True), ("ab", True), ("aaaab", True), ("a", False)]),
        ("a", [("", False), ("a", True), ("aa", False), ("b", False)]),
        ("[a-z]", [("a", True), ("m", True), ("z", True), ("A", False), ("aa", False)]),
        (r"a\*b", [("a*b", True), ("ab", False), ("aaab", False), ("a**b", False)]),
        ("(a|&)*b", [("b", True), ("ab", True), ("aaaab", True), ("a", False)]),
        ("a(b|c)*d", [("ad", True), ("abd", True), ("acbcd", True), ("ab", False), ("da", False)]),
        ("[a-z]", [("a", True), ("m", True), ("z", True), ("A", False), ("aa", False)]),
        ("[A-Z]", [("A", True), ("M", True), ("Z", True), ("a", False), ("AA", False)]),
        ("[0-9]", [("0", True), ("5", True), ("9", True), ("a", False), ("10", False)]),
        ("[a-c]", [("a", True), ("b", True), ("c", True), ("d", False), ("", False)]),
        ("[x-z]", [("x", True), ("y", True), ("z", True), ("w", False), ("xy", False)]),
        ("[a-z][0-9]", [("a0", True), ("m5", True), ("z9", True), ("A1", False), ("aa", False)]),
        ("[0-9][a-z]", [("0a", True), ("5m", True), ("9z", True), ("a0", False), ("00", False)]),
        ("[a-z]*", [("", True), ("a", True), ("abcxyz", True), ("ABC", False), ("abc1", False)]),
        ("[0-9]*", [("", True), ("0", True), ("123456", True), ("12a", False), ("a12", False)]),
        ("[a-z]|[0-9]", [("a", True), ("z", True), ("0", True), ("9", True), ("A", False)]),
        ("([a-z]|[0-9])*", [("", True), ("abc", True), ("123", True), ("a1b2", True), ("a_B", False)]),
        ("[a-z][a-z]*", [("a", True), ("abc", True), ("zxy", True), ("", False), ("abc1", False)]),
        ("[A-Z][a-z]*", [("A", True), ("Abc", True), ("Zebra", True), ("abc", False), ("A1", False)]),
        ("[a-zA-Z]", [("a", True), ("Z", True), ("m", True), ("5", False), ("az", False)]),
        ("[a-zA-Z]*", [("", True), ("abc", True), ("ABC", True), ("aBcZ", True), ("abc9", False)]),
        ("[a-zA-Z][a-zA-Z0-9]*", [("a", True), ("A1", True), ("var123", True), ("1var", False), ("var_1", False)]),
        ("[0-9][0-9]*", [("0", True), ("42", True), ("2026", True), ("", False), ("12a", False)]),
        ("[1-9][0-9]*", [("1", True), ("9", True), ("42", True), ("0", False), ("01", False)]),
        ("[a-f][0-9a-f]*", [("a", True), ("f", True), ("a10f", True), ("g", False), ("afz", False)]),
        ("0x[0-9a-fA-F][0-9a-fA-F]*", [("0x0", True), ("0xff", True), ("0xA1", True), ("0x", False), ("ff", False)]),
        (r"\*", [("*", True), ("", False), ("a", False), ("**", False)]),
        (r"\|", [("|", True), ("", False), ("a", False), ("||", False)]),
        (r"\(", [("(", True), (")", False), ("", False), ("((", False)]),
        (r"\)", [(")", True), ("(", False), ("", False), ("))", False)]),
        (r"\[", [("[", True), ("]", False), ("", False), ("[[", False)]),
        (r"\]", [("]", True), ("[", False), ("", False), ("]]", False)]),
        (r"\\", [("\\", True), ("", False), ("\\\\", False), ("/", False)]),
        (r"a\*b", [("a*b", True), ("ab", False), ("aaab", False), ("a**b", False)]),
        (r"a\|b", [("a|b", True), ("a", False), ("b", False), ("ab", False)]),
        (r"\(ab\)", [("(ab)", True), ("ab", False), ("(a)", False), ("(ab", False)]),
        (r"\[a-z\]", [("[a-z]", True), ("a", False), ("z", False), ("[m]", False)]),
        (r"[a-z]\*[0-9]", [("a*0", True), ("z*9", True), ("a0", False), ("a**0", False)]),
        (r"(\*|\+)", [("*", True), ("+", True), ("", False), ("*+", False)]),
        (r"\\[a-z]", [("\\a", True), ("\\z", True), ("a", False), ("\\A", False)]),
        (r"[a-z]\|[0-9]", [("a|0", True), ("z|9", True), ("a", False), ("a|x", False)]),
        ("a", [("", False), ("a", True), ("aa", False), ("b", False)]),
        ("b", [("", False), ("b", True), ("a", False), ("bb", False)]),
        ("ab", [("", False), ("a", False), ("ab", True), ("abc", False), ("b", False)]),
        ("abc", [("abc", True), ("ab", False), ("abcd", False), ("bc", False)]),
        ("a|b", [("a", True), ("b", True), ("", False), ("ab", False), ("c", False)]),
        ("a|bc", [("a", True), ("bc", True), ("b", False), ("abc", False)]),
        ("ab|c", [("ab", True), ("c", True), ("a", False), ("abc", False)]),
        ("a|b|c", [("a", True), ("b", True), ("c", True), ("ab", False), ("", False)]),
        ("a*", [("", True), ("a", True), ("aaaa", True), ("b", False), ("aaab", False)]),
        ("b*", [("", True), ("b", True), ("bbb", True), ("a", False), ("bbba", False)]),
        ("ab*", [("a", True), ("ab", True), ("abbbb", True), ("", False), ("b", False)]),
        ("a*b", [("b", True), ("ab", True), ("aaaab", True), ("a", False), ("ba", False)]),
        ("(ab)*", [("", True), ("ab", True), ("abab", True), ("a", False), ("aba", False)]),
        ("(a|b)*", [("", True), ("a", True), ("b", True), ("abba", True), ("abc", False)]),
        ("(a|b)c", [("ac", True), ("bc", True), ("c", False), ("abc", False), ("a", False)]),
        ("a(b|c)", [("ab", True), ("ac", True), ("a", False), ("abc", False), ("b", False)]),
        ("a(b|c)d", [("abd", True), ("acd", True), ("ad", False), ("abcd", False)]),
        ("(a|b)(c|d)", [("ac", True), ("ad", True), ("bc", True), ("bd", True), ("ab", False)]),
        ("(a|b)*c", [("c", True), ("ac", True), ("bbac", True), ("", False), ("ca", False)]),
        ("a(b|c)*d", [("ad", True), ("abd", True), ("acbcd", True), ("ab", False), ("da", False)]),
        ("((a|b)c)*", [("", True), ("ac", True), ("bc", True), ("acbc", True), ("a", False)]),
        ("a(bc|d)", [("abc", True), ("ad", True), ("ab", False), ("abcd", False)]),
        ("(ab|cd)e", [("abe", True), ("cde", True), ("ab", False), ("cdee", False)]),
        ("a(b|cd)*e", [("ae", True), ("abe", True), ("acdbbe", True), ("acd", False)]),
        ("(a|&)", [("", True), ("a", True), ("aa", False), ("b", False)]),
        ("&", [("", True), ("a", False), ("&", False)]),
        ("a&b", [("ab", True), ("a", False), ("b", False), ("a&b", False)]),
        ("(&|a)b", [("b", True), ("ab", True), ("a", False), ("bb", False)]),
        ("a(&|b)", [("a", True), ("ab", True), ("b", False), ("aa", False)]),
        ("(&|a)*", [("", True), ("a", True), ("aaaa", True), ("b", False)]),
        ("(a|&)*b", [("b", True), ("ab", True), ("aaaab", True), ("a", False)]),
        ("a*", [("", True), ("a", True), ("aaaaaa", True), ("ba", False)]),
        ("(a*)b", [("b", True), ("ab", True), ("aaaaab", True), ("aba", False)]),
        ("a(b*)", [("a", True), ("ab", True), ("abbbbb", True), ("", False), ("ba", False)]),
        ("(a|b*)c", [("ac", True), ("c", True), ("bbc", True), ("bc", True), ("ab", False)]),
        ("(a|b)(a|b)", [("aa", True), ("ab", True), ("ba", True), ("bb", True), ("a", False)]),
        ("(a|b)(a|b)*", [("a", True), ("b", True), ("abba", True), ("", False), ("abc", False)]),
        
        ("(0|1)*", [("", True), ("0", True), ("1", True), ("01011", True), ("2", False)]),
        ("0(0|1)*1", [("01", True), ("001", True), ("0101", True), ("0", False), ("10", False)]),
        ("(01)*", [("", True), ("01", True), ("0101", True), ("0", False), ("011", False)]),
        ("(0|1)(0|1)", [("00", True), ("01", True), ("10", True), ("11", True), ("1", False)]),
        ("1*01*", [("0", True), ("10", True), ("011", True), ("111011", True), ("", False)]),
        ("(a|b|c)*d", [("d", True), ("ad", True), ("abccd", True), ("abc", False), ("de", False)]),
        ("a((b|c)*)d", [("ad", True), ("abd", True), ("accbd", True), ("abcd", True), ("acda", False)]),
        ("((a|b)|(c|d))", [("a", True), ("b", True), ("c", True), ("d", True), ("ab", False)]),
        ("((a|b)*)|(cd)", [("", True), ("abba", True), ("cd", True), ("c", False), ("abcd", False)]),
        ("a(b(c|d))*e", [("ae", True), ("abce", True), ("abcbde", True), ("abde", True), ("abcd", False)]),
        ("((ab)|(a))*", [("", True), ("a", True), ("ab", True), ("aababa", True), ("b", False)]),
        ("(a|b)*abb", [("abb", True), ("aabb", True), ("babb", True), ("ababa", False), ("ab", False)]),
    ]

    for regex, examples in cases:
        print(f"\n== Regex {regex!r} ==")
        runner.regex_case(modules, regex, examples)


def main():
    print("Testador do parse_regex em Automato")
    print(f"Pasta testada: {AUTOMATO_DIR}")

    runner = TestRunner()
    add_automato_to_path()

    modules = load_modules(runner)
    if modules is not None:
        run_regex_tests(runner, modules)

    runner.summary()


if __name__ == "__main__":
    main()
