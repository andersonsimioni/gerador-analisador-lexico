from pathlib import Path
import re
import sys
import traceback


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
SINTATICO_DIR = BASE_DIR / "analisador_sintatico"
EPSILON = "&"
FIM = "$"


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


def parse_producoes(texto):
    linhas = [x.strip() for x in texto.splitlines() if x.strip()]
    cabecas_originais = [x.split("::=")[0].strip() for x in linhas]
    cabeca_inicial = cabecas_originais[0]
    nova_cabeca = cabeca_inicial

    while nova_cabeca in cabecas_originais:
        nova_cabeca += "'"

    producoes = [(nova_cabeca, [cabeca_inicial])]
    for linha in linhas:
        cabeca, corpo = linha.split("::=")
        producoes.append((cabeca.strip(), corpo.strip().split()))

    return producoes, nova_cabeca


def producao_para_string(producao):
    cabeca, corpo = producao
    return f"{cabeca} ::= {' '.join(corpo)}"


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


def firsts_referencia(producoes, cabecas):
    firsts = {cabeca: set() for cabeca in cabecas}
    mudou = True

    while mudou:
        mudou = False
        for cabeca, corpo in producoes:
            todos_nullable = True

            for simbolo in corpo:
                if simbolo == EPSILON:
                    if EPSILON not in firsts[cabeca]:
                        firsts[cabeca].add(EPSILON)
                        mudou = True
                    break

                if simbolo not in cabecas:
                    if simbolo not in firsts[cabeca]:
                        firsts[cabeca].add(simbolo)
                        mudou = True
                    todos_nullable = False
                    break

                for x in firsts[simbolo]:
                    if x != EPSILON and x not in firsts[cabeca]:
                        firsts[cabeca].add(x)
                        mudou = True

                if EPSILON not in firsts[simbolo]:
                    todos_nullable = False
                    break

            if todos_nullable and EPSILON not in firsts[cabeca]:
                firsts[cabeca].add(EPSILON)
                mudou = True

    return firsts


def first_sequencia(seq, firsts, cabecas):
    saida = set()

    if not seq:
        return {EPSILON}

    for simbolo in seq:
        if simbolo == EPSILON:
            saida.add(EPSILON)
            return saida

        if simbolo not in cabecas:
            saida.add(simbolo)
            return saida

        saida.update(x for x in firsts[simbolo] if x != EPSILON)
        if EPSILON not in firsts[simbolo]:
            return saida

    saida.add(EPSILON)
    return saida


def follows_referencia(producoes, cabecas, cabeca_inicial):
    firsts = firsts_referencia(producoes, cabecas)
    follows = {cabeca: set() for cabeca in cabecas}
    follows[cabeca_inicial].add(FIM)
    mudou = True

    while mudou:
        mudou = False
        for cabeca, corpo in producoes:
            for i, simbolo in enumerate(corpo):
                if simbolo not in cabecas:
                    continue

                beta = corpo[i + 1:]
                first_beta = first_sequencia(beta, firsts, cabecas)

                for x in first_beta:
                    if x != EPSILON and x not in follows[simbolo]:
                        follows[simbolo].add(x)
                        mudou = True

                if EPSILON in first_beta:
                    for x in follows[cabeca]:
                        if x not in follows[simbolo]:
                            follows[simbolo].add(x)
                            mudou = True

    return follows


def colecao_gotos_slr_referencia(texto):
    producoes, cabeca_estendida = parse_producoes(texto)
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

    follows = follows_referencia(producoes, cabecas, cabeca_estendida)
    action = set()
    goto_table = set()

    for origem, destinos in gotos.items():
        for simbolo, destino in destinos.items():
            if simbolo in cabecas:
                goto_table.add((estados_str[origem], simbolo, estados_str[destino]))
            else:
                action.add((estados_str[origem], simbolo, ("shift", estados_str[destino])))

    for i_estado, estado in enumerate(estados):
        for indice, ponto in estado:
            cabeca, corpo = producoes[indice]
            if ponto < len(corpo):
                continue

            if cabeca == cabeca_estendida:
                action.add((estados_str[i_estado], FIM, ("accept",)))
            else:
                prod_str = producao_para_string(producoes[indice])
                for terminal in follows[cabeca]:
                    action.add((estados_str[i_estado], terminal, ("reduce", prod_str)))

    return estados_str, action, goto_table


def normalizar_producao_str(valor):
    texto = str(valor)
    texto = texto.replace(chr(194) + chr(183), ".")
    texto = texto.replace(chr(183), ".")
    texto = texto.replace(".", "")
    texto = " ".join(texto.split())
    return texto


def normalizar_action(valor, estados):
    if isinstance(valor, dict):
        tipo = str(valor.get("tipo", valor.get("type", valor.get("acao", valor.get("action", ""))))).lower()
        destino = valor.get("estado", valor.get("destino", valor.get("to", None)))
        prod = valor.get("producao", valor.get("prod", valor.get("reduce", None)))
    elif isinstance(valor, (tuple, list)):
        tipo = str(valor[0]).lower() if valor else ""
        destino = valor[1] if len(valor) > 1 else None
        prod = valor[1] if len(valor) > 1 else None
    else:
        texto = str(valor).strip()
        low = texto.lower()
        if low.startswith("s") or "shift" in low:
            nums = re.findall(r"\d+", texto)
            return ("shift", estados[int(nums[-1])]) if nums else ("desconhecido", texto)
        if "accept" in low or low == "acc":
            return ("accept",)
        if low.startswith("r") or "reduce" in low:
            prod_txt = re.sub(r"(?i)reduce", "", texto).strip()
            prod_txt = re.sub(r"^r\s*", "", prod_txt).strip()
            return ("reduce", normalizar_producao_str(prod_txt))
        return ("desconhecido", texto)

    if tipo.startswith("s") or "shift" in tipo:
        return ("shift", estados[int(destino)])
    if "accept" in tipo or tipo == "acc":
        return ("accept",)
    if tipo.startswith("r") or "reduce" in tipo:
        return ("reduce", normalizar_producao_str(prod))

    return ("desconhecido", str(valor))


