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


def formatar_transicoes(transicoes):
    linhas = []
    for origem, simbolo, destino in sorted(transicoes, key=lambda x: (sorted(x[0]), x[1], sorted(x[2]))):
        linhas.append(f"com {simbolo}:")
        linhas.append("  origem:")
        for item in sorted(origem):
            linhas.append(f"    {item}")
        linhas.append("  destino:")
        for item in sorted(destino):
            linhas.append(f"    {item}")
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

    return producoes


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


def colecao_e_gotos_referencia(texto):
    producoes = parse_producoes(texto)
    cabecas = {cabeca for cabeca, _ in producoes}
    inicial = closure_referencia(producoes, cabecas, {(0, 0)})
    estados = [inicial]
    vistos = {inicial: 0}
    gotos = {}
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

        for simbolo, avancos in avancos_por_simbolo.items():
            novo_estado = closure_referencia(producoes, cabecas, avancos)
            if novo_estado not in vistos:
                vistos[novo_estado] = len(estados)
                estados.append(novo_estado)

            gotos.setdefault(i, {})[simbolo] = vistos[novo_estado]

        i += 1

    estados_str = [
        frozenset(item_para_string(producoes, item) for item in estado)
        for estado in estados
    ]

    transicoes = set()
    for origem, destinos in gotos.items():
        for simbolo, destino in destinos.items():
            transicoes.add((estados_str[origem], simbolo, estados_str[destino]))

    return estados_str, transicoes


def executar_gotos(texto):
    try:
        if str(SINTATICO_DIR) not in sys.path:
            sys.path.insert(0, str(SINTATICO_DIR))

        gramatica_livre = __import__("gramatica_livre")
        glc = gramatica_livre.GramaticaLivreDeContexto(texto)

        estados = [normalizar_estado(estado) for estado in glc.get_itens_LR0()]
        gotos = glc.get_gotos()

        transicoes = set()
        for origem, destinos in gotos.items():
            for simbolo, destino in destinos.items():
                transicoes.add((estados[origem], simbolo, estados[destino]))

        return {
            "ok": True,
            "estados": estados,
            "transicoes": transicoes,
            "gotos": gotos,
        }
    except Exception:
        return {
            "ok": False,
            "erro": traceback.format_exc(),
        }


def check_gotos(runner, nome, texto):
    resultado = executar_gotos(texto)

    if not resultado.get("ok"):
        runner.check(f"{nome}: executar", False, resultado.get("erro", "erro desconhecido"))
        return

    _, esperadas = colecao_e_gotos_referencia(texto)
    obtidas = resultado["transicoes"]

    detalhes = (
        "esperado:\n"
        + formatar_transicoes(esperadas)
        + "\n\nobtido:\n"
        + formatar_transicoes(obtidas)
    )

    runner.check(f"{nome}: tem gotos", len(resultado["gotos"]) > 0, f"get_gotos retornou vazio: {resultado['gotos']!r}")
    runner.check(f"{nome}: transicoes", obtidas == esperadas, detalhes)


