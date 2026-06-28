from pathlib import Path
import sys
import traceback


BASE_DIR = Path(__file__).resolve().parent
SINTATICO_DIR = BASE_DIR / "analisador_sintatico"


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

    def summary(self):
        failed = self.total - self.passed
        print("\n== Resumo ==")
        print(f"Passou: {self.passed}/{self.total}")
        print(f"Falhou: {failed}/{self.total}")


def add_paths():
    sys.path.insert(0, str(SINTATICO_DIR))
    sys.path.insert(0, str(BASE_DIR))


def load_modules(runner):
    print("\n== Imports ==")
    modules = {}

    for module_name in ["simbolo_producao", "producao", "gramatica_livre"]:
        try:
            modules[module_name] = __import__(module_name)
            runner.check(f"import {module_name}", True)
        except Exception:
            runner.check(f"import {module_name}", False, traceback.format_exc())
            return None

    return modules


def simbolos_to_tuples(producao):
    return [(x.simbolo, x.is_terminal) for x in producao.corpo]


def check_producao(runner, Producao, texto, cabecas, cabeca_esperada, corpo_esperado, str_esperado):
    try:
        p = Producao(texto, cabecas)
        runner.check(f"Producao({texto!r}).cabeca", p.cabeca == cabeca_esperada, f"obtido: {p.cabeca!r}")
        runner.check(f"Producao({texto!r}).corpo", simbolos_to_tuples(p) == corpo_esperado, f"obtido: {simbolos_to_tuples(p)!r}")
        runner.check(f"str(Producao({texto!r}))", str(p) == str_esperado, f"obtido: {str(p)!r}")
    except Exception:
        runner.check(f"Producao({texto!r})", False, traceback.format_exc())


def check_gramatica(runner, GramaticaLivreDeContexto, nome, texto, cabecas_esperadas, producoes_esperadas, str_esperado):
    try:
        glc = GramaticaLivreDeContexto(texto)
        runner.check(f"{nome}: quantidade de producoes", len(glc.producoes) == len(producoes_esperadas), f"obtido: {len(glc.producoes)!r}")
        runner.check(f"{nome}: get_cabecas", glc.get_cabecas() == cabecas_esperadas, f"obtido: {glc.get_cabecas()!r}")

        obtidas = [
            (p.cabeca, simbolos_to_tuples(p), str(p))
            for p in glc.producoes
        ]
        runner.check(f"{nome}: producoes parseadas", obtidas == producoes_esperadas, f"obtido: {obtidas!r}")

        try:
            obtido_str = str(glc)
            runner.check(f"{nome}: str(glc)", obtido_str == str_esperado, f"obtido: {obtido_str!r}")
        except Exception:
            runner.check(f"{nome}: str(glc)", False, traceback.format_exc())
    except Exception:
        runner.check(f"{nome}: GramaticaLivreDeContexto(...)", False, traceback.format_exc())


def montar_producao(cabeca, corpo):
    texto = f"{cabeca} ::= {' '.join(corpo)}"
    return texto, (cabeca, corpo)


def esperado_de_gramatica(producoes):
    cabecas = [cabeca for _, (cabeca, _) in producoes]
    cabecas_set = set(cabecas)
    producoes_esperadas = []

    for texto, (cabeca, corpo) in producoes:
        corpo_esperado = [(simbolo, simbolo not in cabecas_set) for simbolo in corpo]
        producoes_esperadas.append((cabeca, corpo_esperado, texto))

    return cabecas, producoes_esperadas, "\n".join([texto for texto, _ in producoes])


def run_simbolo_tests(runner, modules):
    print("\n== SimboloProducao ==")
    SimboloProducao = modules["simbolo_producao"].SimboloProducao

    cases = [
        ("E", False, "E"),
        ("T", False, "T"),
        ("id", True, "id"),
        ("ID", True, "ID"),
        ("+", True, "+"),
        ("&", True, "&"),
    ]

    for simbolo, terminal, esperado in cases:
        try:
            s = SimboloProducao(simbolo, terminal)
            runner.check(f"str(SimboloProducao({simbolo!r}, {terminal!r}))", str(s) == esperado, f"obtido: {str(s)!r}")
        except Exception:
            runner.check(f"SimboloProducao({simbolo!r}, {terminal!r})", False, traceback.format_exc())