def normalizar_destino_estado(valor):
    if isinstance(valor, str):
        nums = re.findall(r"\d+", valor)
        return int(nums[-1]) if nums else int(valor)
    return int(valor)


def executar_tabela(texto):
    try:
        if str(SINTATICO_DIR) not in sys.path:
            sys.path.insert(0, str(SINTATICO_DIR))

        gramatica_livre = __import__("gramatica_livre")
        glc = gramatica_livre.GramaticaLivreDeContexto(texto)
        glc_ext = glc.GLC_exntedida

        tabela = getattr(glc_ext, "tabela_SLR", None)
        if tabela is None:
            tabela = glc_ext.calcula_tabela_SLR()

        if isinstance(tabela, tuple) and len(tabela) == 2:
            action_table, goto_table = tabela
        elif isinstance(tabela, dict):
            action_table = tabela.get("action", tabela.get("ACTION", tabela.get("action_table", {})))
            goto_table = tabela.get("goto", tabela.get("GOTO", tabela.get("goto_table", {})))
        else:
            return {"ok": False, "erro": f"formato de tabela desconhecido: {tabela!r}"}

        estados = [normalizar_estado(estado) for estado in glc.get_itens_LR0()]
        action = set()
        gotos = set()

        for origem, linha in action_table.items():
            for terminal, valor in linha.items():
                action.add((estados[int(origem)], terminal, normalizar_action(valor, estados)))

        for origem, linha in goto_table.items():
            for simbolo, destino in linha.items():
                gotos.add((estados[int(origem)], simbolo, estados[normalizar_destino_estado(destino)]))

        return {
            "ok": True,
            "action": action,
            "goto": gotos,
        }
    except Exception:
        return {
            "ok": False,
            "erro": traceback.format_exc(),
        }


def formatar_action(actions):
    linhas = []
    for estado, terminal, acao in sorted(actions, key=lambda x: (sorted(x[0]), x[1], str(x[2]))):
        linhas.append(f"terminal {terminal}: {acao}")
        for item in sorted(estado):
            linhas.append(f"  {item}")
    return "\n".join(linhas)


def formatar_goto(gotos):
    linhas = []
    for estado, simbolo, destino in sorted(gotos, key=lambda x: (sorted(x[0]), x[1], sorted(x[2]))):
        linhas.append(f"simbolo {simbolo}:")
        linhas.append("  origem:")
        for item in sorted(estado):
            linhas.append(f"    {item}")
        linhas.append("  destino:")
        for item in sorted(destino):
            linhas.append(f"    {item}")
    return "\n".join(linhas)


def check_tabela(runner, nome, texto):
    resultado = executar_tabela(texto)

    if not resultado.get("ok"):
        runner.check(f"{nome}: executar", False, resultado.get("erro", "erro desconhecido"))
        return

    _, action_esperado, goto_esperado = colecao_gotos_slr_referencia(texto)
    action_obtido = resultado["action"]
    goto_obtido = resultado["goto"]

    runner.check(
        f"{nome}: ACTION",
        action_obtido == action_esperado,
        "esperado:\n"
        + formatar_action(action_esperado)
        + "\n\nobtido:\n"
        + formatar_action(action_obtido)
    )

    runner.check(
        f"{nome}: GOTO_TABLE",
        goto_obtido == goto_esperado,
        "esperado:\n"
        + formatar_goto(goto_esperado)
        + "\n\nobtido:\n"
        + formatar_goto(goto_obtido)
    )


def run_tabela_tests(runner):
    print("\n== TABELA SLR debug imediato ==")

    check_tabela(
        runner,
        "debug 01 - terminal simples com accept e reduce",
        "\n".join([
            "S ::= a",
        ]),
    )

    check_tabela(
        runner,
        "debug 02 - reduce usa FOLLOW da cabeca",
        "\n".join([
            "S ::= A b",
            "A ::= a",
        ]),
    )

    check_tabela(
        runner,
        "debug 03 - epsilon reduz no follow",
        "\n".join([
            "S ::= A b",
            "A ::= a",
            "A ::= &",
        ]),
    )

    check_tabela(
        runner,
        "debug 04 - goto table de nao terminais",
        "\n".join([
            "S ::= A B",
            "A ::= a",
            "B ::= b",
        ]),
    )

    check_tabela(
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

    print("\n== TABELA SLR stress gerado ==")

    for i in range(1, 31):
        check_tabela(
            runner,
            f"stress terminal {i:03d}",
            "\n".join([
                f"S ::= a{i}",
            ]),
        )

    for i in range(1, 31):
        check_tabela(
            runner,
            f"stress follow simples {i:03d}",
            "\n".join([
                "S ::= A B",
                f"A ::= a{i}",
                f"B ::= b{i}",
            ]),
        )

    for i in range(1, 31):
        check_tabela(
            runner,
            f"stress epsilon {i:03d}",
            "\n".join([
                "S ::= A B",
                f"A ::= a{i}",
                "A ::= &",
                f"B ::= b{i}",
                "B ::= &",
            ]),
        )

    for i in range(1, 31):
        check_tabela(
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


def main():
    print("Testador da tabela SLR da GramaticaLivreDeContexto")
    print(f"Pasta testada: {SINTATICO_DIR}")

    runner = TestRunner()
    run_tabela_tests(runner)
    runner.summary()


if __name__ == "__main__":
    main()
