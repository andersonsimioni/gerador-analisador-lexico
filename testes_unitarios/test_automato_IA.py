from pathlib import Path
import sys
import traceback


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
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

    def case(self, automato, palavra, esperado):
        name = f"{automato.nome}.reconhece({palavra!r}) == {esperado}"
        try:
            obtido = automato.reconhece(palavra)
            self.check(name, obtido == esperado, f"obtido: {obtido!r}")
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


def build_helpers(modules):
    Estado = modules["estado"].Estado
    Transicao = modules["transicao"].Transicao
    Automato = modules["automato"].Automato

    def state(nome, inicial=False, final=False):
        return Estado(nome, inicial, final)

    def link(origem, destino, simbolo):
        origem.add_transicao(Transicao(origem, destino, simbolo))

    def automaton(nome, *estados):
        automato = Automato(nome)
        for estado in estados:
            automato.add_estado(estado)
        return automato

    return state, link, automaton


def test_deterministic_basic(runner, helpers):
    print("\n== AFD basico: aceita a+ ==")
    state, link, automaton = helpers

    q0 = state("q0", inicial=True)
    q1 = state("q1", final=True)

    link(q0, q1, "a")
    link(q1, q1, "a")

    afd = automaton("afd_a_mais", q0, q1)

    runner.case(afd, "aa", True)
    runner.case(afd, "aaaaaa", True)
    runner.case(afd, "", False)
    runner.case(afd, "a", True)
    runner.case(afd, "b", False)
    runner.case(afd, "ab", False)


def test_empty_word(runner, helpers):
    print("\n== Palavra vazia ==")
    state, link, automaton = helpers

    initial_final = state("q0", inicial=True, final=True)
    other = state("q1")
    link(initial_final, other, "a")

    accepts_empty = automaton("aceita_vazia", initial_final, other)

    runner.case(accepts_empty, "", True)
    runner.case(accepts_empty, "a", False)


def test_do_not_accept_before_word_ends(runner, helpers):
    print("\n== Nao aceitar antes de consumir toda a palavra ==")
    state, link, automaton = helpers

    q0 = state("q0", inicial=True)
    q1 = state("q1", final=True)
    dead = state("dead")

    link(q0, q1, "a")
    link(q1, dead, "b")
    link(dead, dead, "a")
    link(dead, dead, "b")

    afd = automaton("nao_aceita_prefixo", q0, q1, dead)

    runner.case(afd, "a", True)
    runner.case(afd, "ab", False)
    runner.case(afd, "aba", False)


def test_nondeterministic_branch(runner, helpers):
    print("\n== AFND: dois caminhos com o mesmo simbolo ==")
    state, link, automaton = helpers

    q0 = state("q0", inicial=True)
    wrong = state("wrong")
    mid = state("mid")
    final = state("final", final=True)

    link(q0, wrong, "a")
    link(q0, mid, "a")
    link(wrong, wrong, "b")
    link(mid, final, "b")

    afnd = automaton("afnd_branch_ab", q0, wrong, mid, final)

    runner.case(afnd, "", False)
    runner.case(afnd, "a", False)
    runner.case(afnd, "ab", True)
    runner.case(afnd, "abb", False)


def test_nondeterministic_cycle(runner, helpers):
    print("\n== AFND: ciclo e caminho alternativo ==")
    state, link, automaton = helpers

    q0 = state("q0", inicial=True)
    loop = state("loop")
    final = state("final", final=True)

    link(q0, q0, "a")
    link(q0, loop, "a")
    link(loop, loop, "a")
    link(loop, final, "b")

    afnd = automaton("afnd_varios_a_depois_b", q0, loop, final)

    runner.case(afnd, "b", False)
    runner.case(afnd, "ab", True)
    runner.case(afnd, "aab", True)
    runner.case(afnd, "aaaaab", True)
    runner.case(afnd, "aaaaa", False)
    runner.case(afnd, "aaaaaba", False)


def test_missing_transitions(runner, helpers):
    print("\n== Simbolos sem transicao ==")
    state, link, automaton = helpers

    q0 = state("q0", inicial=True)
    q1 = state("q1", final=True)
    link(q0, q1, "x")

    afd = automaton("transicao_ausente", q0, q1)

    runner.case(afd, "y", False)
    runner.case(afd, "xy", False)
    runner.case(afd, "xx", False)


def test_dead_branch_does_not_kill_good_branch(runner, helpers):
    print("\n== AFND: caminho morto nao mata caminho bom ==")
    state, link, automaton = helpers

    q0 = state("q0", inicial=True)
    dies = state("dies")
    keeps = state("keeps")
    final = state("final", final=True)

    link(q0, dies, "a")
    link(q0, keeps, "a")
    link(dies, dies, "x")
    link(keeps, keeps, "b")
    link(keeps, final, "c")

    afnd = automaton("afnd_um_caminho_morre", q0, dies, keeps, final)

    runner.case(afnd, "ac", True)
    runner.case(afnd, "abc", True)
    runner.case(afnd, "abbbc", True)
    runner.case(afnd, "ax", False)
    runner.case(afnd, "abbbx", False)


def test_multiple_final_states(runner, helpers):
    print("\n== Multiplos estados finais ==")
    state, link, automaton = helpers

    q0 = state("q0", inicial=True)
    ends_a = state("ends_a", final=True)
    ends_b = state("ends_b", final=True)
    dead = state("dead")

    link(q0, ends_a, "a")
    link(q0, ends_b, "b")
    link(ends_a, dead, "a")
    link(ends_a, dead, "b")
    link(ends_b, dead, "a")
    link(ends_b, dead, "b")
    link(dead, dead, "a")
    link(dead, dead, "b")

    afd = automaton("multiplos_finais_so_um_simbolo", q0, ends_a, ends_b, dead)

    runner.case(afd, "", False)
    runner.case(afd, "a", True)
    runner.case(afd, "b", True)
    runner.case(afd, "aa", False)
    runner.case(afd, "ba", False)