def run_producao_tests(runner, modules):
    print("\n== Producao ==")
    Producao = modules["producao"].Producao

    cabecas_expr = {"E", "T", "F"}
    check_producao(
        runner, Producao,
        "E ::= E + T",
        cabecas_expr,
        "E",
        [("E", False), ("+", True), ("T", False)],
        "E ::= E + T"
    )
    check_producao(
        runner, Producao,
        "T ::= T * F",
        cabecas_expr,
        "T",
        [("T", False), ("*", True), ("F", False)],
        "T ::= T * F"
    )
    check_producao(
        runner, Producao,
        "F ::= ( E )",
        cabecas_expr,
        "F",
        [("(", True), ("E", False), (")", True)],
        "F ::= ( E )"
    )
    check_producao(
        runner, Producao,
        "F ::= id",
        cabecas_expr,
        "F",
        [("id", True)],
        "F ::= id"
    )

    cabecas_stmt = {"S", "A", "B"}
    check_producao(
        runner, Producao,
        "S ::= A B",
        cabecas_stmt,
        "S",
        [("A", False), ("B", False)],
        "S ::= A B"
    )
    check_producao(
        runner, Producao,
        "A ::= &",
        cabecas_stmt,
        "A",
        [("&", True)],
        "A ::= &"
    )
    check_producao(
        runner, Producao,
        "B ::= b",
        cabecas_stmt,
        "B",
        [("b", True)],
        "B ::= b"
    )


