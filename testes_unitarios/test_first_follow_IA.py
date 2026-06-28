from pathlib import Path
import sys
import traceback


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
SINTATICO_DIR = BASE_DIR / "analisador_sintatico"
EPSILON = "&"
FIM = "$"
TIMEOUT_SEGUNDOS = 2


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


def normalizar_conjuntos(valor):
    if valor is None:
        return None

    if isinstance(valor, tuple) and len(valor) == 2:
        valor = valor[0]

    return {k: set(v) for k, v in valor.items()}


def executar_gramatica(texto):
    try:
        gramatica_livre = __import__("gramatica_livre")
        glc = gramatica_livre.GramaticaLivreDeContexto(texto)

        firsts = getattr(glc, "firsts", None)
        follows = getattr(glc, "follows", None)

        if follows is None and isinstance(firsts, tuple) and len(firsts) == 2:
            firsts, follows = firsts

        return {
            "ok": True,
            "firsts": normalizar_conjuntos(firsts),
            "follows": normalizar_conjuntos(follows),
        }
    except Exception:
        return {
            "ok": False,
            "erro": traceback.format_exc(),
        }


def check_first_follow(runner, nome, texto, firsts_esperados, follows_esperados):
    resultado = executar_gramatica(texto)

    if resultado.get("timeout"):
        runner.check(f"{nome}: nao travar", False, f"estourou timeout de {TIMEOUT_SEGUNDOS}s")
        return

    if not resultado.get("ok"):
        runner.check(f"{nome}: executar", False, resultado.get("erro", "erro desconhecido"))
        return

    firsts = resultado["firsts"]
    follows = resultado["follows"]

    runner.check(
        f"{nome}: firsts existem",
        firsts is not None,
        "glc.firsts nao existe ou calcular_first_follow nao retornou firsts"
    )
    if firsts is not None:
        runner.check(
            f"{nome}: FIRST",
            firsts == firsts_esperados,
            f"esperado: {firsts_esperados!r}\nobtido:   {firsts!r}"
        )

    runner.check(
        f"{nome}: follows existem",
        follows is not None,
        "glc.follows nao existe ou calcular_first_follow nao retornou follows"
    )
    if follows is not None:
        runner.check(
            f"{nome}: FOLLOW",
            follows == follows_esperados,
            f"esperado: {follows_esperados!r}\nobtido:   {follows!r}"
        )