def test_unreachable_final_state(runner, helpers):
    print("\n== Estado final inalcançavel nao deve aceitar ==")
    state, link, automaton = helpers

    q0 = state("q0", inicial=True)
    reachable = state("reachable")
    unreachable_final = state("unreachable_final", final=True)

    link(q0, reachable, "a")
    link(reachable, reachable, "a")

    afd = automaton("final_inalcancavel", q0, reachable, unreachable_final)

    runner.case(afd, "", False)
    runner.case(afd, "a", False)
    runner.case(afd, "aaaa", False)


def test_exact_suffix_with_noise(runner, helpers):
    print("\n== AFND: aceitar se termina com ab ==")
    state, link, automaton = helpers

    q0 = state("q0", inicial=True)
    saw_a = state("saw_a")
    final = state("final", final=True)

    link(q0, q0, "a")
    link(q0, q0, "b")
    link(q0, saw_a, "a")
    link(saw_a, final, "b")

    afnd = automaton("termina_com_ab", q0, saw_a, final)

    runner.case(afnd, "", False)
    runner.case(afnd, "ab", True)
    runner.case(afnd, "aab", True)
    runner.case(afnd, "bbab", True)
    runner.case(afnd, "aba", False)
    runner.case(afnd, "abba", False)


def test_long_nondeterministic_word(runner, helpers):
    print("\n== AFND: palavra longa com muitos ramos ==")
    state, link, automaton = helpers

    q0 = state("q0", inicial=True)
    even = state("even", final=True)
    odd = state("odd")
    trap = state("trap")

    link(q0, even, "0")
    link(q0, trap, "0")
    link(even, odd, "1")
    link(odd, even, "1")
    link(trap, trap, "0")
    link(trap, trap, "1")

    afnd = automaton("zeros_e_quantidade_par_de_uns", q0, even, odd, trap)

    runner.case(afnd, "0", True)
    runner.case(afnd, "01", False)
    runner.case(afnd, "011", True)
    runner.case(afnd, "01111111111", True)
    runner.case(afnd, "011111111111", False)
    runner.case(afnd, "0011", False)


def test_epsilon_transitions(runner, helpers, modules):
    print("\n== Epsilon (&): transicoes sem consumir simbolo ==")
    state, link, automaton = helpers
    epsilon = getattr(modules["definicoes"], "EPSILON", getattr(modules["definicoes"], "EPISLON", "&"))

    q0 = state("q0", inicial=True)
    after_epsilon = state("after_epsilon")
    final = state("final", final=True)

    link(q0, after_epsilon, epsilon)
    link(after_epsilon, final, "a")

    afnd = automaton("epsilon_antes_de_a", q0, after_epsilon, final)

    runner.case(afnd, "", False)
    runner.case(afnd, "a", True)
    runner.case(afnd, "aa", False)


def test_epsilon_accepts_empty(runner, helpers, modules):
    print("\n== Epsilon (&): aceitar palavra vazia via salto ==")
    state, link, automaton = helpers
    epsilon = getattr(modules["definicoes"], "EPSILON", getattr(modules["definicoes"], "EPISLON", "&"))

    q0 = state("q0", inicial=True)
    final = state("final", final=True)
    after_a = state("after_a")

    link(q0, final, epsilon)
    link(q0, after_a, "a")

    afnd = automaton("epsilon_aceita_vazia", q0, final, after_a)

    runner.case(afnd, "", True)
    runner.case(afnd, "a", False)


def test_direct_state_methods(runner, helpers):
    print("\n== Metodos diretos de Estado ==")
    state, link, _ = helpers

    q0 = state("q0", inicial=True)
    q1 = state("q1")
    q2 = state("q2")

    try:
        link(q0, q1, "a")
        link(q0, q2, "a")
        proximos = q0.get_proximos_estados("a")
        nomes = sorted(estado.nome for estado in proximos)
        runner.check("Estado guarda duas transicoes para o mesmo simbolo", nomes == ["q1", "q2"], f"obtido: {nomes!r}")
    except Exception:
        runner.check("Estado guarda duas transicoes para o mesmo simbolo", False, traceback.format_exc())

    try:
        proximos = q0.get_proximos_estados("z")
        runner.check("Estado retorna lista vazia quando nao ha transicao", proximos == [], f"obtido: {proximos!r}")
    except Exception:
        runner.check("Estado retorna lista vazia quando nao ha transicao", False, traceback.format_exc())


def run_functional_tests(runner, modules):
    helpers = build_helpers(modules)

    test_direct_state_methods(runner, helpers)
    test_deterministic_basic(runner, helpers)
    test_empty_word(runner, helpers)
    test_do_not_accept_before_word_ends(runner, helpers)
    test_nondeterministic_branch(runner, helpers)
    test_nondeterministic_cycle(runner, helpers)
    test_missing_transitions(runner, helpers)
    test_dead_branch_does_not_kill_good_branch(runner, helpers)
    test_multiple_final_states(runner, helpers)
    test_unreachable_final_state(runner, helpers)
    test_exact_suffix_with_noise(runner, helpers)
    test_long_nondeterministic_word(runner, helpers)
    test_epsilon_transitions(runner, helpers, modules)
    test_epsilon_accepts_empty(runner, helpers, modules)


def main():
    print("Testador do codigo em automato/")
    print(f"Pasta testada: {AUTOMATO_DIR}")

    runner = TestRunner()
    add_automato_to_path()

    modules = load_modules(runner)
    if modules is not None:
        run_functional_tests(runner, modules)

    runner.summary()


if __name__ == "__main__":
    main()