def run_gramatica_tests(runner, modules):
    print("\n== GramaticaLivreDeContexto ==")
    GramaticaLivreDeContexto = modules["gramatica_livre"].GramaticaLivreDeContexto

    chato_1 = "\n".join([
        "S ::= Bloco EOF",
        "Bloco ::= abre Lista fecha",
        "Lista ::= Item sep Lista",
        "Lista ::= Item",
        "Item ::= id",
        "Item ::= num",
        "Item ::= abre Lista fecha",
        "EOF ::= &",
    ])
    check_gramatica(
        runner,
        GramaticaLivreDeContexto,
        "chato inicial: lista aninhada com eof epsilon",
        chato_1,
        ["S", "Bloco", "Lista", "Lista", "Item", "Item", "Item", "EOF"],
        [
            ("S", [("Bloco", False), ("EOF", False)], "S ::= Bloco EOF"),
            ("Bloco", [("abre", True), ("Lista", False), ("fecha", True)], "Bloco ::= abre Lista fecha"),
            ("Lista", [("Item", False), ("sep", True), ("Lista", False)], "Lista ::= Item sep Lista"),
            ("Lista", [("Item", False)], "Lista ::= Item"),
            ("Item", [("id", True)], "Item ::= id"),
            ("Item", [("num", True)], "Item ::= num"),
            ("Item", [("abre", True), ("Lista", False), ("fecha", True)], "Item ::= abre Lista fecha"),
            ("EOF", [("&", True)], "EOF ::= &"),
        ],
        chato_1
    )

    chato_2 = "\n".join([
        "Expr ::= Expr op Term",
        "Expr ::= Term",
        "Term ::= Term mul Unary",
        "Term ::= Unary",
        "Unary ::= not Unary",
        "Unary ::= sinal Unary",
        "Unary ::= Prim",
        "Prim ::= id",
        "Prim ::= num",
        "Prim ::= abre Expr fecha",
    ])
    check_gramatica(
        runner,
        GramaticaLivreDeContexto,
        "chato inicial: precedencia com unario",
        chato_2,
        ["Expr", "Expr", "Term", "Term", "Unary", "Unary", "Unary", "Prim", "Prim", "Prim"],
        [
            ("Expr", [("Expr", False), ("op", True), ("Term", False)], "Expr ::= Expr op Term"),
            ("Expr", [("Term", False)], "Expr ::= Term"),
            ("Term", [("Term", False), ("mul", True), ("Unary", False)], "Term ::= Term mul Unary"),
            ("Term", [("Unary", False)], "Term ::= Unary"),
            ("Unary", [("not", True), ("Unary", False)], "Unary ::= not Unary"),
            ("Unary", [("sinal", True), ("Unary", False)], "Unary ::= sinal Unary"),
            ("Unary", [("Prim", False)], "Unary ::= Prim"),
            ("Prim", [("id", True)], "Prim ::= id"),
            ("Prim", [("num", True)], "Prim ::= num"),
            ("Prim", [("abre", True), ("Expr", False), ("fecha", True)], "Prim ::= abre Expr fecha"),
        ],
        chato_2
    )

    chato_3 = "\n".join([
        "A ::= B C D E",
        "B ::= b",
        "C ::= &",
        "D ::= D d",
        "D ::= &",
        "E ::= e E",
        "E ::= f",
    ])
    check_gramatica(
        runner,
        GramaticaLivreDeContexto,
        "chato inicial: muitos anulaveis no meio",
        chato_3,
        ["A", "B", "C", "D", "D", "E", "E"],
        [
            ("A", [("B", False), ("C", False), ("D", False), ("E", False)], "A ::= B C D E"),
            ("B", [("b", True)], "B ::= b"),
            ("C", [("&", True)], "C ::= &"),
            ("D", [("D", False), ("d", True)], "D ::= D d"),
            ("D", [("&", True)], "D ::= &"),
            ("E", [("e", True), ("E", False)], "E ::= e E"),
            ("E", [("f", True)], "E ::= f"),
        ],
        chato_3
    )

    chato_4 = "\n".join([
        "S ::= ID id Id",
        "ID ::= token",
        "Id ::= outro",
        "X ::= ID x Id",
    ])
    check_gramatica(
        runner,
        GramaticaLivreDeContexto,
        "chato inicial: nomes parecidos maiusculo minusculo",
        chato_4,
        ["S", "ID", "Id", "X"],
        [
            ("S", [("ID", False), ("id", True), ("Id", False)], "S ::= ID id Id"),
            ("ID", [("token", True)], "ID ::= token"),
            ("Id", [("outro", True)], "Id ::= outro"),
            ("X", [("ID", False), ("x", True), ("Id", False)], "X ::= ID x Id"),
        ],
        chato_4
    )

    chato_5 = "\n".join([
        "S ::= abre A fecha",
        "A ::= A virgula B",
        "A ::= B",
        "B ::= colchete_abre A colchete_fecha",
        "B ::= chave_abre A chave_fecha",
        "B ::= id",
        "B ::= &",
    ])
    check_gramatica(
        runner,
        GramaticaLivreDeContexto,
        "chato inicial: varios delimitadores nomeados",
        chato_5,
        ["S", "A", "A", "B", "B", "B", "B"],
        [
            ("S", [("abre", True), ("A", False), ("fecha", True)], "S ::= abre A fecha"),
            ("A", [("A", False), ("virgula", True), ("B", False)], "A ::= A virgula B"),
            ("A", [("B", False)], "A ::= B"),
            ("B", [("colchete_abre", True), ("A", False), ("colchete_fecha", True)], "B ::= colchete_abre A colchete_fecha"),
            ("B", [("chave_abre", True), ("A", False), ("chave_fecha", True)], "B ::= chave_abre A chave_fecha"),
            ("B", [("id", True)], "B ::= id"),
            ("B", [("&", True)], "B ::= &"),
        ],
        chato_5
    )

    expr = "\n".join([
        "E ::= E + T",
        "E ::= T",
        "T ::= T * F",
        "T ::= F",
        "F ::= ( E )",
        "F ::= id",
    ])
    check_gramatica(
        runner,
        GramaticaLivreDeContexto,
        "gramatica expressoes",
        expr,
        ["E", "E", "T", "T", "F", "F"],
        [
            ("E", [("E", False), ("+", True), ("T", False)], "E ::= E + T"),
            ("E", [("T", False)], "E ::= T"),
            ("T", [("T", False), ("*", True), ("F", False)], "T ::= T * F"),
            ("T", [("F", False)], "T ::= F"),
            ("F", [("(", True), ("E", False), (")", True)], "F ::= ( E )"),
            ("F", [("id", True)], "F ::= id"),
        ],
        expr
    )

    stmt = "\n".join([
        "S ::= if E then S else S",
        "S ::= if E then S",
        "S ::= id = E",
        "E ::= id",
        "E ::= num",
    ])
    check_gramatica(
        runner,
        GramaticaLivreDeContexto,
        "gramatica comandos",
        stmt,
        ["S", "S", "S", "E", "E"],
        [
            ("S", [("if", True), ("E", False), ("then", True), ("S", False), ("else", True), ("S", False)], "S ::= if E then S else S"),
            ("S", [("if", True), ("E", False), ("then", True), ("S", False)], "S ::= if E then S"),
            ("S", [("id", True), ("=", True), ("E", False)], "S ::= id = E"),
            ("E", [("id", True)], "E ::= id"),
            ("E", [("num", True)], "E ::= num"),
        ],
        stmt
    )

    epsilon = "\n".join([
        "S ::= A B",
        "A ::= a A",
        "A ::= &",
        "B ::= b B",
        "B ::= &",
    ])
    check_gramatica(
        runner,
        GramaticaLivreDeContexto,
        "gramatica epsilon",
        epsilon,
        ["S", "A", "A", "B", "B"],
        [
            ("S", [("A", False), ("B", False)], "S ::= A B"),
            ("A", [("a", True), ("A", False)], "A ::= a A"),
            ("A", [("&", True)], "A ::= &"),
            ("B", [("b", True), ("B", False)], "B ::= b B"),
            ("B", [("&", True)], "B ::= &"),
        ],
        epsilon
    )