def run_first_follow_tests(runner):
    print("\n== FIRST/FOLLOW debug imediato ==")

    check_first_follow(
        runner,
        "debug 00 - GLC dificil com nullable em cadeia",
        "\n".join([
            "S ::= A B C d",
            "S ::= E f",
            "A ::= a A",
            "A ::= &",
            "B ::= b B",
            "B ::= C D",
            "B ::= &",
            "C ::= c C",
            "C ::= &",
            "D ::= d D",
            "D ::= &",
            "E ::= A e",
            "E ::= g",
        ]),
        {
            "S": {"a", "b", "c", "d", "e", "g"},
            "A": {"a", EPSILON},
            "B": {"b", "c", "d", EPSILON},
            "C": {"c", EPSILON},
            "D": {"d", EPSILON},
            "E": {"a", "e", "g"},
        },
        {
            "S": {FIM},
            "A": {"b", "c", "d", "e"},
            "B": {"c", "d"},
            "C": {"c", "d"},
            "D": {"c", "d"},
            "E": {"f"},
        }
    )

    check_first_follow(
        runner,
        "debug 01 - terminal antes de terminal nao vira FOLLOW",
        "\n".join([
            "S ::= id = E",
            "E ::= id",
        ]),
        {
            "S": {"id"},
            "E": {"id"},
        },
        {
            "S": {FIM},
            "E": {FIM},
        }
    )

    check_first_follow(
        runner,
        "debug 02 - terminal simples nao pode virar chave de FOLLOW",
        "\n".join([
            "S ::= a",
        ]),
        {
            "S": {"a"},
        },
        {
            "S": {FIM},
        }
    )

    check_first_follow(
        runner,
        "debug 03 - alvo do FOLLOW precisa ser nao terminal",
        "\n".join([
            "S ::= A b",
            "A ::= a",
        ]),
        {
            "S": {"a"},
            "A": {"a"},
        },
        {
            "S": {FIM},
            "A": {"b"},
        }
    )

    check_first_follow(
        runner,
        "debug 04 - epsilon nao pode virar chave de FOLLOW",
        "\n".join([
            "S ::= A B",
            "A ::= &",
            "B ::= &",
        ]),
        {
            "S": {EPSILON},
            "A": {EPSILON},
            "B": {EPSILON},
        },
        {
            "S": {FIM},
            "A": {FIM},
            "B": {FIM},
        }
    )

    check_first_follow(
        runner,
        "debug 05 - terminal depois de nullable entra no anterior",
        "\n".join([
            "S ::= A B c",
            "A ::= a",
            "B ::= b",
            "B ::= &",
        ]),
        {
            "S": {"a"},
            "A": {"a"},
            "B": {"b", EPSILON},
        },
        {
            "S": {FIM},
            "A": {"b", "c"},
            "B": {"c"},
        }
    )

    check_first_follow(
        runner,
        "debug 06 - precisa olhar sufixo inteiro",
        "\n".join([
            "S ::= A B C d",
            "A ::= a",
            "B ::= b",
            "B ::= &",
            "C ::= c",
            "C ::= &",
        ]),
        {
            "S": {"a"},
            "A": {"a"},
            "B": {"b", EPSILON},
            "C": {"c", EPSILON},
        },
        {
            "S": {FIM},
            "A": {"b", "c", "d"},
            "B": {"c", "d"},
            "C": {"d"},
        }
    )

    print("\n== FIRST/FOLLOW basicos ==")

    check_first_follow(
        runner,
        "terminal simples",
        "\n".join([
            "S ::= a",
        ]),
        {
            "S": {"a"},
        },
        {
            "S": {FIM},
        }
    )

    check_first_follow(
        runner,
        "cadeia simples",
        "\n".join([
            "S ::= A b",
            "A ::= a",
        ]),
        {
            "S": {"a"},
            "A": {"a"},
        },
        {
            "S": {FIM},
            "A": {"b"},
        }
    )

    check_first_follow(
        runner,
        "epsilon no primeiro simbolo",
        "\n".join([
            "S ::= A b",
            "A ::= a",
            "A ::= &",
        ]),
        {
            "S": {"a", "b"},
            "A": {"a", EPSILON},
        },
        {
            "S": {FIM},
            "A": {"b"},
        }
    )

    check_first_follow(
        runner,
        "todos anulaveis",
        "\n".join([
            "S ::= A B",
            "A ::= &",
            "B ::= &",
        ]),
        {
            "S": {EPSILON},
            "A": {EPSILON},
            "B": {EPSILON},
        },
        {
            "S": {FIM},
            "A": {FIM},
            "B": {FIM},
        }
    )

    check_first_follow(
        runner,
        "follow herda da cabeca",
        "\n".join([
            "S ::= A",
            "A ::= a",
        ]),
        {
            "S": {"a"},
            "A": {"a"},
        },
        {
            "S": {FIM},
            "A": {FIM},
        }
    )

    print("\n== FIRST/FOLLOW expressoes ==")

    check_first_follow(
        runner,
        "expressao classica",
        "\n".join([
            "E ::= T X",
            "X ::= + T X",
            "X ::= &",
            "T ::= F Y",
            "Y ::= * F Y",
            "Y ::= &",
            "F ::= ( E )",
            "F ::= id",
        ]),
        {
            "E": {"(", "id"},
            "X": {"+", EPSILON},
            "T": {"(", "id"},
            "Y": {"*", EPSILON},
            "F": {"(", "id"},
        },
        {
            "E": {")", FIM},
            "X": {")", FIM},
            "T": {"+", ")", FIM},
            "Y": {"+", ")", FIM},
            "F": {"*", "+", ")", FIM},
        }
    )

    check_first_follow(
        runner,
        "recursao esquerda",
        "\n".join([
            "E ::= E + T",
            "E ::= T",
            "T ::= T * F",
            "T ::= F",
            "F ::= ( E )",
            "F ::= id",
        ]),
        {
            "E": {"(", "id"},
            "T": {"(", "id"},
            "F": {"(", "id"},
        },
        {
            "E": {"+", ")", FIM},
            "T": {"*", "+", ")", FIM},
            "F": {"*", "+", ")", FIM},
        }
    )

    print("\n== FIRST/FOLLOW chatos ==")

    check_first_follow(
        runner,
        "cadeia com varios epsilons antes de terminal",
        "\n".join([
            "S ::= A B C d",
            "A ::= a",
            "A ::= &",
            "B ::= b",
            "B ::= &",
            "C ::= c",
            "C ::= &",
        ]),
        {
            "S": {"a", "b", "c", "d"},
            "A": {"a", EPSILON},
            "B": {"b", EPSILON},
            "C": {"c", EPSILON},
        },
        {
            "S": {FIM},
            "A": {"b", "c", "d"},
            "B": {"c", "d"},
            "C": {"d"},
        }
    )

    check_first_follow(
        runner,
        "cadeia toda nullable",
        "\n".join([
            "S ::= A B C",
            "A ::= a",
            "A ::= &",
            "B ::= b",
            "B ::= &",
            "C ::= c",
            "C ::= &",
        ]),
        {
            "S": {"a", "b", "c", EPSILON},
            "A": {"a", EPSILON},
            "B": {"b", EPSILON},
            "C": {"c", EPSILON},
        },
        {
            "S": {FIM},
            "A": {"b", "c", FIM},
            "B": {"c", FIM},
            "C": {FIM},
        }
    )

    check_first_follow(
        runner,
        "if else",
        "\n".join([
            "S ::= if E then S Else",
            "S ::= id = E",
            "Else ::= else S",
            "Else ::= &",
            "E ::= id",
            "E ::= num",
        ]),
        {
            "S": {"if", "id"},
            "Else": {"else", EPSILON},
            "E": {"id", "num"},
        },
        {
            "S": {"else", FIM},
            "Else": {"else", FIM},
            "E": {"then", "else", FIM},
        }
    )

    check_first_follow(
        runner,
        "lista separada por virgula",
        "\n".join([
            "Lista ::= Item Resto",
            "Resto ::= virgula Item Resto",
            "Resto ::= &",
            "Item ::= id",
            "Item ::= num",
        ]),
        {
            "Lista": {"id", "num"},
            "Resto": {"virgula", EPSILON},
            "Item": {"id", "num"},
        },
        {
            "Lista": {FIM},
            "Resto": {FIM},
            "Item": {"virgula", FIM},
        }
    )


