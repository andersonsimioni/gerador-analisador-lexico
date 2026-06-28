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


def normalizar_item_str(item):
    texto = str(item)
    texto = texto.replace(chr(194) + chr(183), ".")
    texto = texto.replace(chr(183), ".")
    return texto


def executar_closure(texto):
    try:
        sys.path.insert(0, str(SINTATICO_DIR))
        gramatica_livre = __import__("gramatica_livre")
        prod_item_LR0 = __import__("prod_item_LR0")

        glc = gramatica_livre.GramaticaLivreDeContexto(texto, True)
        prod_inicial = [p for p in glc.producoes if p.cabeca == glc.cabeca_inicial][0]
        item_inicial = prod_item_LR0.ProdItemLR0(prod_inicial, 0)
        closure = glc.calcula_closure([item_inicial])

        return {
            "ok": True,
            "itens": [normalizar_item_str(x) for x in closure],
            "itens_set": {normalizar_item_str(x) for x in closure},
        }
    except Exception:
        return {
            "ok": False,
            "erro": traceback.format_exc(),
        }


def check_closure(runner, nome, texto, esperados):
    resultado = executar_closure(texto)

    if not resultado.get("ok"):
        runner.check(f"{nome}: executar", False, resultado.get("erro", "erro desconhecido"))
        return

    obtidos = resultado["itens_set"]
    esperados = set(esperados)

    runner.check(
        f"{nome}: closure",
        obtidos == esperados,
        "esperado:\n"
        + "\n".join(sorted(esperados))
        + "\n\nobtido:\n"
        + "\n".join(resultado["itens"])
    )


def run_closure_tests(runner):
    print("\n== CLOSURE LR0 debug imediato ==")

    check_closure(
        runner,
        "debug 01 - terminal nao expande",
        "\n".join([
            "S ::= a A",
            "A ::= b",
        ]),
        [
            "S' ::= .S",
            "S ::= .a A",
        ],
    )

    check_closure(
        runner,
        "debug 02 - cadeia de nao terminais",
        "\n".join([
            "S ::= A",
            "A ::= B",
            "A ::= a",
            "B ::= b",
        ]),
        [
            "S' ::= .S",
            "S ::= .A",
            "A ::= .B",
            "A ::= .a",
            "B ::= .b",
        ],
    )

    check_closure(
        runner,
        "debug 03 - multiplas producoes da mesma cabeca",
        "\n".join([
            "S ::= A",
            "A ::= a",
            "A ::= b",
            "A ::= c",
        ]),
        [
            "S' ::= .S",
            "S ::= .A",
            "A ::= .a",
            "A ::= .b",
            "A ::= .c",
        ],
    )

    check_closure(
        runner,
        "debug 04 - recursao mutua nao pode loopar",
        "\n".join([
            "S ::= A",
            "A ::= S",
            "A ::= a",
        ]),
        [
            "S' ::= .S",
            "S ::= .A",
            "A ::= .S",
            "A ::= .a",
        ],
    )

    print("\n== CLOSURE LR0 expressoes ==")

    check_closure(
        runner,
        "expressao classica no estado inicial",
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
        [
            "E' ::= .E",
            "E ::= .T X",
            "T ::= .F Y",
            "F ::= .( E )",
            "F ::= .id",
        ],
    )

    check_closure(
        runner,
        "nao terminal depois do ponto com epsilon",
        "\n".join([
            "S ::= A fim",
            "A ::= &",
            "A ::= a",
        ]),
        [
            "S' ::= .S",
            "S ::= .A fim",
            "A ::= .&",
            "A ::= .a",
        ],
    )

    print("\n== CLOSURE LR0 stress gerado ==")

    for i in range(1, 31):
        check_closure(
            runner,
            f"stress cadeia longa {i:03d}",
            "\n".join([
                "S ::= A1",
                "A1 ::= A2",
                "A1 ::= a1",
                "A2 ::= A3",
                "A2 ::= a2",
                "A3 ::= A4",
                "A3 ::= a3",
                "A4 ::= fim",
            ]),
            [
                "S' ::= .S",
                "S ::= .A1",
                "A1 ::= .A2",
                "A1 ::= .a1",
                "A2 ::= .A3",
                "A2 ::= .a2",
                "A3 ::= .A4",
                "A3 ::= .a3",
                "A4 ::= .fim",
            ],
        )

    for i in range(1, 31):
        check_closure(
            runner,
            f"stress muitas alternativas {i:03d}",
            "\n".join([
                "S ::= A",
                f"A ::= a{i}",
                f"A ::= b{i}",
                f"A ::= c{i}",
                f"A ::= d{i}",
                f"A ::= e{i}",
                f"A ::= f{i}",
            ]),
            [
                "S' ::= .S",
                "S ::= .A",
                f"A ::= .a{i}",
                f"A ::= .b{i}",
                f"A ::= .c{i}",
                f"A ::= .d{i}",
                f"A ::= .e{i}",
                f"A ::= .f{i}",
            ],
        )

    for i in range(1, 21):
        check_closure(
            runner,
            f"stress epsilon e ramificacao {i:03d}",
            "\n".join([
                "S ::= A",
                "A ::= B",
                "A ::= C",
                "A ::= &",
                f"B ::= b{i}",
                f"C ::= c{i}",
                "C ::= D",
                f"D ::= d{i}",
            ]),
            [
                "S' ::= .S",
                "S ::= .A",
                "A ::= .B",
                "A ::= .C",
                "A ::= .&",
                f"B ::= .b{i}",
                f"C ::= .c{i}",
                "C ::= .D",
                f"D ::= .d{i}",
            ],
        )

    for i in range(1, 21):
        check_closure(
            runner,
            f"stress recursao circular {i:03d}",
            "\n".join([
                "S ::= A",
                "A ::= B",
                f"A ::= a{i}",
                "B ::= C",
                f"B ::= b{i}",
                "C ::= A",
                f"C ::= c{i}",
            ]),
            [
                "S' ::= .S",
                "S ::= .A",
                "A ::= .B",
                f"A ::= .a{i}",
                "B ::= .C",
                f"B ::= .b{i}",
                "C ::= .A",
                f"C ::= .c{i}",
            ],
        )

    for i in range(1, 21):
        check_closure(
            runner,
            f"stress terminal no inicio nao expande {i:03d}",
            "\n".join([
                f"S ::= inicio{i} A",
                "A ::= B",
                f"B ::= b{i}",
            ]),
            [
                "S' ::= .S",
                f"S ::= .inicio{i} A",
            ],
        )


def main():
    print("Testador de CLOSURE LR0 da GramaticaLivreDeContexto")
    print(f"Pasta testada: {SINTATICO_DIR}")

    if str(SINTATICO_DIR) not in sys.path:
        sys.path.insert(0, str(SINTATICO_DIR))

    runner = TestRunner()
    run_closure_tests(runner)
    runner.summary()


if __name__ == "__main__":
    main()