def run_stress_tests(runner, modules):
    print("\n== Stress 500 gramaticas ==")
    GramaticaLivreDeContexto = modules["gramatica_livre"].GramaticaLivreDeContexto

    terminais = [
        "id", "num", "str", "if", "else", "while", "return", "mais", "menos",
        "vezes", "divide", "abre", "fecha", "virgula", "ponto_virgula", "op_rel"
    ]

    for i in range(500):
        S = f"S{i}"
        A = f"A{i}"
        B = f"B{i}"
        C = f"C{i}"
        D = f"D{i}"
        E = f"E{i}"
        t1 = terminais[i % len(terminais)]
        t2 = terminais[(i * 3 + 1) % len(terminais)]
        t3 = terminais[(i * 5 + 2) % len(terminais)]
        t4 = terminais[(i * 7 + 3) % len(terminais)]

        producoes = [
            montar_producao(S, [A, B, "fim"]),
            montar_producao(A, [t1, A]),
            montar_producao(A, ["&"]),
            montar_producao(B, [C, D]),
            montar_producao(C, [t2]),
            montar_producao(C, ["abre", S, "fecha"]),
            montar_producao(D, [D, t3]),
            montar_producao(D, [E]),
            montar_producao(E, [t4]),
            montar_producao(E, ["&"]),
        ]

        if i % 2 == 0:
            producoes.append(montar_producao(B, [B, "virgula", C]))
        if i % 3 == 0:
            producoes.append(montar_producao(C, ["not", C]))
        if i % 5 == 0:
            producoes.append(montar_producao(S, ["inicio", S, "fim"]))
        if i % 7 == 0:
            producoes.append(montar_producao(E, ["id", "op_rel", "num"]))

        cabecas, producoes_esperadas, texto = esperado_de_gramatica(producoes)
        check_gramatica(
            runner,
            GramaticaLivreDeContexto,
            f"stress {i + 1:03}",
            texto,
            cabecas,
            producoes_esperadas,
            texto
        )


def main():
    print("Testador do parser da GramaticaLivreDeContexto")
    print(f"Pasta testada: {SINTATICO_DIR}")
    runner = TestRunner()

    add_paths()
    modules = load_modules(runner)
    if modules is not None:
        run_simbolo_tests(runner, modules)
        run_producao_tests(runner, modules)
        run_gramatica_tests(runner, modules)
        run_stress_tests(runner, modules)

    runner.summary()


if __name__ == "__main__":
    main()