def run_generated_stress_tests(runner):
    print("\n== FIRST/FOLLOW stress gerado ==")

    for i in range(100):
        S = f"S{i}"
        A = f"A{i}"
        B = f"B{i}"
        C = f"C{i}"
        t1 = f"a{i}"
        t2 = f"b{i}"
        t3 = f"c{i}"
        fim = f"fim{i}"

        texto = "\n".join([
            f"{S} ::= {A} {B} {C} {fim}",
            f"{A} ::= {t1}",
            f"{A} ::= &",
            f"{B} ::= {t2}",
            f"{B} ::= &",
            f"{C} ::= {t3}",
        ])

        check_first_follow(
            runner,
            f"stress {i + 1:03}",
            texto,
            {
                S: {t1, t2, t3},
                A: {t1, EPSILON},
                B: {t2, EPSILON},
                C: {t3},
            },
            {
                S: {FIM},
                A: {t2, t3},
                B: {t3},
                C: {fim},
            }
        )


def main():
    print("Testador de FIRST/FOLLOW da GramaticaLivreDeContexto")
    print(f"Pasta testada: {SINTATICO_DIR}")
    runner = TestRunner()

    sys.path.insert(0, str(SINTATICO_DIR))
    sys.path.insert(0, str(BASE_DIR))

    run_first_follow_tests(runner)
    run_generated_stress_tests(runner)

    runner.summary()


if __name__ == "__main__":
    main()
