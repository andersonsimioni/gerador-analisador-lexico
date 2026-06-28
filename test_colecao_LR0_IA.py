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


def normalizar_estado(estado):
    return frozenset(normalizar_item_str(item) for item in estado)


def formatar_colecao(colecao):
    linhas = []
    for i, estado in enumerate(colecao):
        linhas.append(f"I{i}:")
        for item in sorted(estado):
            linhas.append(f"  {item}")
    return "\n".join(linhas)


def parse_producoes(texto):
    linhas = [x.strip() for x in texto.splitlines() if x.strip()]
    cabecas = [x.split("::=")[0].strip() for x in linhas]
    cabeca_inicial = cabecas[0]
    nova_cabeca = cabeca_inicial

    while nova_cabeca in cabecas:
        nova_cabeca += "'"

    producoes = [(nova_cabeca, [cabeca_inicial])]
    for linha in linhas:
        cabeca, corpo = linha.split("::=")
        producoes.append((cabeca.strip(), corpo.strip().split()))

    return producoes, nova_cabeca


def item_para_string(producoes, item):
    indice, ponto = item
    cabeca, corpo = producoes[indice]
    aux = list(corpo)

    if ponto >= len(aux):
        return f"{cabeca} ::= {' '.join(aux)}."

    aux[ponto] = f".{aux[ponto]}"
    return f"{cabeca} ::= {' '.join(aux)}"


def closure_referencia(producoes, cabecas, itens):
    closure = set(itens)
    mudou = True

    while mudou:
        mudou = False
        for indice, ponto in list(closure):
            cabeca, corpo = producoes[indice]

            if ponto >= len(corpo):
                continue

            simbolo = corpo[ponto]
            if simbolo not in cabecas:
                continue

            for i, producao in enumerate(producoes):
                if producao[0] != simbolo:
                    continue

                novo = (i, 0)
                if novo not in closure:
                    closure.add(novo)
                    mudou = True

    return frozenset(closure)


def colecao_lr0_referencia(texto):
    producoes, _ = parse_producoes(texto)
    cabecas = {cabeca for cabeca, _ in producoes}
    inicial = closure_referencia(producoes, cabecas, {(0, 0)})
    estados = [inicial]
    vistos = {inicial}
    i = 0

    while i < len(estados):
        estado = estados[i]
        avancos_por_simbolo = {}

        for indice, ponto in estado:
            cabeca, corpo = producoes[indice]
            if ponto >= len(corpo):
                continue

            simbolo = corpo[ponto]
            avancos_por_simbolo.setdefault(simbolo, set()).add((indice, ponto + 1))

        for avancos in avancos_por_simbolo.values():
            novo_estado = closure_referencia(producoes, cabecas, avancos)
            if novo_estado not in vistos:
                vistos.add(novo_estado)
                estados.append(novo_estado)

        i += 1

    return [
        {item_para_string(producoes, item) for item in estado}
        for estado in estados
    ]


def executar_colecao(texto):
    try:
        if str(SINTATICO_DIR) not in sys.path:
            sys.path.insert(0, str(SINTATICO_DIR))

        gramatica_livre = __import__("gramatica_livre")
        glc = gramatica_livre.GramaticaLivreDeContexto(texto)
        colecao = glc.get_itens_LR0()

        estados = [normalizar_estado(estado) for estado in colecao]

        return {
            "ok": True,
            "estados": estados,
            "estados_set": set(estados),
        }
    except Exception:
        return {
            "ok": False,
            "erro": traceback.format_exc(),
        }


def check_colecao(runner, nome, texto, esperados):
    resultado = executar_colecao(texto)

    if not resultado.get("ok"):
        runner.check(f"{nome}: executar", False, resultado.get("erro", "erro desconhecido"))
        return

    obtidos = resultado["estados_set"]
    esperados = {frozenset(estado) for estado in esperados}

    detalhes = (
        "esperado:\n"
        + formatar_colecao(sorted(esperados, key=lambda x: sorted(x)))
        + "\n\nobtido:\n"
        + formatar_colecao(resultado["estados"])
    )

    runner.check(f"{nome}: quantidade", len(resultado["estados"]) == len(obtidos), "tem estado duplicado\n\n" + detalhes)
    runner.check(f"{nome}: estados", obtidos == esperados, detalhes)


def check_colecao_referencia(runner, nome, texto):
    check_colecao(runner, nome, texto, colecao_lr0_referencia(texto))