def run_goto_tests(runner):
    print("\n== GOTO LR0 debug imediato ==")

    check_gotos(
        runner,
        "debug 01 - terminal simples",
        "\n".join([
            "S ::= a",
        ]),
    )

    check_gotos(
        runner,
        "debug 02 - goto por nao terminal",
        "\n".join([
            "S ::= A",
            "A ::= a",
        ]),
    )

    check_gotos(
        runner,
        "debug 03 - mesmo simbolo junta dois avancos",
        "\n".join([
            "S ::= A x",
            "S ::= A",
            "A ::= a",
        ]),
    )

    check_gotos(
        runner,
        "debug 04 - B e C avancam pelo mesmo D",
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

    check_gotos(
        runner,
        "debug 05 - expressao classica",
        "\n".join([
            "E ::= E + T",
            "E ::= T",
            "T ::= T * F",
            "T ::= F",
            "F ::= ( E )",
            "F ::= id",
        ]),
    )

    print("\n== GOTO LR0 stress gerado ==")

    for i in range(1, 61):
        check_gotos(
            runner,
            f"stress terminal simples {i:03d}",
            "\n".join([
                f"S ::= a{i}",
            ]),
        )

    for i in range(1, 61):
        check_gotos(
            runner,
            f"stress alternativas {i:03d}",
            "\n".join([
                "S ::= A",
                f"A ::= a{i}",
                f"A ::= b{i}",
                f"A ::= c{i}",
            ]),
        )

    for i in range(1, 61):
        check_gotos(
            runner,
            f"stress agrupamento {i:03d}",
            "\n".join([
                "S ::= A A",
                "S ::= A B",
                "S ::= A",
                f"A ::= a{i}",
                f"A ::= x{i}",
                f"B ::= b{i}",
            ]),
        )

    for i in range(1, 61):
        check_gotos(
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
        check_gotos(
            runner,
            f"stress epsilon {i:03d}",
            "\n".join([
                "S ::= A B A",
                f"A ::= a{i} A",
                "A ::= &",
                f"B ::= b{i}",
                "B ::= A",
            ]),
        )

    print("\n== GOTO LR0 stress extremo ==")

    for i in range(1, 121):
        check_gotos(
            runner,
            f"extremo recursao mutua tripla {i:03d}",
            "\n".join([
                "S ::= A fim",
                "S ::= B fim",
                "A ::= B ax",
                f"A ::= a{i}",
                "B ::= C by",
                f"B ::= b{i}",
                "C ::= A cz",
                f"C ::= c{i}",
            ]),
        )

    for i in range(1, 121):
        check_gotos(
            runner,
            f"extremo prefixos compartilhados {i:03d}",
            "\n".join([
                "S ::= A p q r",
                "S ::= A p q s",
                "S ::= A p t",
                "S ::= A u",
                f"A ::= a{i} A",
                f"A ::= base{i}",
            ]),
        )

    for i in range(1, 121):
        check_gotos(
            runner,
            f"extremo ramificacao profunda {i:03d}",
            "\n".join([
                "S ::= A B C D",
                "S ::= A C E",
                "A ::= F",
                f"A ::= a{i}",
                "B ::= F G",
                f"B ::= b{i}",
                "C ::= G H",
                f"C ::= c{i}",
                "D ::= H",
                f"D ::= d{i}",
                "E ::= F H",
                f"E ::= e{i}",
                "F ::= I",
                f"F ::= f{i}",
                "G ::= I",
                f"G ::= g{i}",
                "H ::= I",
                f"H ::= h{i}",
                f"I ::= i{i}",
                "I ::= &",
            ]),
        )

    for i in range(1, 101):
        check_gotos(
            runner,
            f"extremo estilo comandos {i:03d}",
            "\n".join([
                "S ::= Bloco",
                "Bloco ::= abre Lista fecha",
                "Lista ::= Stmt Lista",
                "Lista ::= &",
                "Stmt ::= id atr Expr pv",
                "Stmt ::= se Expr entao Stmt Senao",
                "Senao ::= senao Stmt",
                "Senao ::= &",
                f"Expr ::= Expr soma{i} Termo",
                "Expr ::= Termo",
                f"Termo ::= Termo mult{i} Fator",
                "Termo ::= Fator",
                "Fator ::= id",
                "Fator ::= num",
                "Fator ::= abre Expr fecha",
            ]),
        )

    for i in range(1, 101):
        check_gotos(
            runner,
            f"extremo nullable espalhado {i:03d}",
            "\n".join([
                "S ::= A B C A D",
                f"A ::= a{i} A",
                "A ::= &",
                f"B ::= b{i} B",
                "B ::= A",
                f"C ::= c{i} C",
                "C ::= B",
                "C ::= &",
                f"D ::= d{i}",
                "D ::= C",
            ]),
        )

    for i in range(1, 91):
        check_gotos(
            runner,
            f"extremo fanout grande {i:03d}",
            "\n".join([
                "S ::= A",
                "S ::= B",
                "S ::= C",
                "S ::= D",
                "A ::= X a",
                "B ::= X b",
                "C ::= X c",
                "D ::= X d",
                f"X ::= x{i}",
                f"X ::= y{i}",
                f"X ::= z{i}",
                "X ::= &",
            ]),
        )

    for i in range(1, 71):
        check_gotos(
            runner,
            f"extremo cadeia profunda {i:03d}",
            "\n".join([
                "S ::= A1 fim",
                "A1 ::= A2 x1",
                "A1 ::= a1",
                "A2 ::= A3 x2",
                "A2 ::= a2",
                "A3 ::= A4 x3",
                "A3 ::= a3",
                "A4 ::= A5 x4",
                "A4 ::= a4",
                "A5 ::= A6 x5",
                "A5 ::= a5",
                "A6 ::= A7 x6",
                "A6 ::= a6",
                "A7 ::= A8 x7",
                "A7 ::= a7",
                f"A8 ::= a8_{i}",
                "A8 ::= &",
            ]),
        )


def main():
    print("Testador de GOTOs LR0 da GramaticaLivreDeContexto")
    print(f"Pasta testada: {SINTATICO_DIR}")

    runner = TestRunner()
    run_goto_tests(runner)
    runner.summary()


if __name__ == "__main__":
    main()