def run_colecao_tests(runner):
    print("\n== COLECAO LR0 debug imediato ==")

    check_colecao_referencia(
        runner,
        "debug 00.0 - mesmo GOTO gera estado com dois itens",
        "\n".join([
            "S ::= A x",
            "S ::= A",
            "A ::= a",
        ]),
    )

    check_colecao_referencia(
        runner,
        "debug 00.0b - nao filtrar item avancado antes do closure",
        "\n".join([
            "S ::= A A",
            "S ::= A",
            "A ::= a",
        ]),
    )

    check_colecao_referencia(
        runner,
        "debug 00.1 - agrupar avancos pelo mesmo simbolo A",
        "\n".join([
            "S ::= A A",
            "S ::= A",
            "A ::= a",
        ]),
    )

    check_colecao_referencia(
        runner,
        "debug 00.2 - agrupar B e C quando avancam pelo mesmo D",
        "\n".join([
            "S ::= A B",
            "S ::= A C",
            "A ::= a",
            "B ::= D b",
            "C ::= D c",
            "D ::= d",
            "D ::= &",
        ]),
    )

    check_colecao_referencia(
        runner,
        "debug 00.3 - recursao esquerda precisa juntar itens do mesmo goto",
        "\n".join([
            "E ::= E + T",
            "E ::= T",
            "T ::= T * F",
            "T ::= F",
            "F ::= ( E )",
            "F ::= id",
        ]),
    )

    check_colecao_referencia(
        runner,
        "debug 00.4 - recursao mutua com avancos compartilhados",
        "\n".join([
            "S ::= A x",
            "S ::= B y",
            "A ::= B a",
            "A ::= a",
            "B ::= A b",
            "B ::= b",
        ]),
    )

    check_colecao_referencia(
        runner,
        "debug 00.5 - prefixos longos compartilhados",
        "\n".join([
            "S ::= A p q",
            "S ::= A p r",
            "S ::= A s",
            "A ::= a A",
            "A ::= base",
        ]),
    )

    check_colecao(
        runner,
        "debug 01 - producao terminal simples",
        "\n".join([
            "S ::= a",
        ]),
        [
            {
                "S' ::= .S",
                "S ::= .a",
            },
            {
                "S' ::= S.",
            },
            {
                "S ::= a.",
            },
        ],
    )

    check_colecao(
        runner,
        "debug 02 - inicial aponta para nao terminal",
        "\n".join([
            "S ::= A",
            "A ::= a",
        ]),
        [
            {
                "S' ::= .S",
                "S ::= .A",
                "A ::= .a",
            },
            {
                "S' ::= S.",
            },
            {
                "S ::= A.",
            },
            {
                "A ::= a.",
            },
        ],
    )

    check_colecao(
        runner,
        "debug 03 - duas alternativas terminais",
        "\n".join([
            "S ::= A",
            "A ::= a",
            "A ::= b",
        ]),
        [
            {
                "S' ::= .S",
                "S ::= .A",
                "A ::= .a",
                "A ::= .b",
            },
            {
                "S' ::= S.",
            },
            {
                "S ::= A.",
            },
            {
                "A ::= a.",
            },
            {
                "A ::= b.",
            },
        ],
    )

    check_colecao(
        runner,
        "debug 04 - cadeia com dois simbolos",
        "\n".join([
            "S ::= a b",
        ]),
        [
            {
                "S' ::= .S",
                "S ::= .a b",
            },
            {
                "S' ::= S.",
            },
            {
                "S ::= a .b",
            },
            {
                "S ::= a b.",
            },
        ],
    )

    check_colecao(
        runner,
        "debug 05 - closure apos avanco em nao terminal",
        "\n".join([
            "S ::= A B",
            "A ::= a",
            "B ::= b",
        ]),
        [
            {
                "S' ::= .S",
                "S ::= .A B",
                "A ::= .a",
            },
            {
                "S' ::= S.",
            },
            {
                "S ::= A .B",
                "B ::= .b",
            },
            {
                "A ::= a.",
            },
            {
                "S ::= A B.",
            },
            {
                "B ::= b.",
            },
        ],
    )

    print("\n== COLECAO LR0 cabeludos ==")

    check_colecao_referencia(
        runner,
        "cabeludo 01 - estado precisa agrupar avancos pelo mesmo simbolo",
        "\n".join([
            "S ::= A A",
            "S ::= A",
            "A ::= a",
        ]),
    )

    check_colecao_referencia(
        runner,
        "cabeludo 02 - closure depois de avancar nao terminal compartilhado",
        "\n".join([
            "S ::= A B",
            "S ::= A C",
            "A ::= a",
            "B ::= D b",
            "C ::= D c",
            "D ::= d",
            "D ::= &",
        ]),
    )

    check_colecao_referencia(
        runner,
        "cabeludo 03 - recursao esquerda com alternativa terminal",
        "\n".join([
            "E ::= E + T",
            "E ::= T",
            "T ::= T * F",
            "T ::= F",
            "F ::= ( E )",
            "F ::= id",
        ]),
    )

    check_colecao_referencia(
        runner,
        "cabeludo 04 - recursao mutua com varios pontos de closure",
        "\n".join([
            "S ::= A x",
            "S ::= B y",
            "A ::= B a",
            "A ::= a",
            "B ::= A b",
            "B ::= b",
        ]),
    )

    check_colecao_referencia(
        runner,
        "cabeludo 05 - nullable espalhado com simbolos repetidos",
        "\n".join([
            "S ::= A B A",
            "A ::= a A",
            "A ::= &",
            "B ::= b B",
            "B ::= &",
        ]),
    )

    print("\n== COLECAO LR0 stress gerado ==")

    for i in range(1, 41):
        check_colecao(
            runner,
            f"stress terminal simples {i:03d}",
            "\n".join([
                f"S ::= a{i}",
            ]),
            [
                {
                    "S' ::= .S",
                    f"S ::= .a{i}",
                },
                {
                    "S' ::= S.",
                },
                {
                    f"S ::= a{i}.",
                },
            ],
        )

    for i in range(1, 31):
        check_colecao(
            runner,
            f"stress duas alternativas {i:03d}",
            "\n".join([
                "S ::= A",
                f"A ::= a{i}",
                f"A ::= b{i}",
            ]),
            [
                {
                    "S' ::= .S",
                    "S ::= .A",
                    f"A ::= .a{i}",
                    f"A ::= .b{i}",
                },
                {
                    "S' ::= S.",
                },
                {
                    "S ::= A.",
                },
                {
                    f"A ::= a{i}.",
                },
                {
                    f"A ::= b{i}.",
                },
            ],
        )

    print("\n== COLECAO LR0 stress cabeludo gerado ==")

    for i in range(1, 81):
        check_colecao_referencia(
            runner,
            f"stress agrupamento mesmo simbolo {i:03d}",
            "\n".join([
                "S ::= A A",
                "S ::= A B",
                "S ::= A",
                f"A ::= a{i}",
                f"A ::= x{i}",
                f"B ::= b{i}",
            ]),
        )

    for i in range(1, 81):
        check_colecao_referencia(
            runner,
            f"stress ramificacao profunda {i:03d}",
            "\n".join([
                "S ::= A B C",
                "S ::= A C",
                "A ::= D",
                f"A ::= a{i}",
                "B ::= D E",
                f"B ::= b{i}",
                "C ::= E",
                f"C ::= c{i}",
                "D ::= F",
                f"D ::= d{i}",
                "E ::= F",
                f"E ::= e{i}",
                f"F ::= f{i}",
                "F ::= &",
            ]),
        )

    for i in range(1, 61):
        check_colecao_referencia(
            runner,
            f"stress recursao esquerda {i:03d}",
            "\n".join([
                "S ::= E",
                f"E ::= E mais{i} T",
                "E ::= T",
                f"T ::= T vezes{i} F",
                "T ::= F",
                f"F ::= abre{i} E fecha{i}",
                f"F ::= id{i}",
            ]),
        )

    for i in range(1, 41):
        check_colecao_referencia(
            runner,
            f"stress recursao mutua {i:03d}",
            "\n".join([
                "S ::= A fim",
                "A ::= B x",
                f"A ::= a{i}",
                "B ::= C y",
                f"B ::= b{i}",
                "C ::= A z",
                f"C ::= c{i}",
            ]),
        )

    for i in range(1, 41):
        check_colecao_referencia(
            runner,
            f"stress epsilon e repeticao {i:03d}",
            "\n".join([
                "S ::= A B A C",
                f"A ::= a{i} A",
                "A ::= &",
                f"B ::= b{i} B",
                "B ::= A",
                f"C ::= c{i}",
                "C ::= &",
            ]),
        )

    for i in range(1, 31):
        check_colecao_referencia(
            runner,
            f"stress prefixos longos compartilhados {i:03d}",
            "\n".join([
                "S ::= A p q",
                "S ::= A p r",
                "S ::= A s",
                f"A ::= a{i} A",
                f"A ::= base{i}",
            ]),
        )

    for i in range(1, 31):
        check_colecao(
            runner,
            f"stress cadeia dois terminais {i:03d}",
            "\n".join([
                f"S ::= a{i} b{i}",
            ]),
            [
                {
                    "S' ::= .S",
                    f"S ::= .a{i} b{i}",
                },
                {
                    "S' ::= S.",
                },
                {
                    f"S ::= a{i} .b{i}",
                },
                {
                    f"S ::= a{i} b{i}.",
                },
            ],
        )


def main():
    print("Testador da colecao de itens LR0 da GramaticaLivreDeContexto")
    print(f"Pasta testada: {SINTATICO_DIR}")

    runner = TestRunner()
    run_colecao_tests(runner)
    runner.summary()


if __name__ == "__main__":
    main()
