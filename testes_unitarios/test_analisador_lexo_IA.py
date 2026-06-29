from pathlib import Path
import sys
import tempfile
import traceback


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
AUTOMATO_DIR = BASE_DIR / "automato"
ANALISADOR_DIR = BASE_DIR / "analisador_lexico"
EXEMPLOS_DIR = BASE_DIR / "exemplos"


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

    def check_silent(self, name, condition, details=""):
        self.total += 1
        if condition:
            self.passed += 1
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
    sys.path.insert(0, str(AUTOMATO_DIR))
    sys.path.insert(0, str(BASE_DIR))
    sys.path.insert(0, str(ANALISADOR_DIR))


def load_analisador(runner):
    print("\n== Imports ==")
    try:
        module = __import__("analisador_lexico")
        runner.check("import analisador_lexico", True)
        return module.AnalisadorLexo
    except Exception:
        runner.check("import analisador_lexico", False, traceback.format_exc())
        return None


def build_analisador(runner, AnalisadorLexo):
    print("\n== Build analisador ==")
    path_definicoes = EXEMPLOS_DIR / "lexico_defs.txt"

    try:
        analisador = AnalisadorLexo(str(path_definicoes))
        runner.check("AnalisadorLexo(exemplos/lexico_defs.txt)", True)
        return analisador
    except Exception:
        runner.check("AnalisadorLexo(exemplos/lexico_defs.txt)", False, traceback.format_exc())
        return None


def get_classes(analisador, palavra):
    return [
        classe for classe in analisador.definicoes_regulares.keys()
        if analisador.definicoes_regulares[classe].reconhece(palavra)
    ]


def check_classes(runner, analisador, palavra, esperadas):
    try:
        obtidas = get_classes(analisador, palavra)
        runner.check(
            f"classifica({palavra!r}) == {esperadas!r}",
            obtidas == esperadas,
            f"obtido: {obtidas!r}"
        )
    except Exception:
        runner.check(f"classifica({palavra!r}) == {esperadas!r}", False, traceback.format_exc())


def check_tabela_tokens(runner, analisador):
    print("\n== Tabela de tokens ==")
    path_palavras = EXEMPLOS_DIR / "lexico_misto.txt"

    esperado = "\n".join([
        "<if,keyword_if>",
        "<else,keyword_else>",
        "<while,keyword_while>",
        "<true,bool>",
        "<false,bool>",
        "<id,1>",
        "<id,2>",
        "<id,3>",
        "<id,4>",
        "<id,5>",
        "<id,6>",
        "<id,7>",
        "<id,8>",
        "<abc_def,snake_id>",
        "<a_b_c1,snake_id>",
        "<abc_,snake_id>",
        "<_abc,erro!>",
        "<snake__case,snake_id>",
        "<ABC_123,snake_id>",
        "<0,num>",
        "<1,num>",
        "<9,num>",
        "<21,num>",
        "<3444,num>",
        "<000,bin>",
        "<01,bin>",
        "<0x0,hex>",
        "<0xff,hex>",
        "<0xA1,hex>",
        "<0xABCDEF,hex>",
        "<0xg,erro!>",
        "<0x,erro!>",
        "<0b0,bin_prefix>",
        "<0b1,bin_prefix>",
        "<0b10101,bin_prefix>",
        "<0b102,erro!>",
        "<12.34,float>",
        "<0.5,float>",
        "<42.,erro!>",
        "<.42,erro!>",
        "<1.2.3,erro!>",
        "<abc@def.com,email>",
        "<a@b.c,email>",
        "<a@b,erro!>",
        "<ab@cd.ef,email>",
        "<01011,bin>",
        "<011,bin>",
        "<012,erro!>",
        "<id,9>",
        "<id,10>",
        "<id,11>",
        "<id,12>",
        "<id,13>",
        "<id,14>",
        "<id,15>",
        "<id,16>",
        "<id,17>",
        "<id,18>",
        "<a*b,literal_star>",
        "<id,19>",
        "<(ab),literal_paren>",
        "<[,lbracket>",
        "<],rbracket>",
        "<[a-z],literal_range>",
        "<|,op_pipe>",
        "<+,op_plus>",
        "<*,op_star>",
        "<=,op_assign>",
        "<==,op_eq>",
        "<===,erro!>",
        "<(,lparen>",
        "<),rparen>",
        "<_,erro!>",
    ])

    try:
        obtido = analisador.get_tabela_tokens(str(path_palavras))
        runner.check("get_tabela_tokens(exemplos/lexico_misto.txt)", obtido == esperado, f"obtido:\n{obtido!r}\n\nesperado:\n{esperado!r}")
    except Exception:
        runner.check("get_tabela_tokens(exemplos/lexico_misto.txt)", False, traceback.format_exc())


def criar_analisador_temp(AnalisadorLexo, definicoes):
    arquivo = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
    arquivo.write(definicoes)
    arquivo.close()
    return AnalisadorLexo(arquivo.name)


def gerar_palavras_pesadas():
    palavras = []

    bases = ["a", "b", "ab", "ba", "abc", "teste", "Alpha", "Z", "xYz", "var"]
    sufixos = ["", "0", "1", "12", "999", "abc", "_", "_x", "x_y", "123abc"]

    for base in bases:
        for sufixo in sufixos:
            palavras.append(base + sufixo)
            palavras.append(sufixo + base)

    for i in range(250):
        palavras.append(str(i))
        palavras.append(f"{i}.{i + 1}")
        palavras.append(f"0x{i:x}")
        palavras.append("0b" + bin(i % 128)[2:])

    for i in range(150):
        meio = "ab" * (i % 12)
        palavras.append(meio + "abb")
        palavras.append(meio + "aba")
        palavras.append("a" * (i % 20))
        palavras.append("b" * (i % 20))

    for i in range(100):
        palavras.append(f"a{i}@b{i}.c")
        palavras.append(f"abc{i}@def{i}.com")
        palavras.append(f"abc{i}@def")
        palavras.append(f"abc@def{i}.com")

    palavras.extend([
        "a*b", "(ab)", "[a-z]", "+", "*", "|", "=", "==", "===",
        "0x", "0xg", "0b102", "12.", ".12", "_abc", "_", "",
    ])

    return palavras


def check_regex_com_espacos(runner, AnalisadorLexo):
    print("\n== Regex com espacos internos ==")

    definicoes_com_espacos = "\n".join([
        "id: [a-zA-Z] ( [a-zA-Z] | [0-9] ) *",
        "num: [1-9] ( [0-9] ) * | 0",
        "float: [0-9] [0-9] * \\. [0-9] [0-9] *",
        "hex: 0x [0-9a-fA-F] [0-9a-fA-F] *",
        "bin_prefix: 0b ( 0 | 1 ) ( 0 | 1 ) *",
        "email: [a-z] [a-z] * @ [a-z] [a-z] * \\. [a-z] [a-z] *",
        "ab_final: ( a | b ) * a b b",
        "literal_star: a \\* b",
        "literal_paren: \\( a b \\)",
    ])

    definicoes_sem_espacos = definicoes_com_espacos.replace(" ", "")

    try:
        analisador_com_espacos = criar_analisador_temp(AnalisadorLexo, definicoes_com_espacos)
        analisador_sem_espacos = criar_analisador_temp(AnalisadorLexo, definicoes_sem_espacos)
        runner.check("monta analisador com regex espacadas", True)
    except Exception:
        runner.check("monta analisador com regex espacadas", False, traceback.format_exc())
        return

    palavras = gerar_palavras_pesadas()

    for i, palavra in enumerate(palavras[:1000]):
        try:
            esperado = get_classes(analisador_sem_espacos, palavra)
            obtido = get_classes(analisador_com_espacos, palavra)
            runner.check_silent(
                f"regex espacada stress {i:04d} {palavra!r}",
                obtido == esperado,
                f"obtido: {obtido!r}\nesperado: {esperado!r}"
            )
        except Exception:
            runner.check_silent(f"regex espacada stress {i:04d} {palavra!r}", False, traceback.format_exc())


def run_tests(runner, analisador, AnalisadorLexo):
    print("\n== Definicoes carregadas ==")
    esperadas = [
        "keyword_if", "keyword_else", "keyword_while", "bool",
        "id", "snake_id", "float", "num", "hex", "bin_prefix", "bin", "email",
        "palavra_a", "palavra_b", "ab_final",
        "literal_range", "literal_star", "literal_paren",
        "op_eq", "op_assign", "op_plus", "op_star", "op_pipe",
        "lparen", "rparen", "lbracket", "rbracket",
        "letra", "digito", "zero_ou_a"
    ]
    obtidas = list(analisador.definicoes_regulares.keys())
    runner.check("classes carregadas na ordem do arquivo", obtidas == esperadas, f"obtido: {obtidas!r}")

    print("\n== Classificacao direta ==")
    cases = [
        ("if", ["keyword_if", "id", "snake_id"]),
        ("else", ["keyword_else", "id", "snake_id"]),
        ("while", ["keyword_while", "id", "snake_id"]),
        ("true", ["bool", "id", "snake_id"]),
        ("false", ["bool", "id", "snake_id"]),
        ("iff", ["id", "snake_id"]),
        ("while1", ["id", "snake_id"]),
        ("a", ["id", "snake_id", "palavra_a", "palavra_b", "letra", "zero_ou_a"]),
        ("Z", ["id", "snake_id", "letra"]),
        ("a1", ["id", "snake_id"]),
        ("teste2", ["id", "snake_id"]),
        ("alpha123", ["id", "snake_id"]),
        ("abc_def", ["snake_id"]),
        ("a_b_c1", ["snake_id"]),
        ("abc_", ["snake_id"]),
        ("_abc", []),
        ("snake__case", ["snake_id"]),
        ("ABC_123", ["snake_id"]),
        ("0", ["num", "digito"]),
        ("1", ["num", "digito"]),
        ("21", ["num"]),
        ("3444", ["num"]),
        ("000", ["bin"]),
        ("01", ["bin"]),
        ("0x0", ["hex"]),
        ("0xff", ["hex"]),
        ("0xA1", ["hex"]),
        ("0xABCDEF", ["hex"]),
        ("0xg", []),
        ("0b0", ["bin_prefix"]),
        ("0b1", ["bin_prefix"]),
        ("0b10101", ["bin_prefix"]),
        ("0b102", []),
        ("12.34", ["float"]),
        ("0.5", ["float"]),
        ("42.", []),
        (".42", []),
        ("1.2.3", []),
        ("abc@def.com", ["email"]),
        ("a@b.c", ["email"]),
        ("a@b", []),
        ("ab@cd.ef", ["email"]),
        ("01011", ["bin"]),
        ("aa", ["id", "snake_id", "palavra_a", "palavra_b", "zero_ou_a"]),
        ("bbbba", ["id", "snake_id", "palavra_a", "palavra_b"]),
        ("ababab", ["id", "snake_id", "palavra_a", "palavra_b"]),
        ("bbbbb", ["id", "snake_id", "palavra_a", "palavra_b"]),
        ("abb", ["id", "snake_id", "palavra_a", "palavra_b", "ab_final"]),
        ("aabb", ["id", "snake_id", "palavra_a", "palavra_b", "ab_final"]),
        ("babb", ["id", "snake_id", "palavra_a", "palavra_b", "ab_final"]),
        ("ababa", ["id", "snake_id", "palavra_a", "palavra_b"]),
        ("aaaa", ["id", "snake_id", "palavra_a", "palavra_b", "zero_ou_a"]),
        ("b", ["id", "snake_id", "palavra_a", "palavra_b", "letra"]),
        ("a*b", ["literal_star"]),
        ("(ab)", ["literal_paren"]),
        ("[", ["lbracket"]),
        ("]", ["rbracket"]),
        ("[a-z]", ["literal_range"]),
        ("|", ["op_pipe"]),
        ("+", ["op_plus"]),
        ("*", ["op_star"]),
        ("=", ["op_assign"]),
        ("==", ["op_eq"]),
        ("===", []),
        ("(", ["lparen"]),
        (")", ["rparen"]),
        ("_", []),
        ("0x", []),
        ("012", []),
    ]

    for palavra, classes in cases:
        check_classes(runner, analisador, palavra, classes)

    check_tabela_tokens(runner, analisador)
    check_regex_com_espacos(runner, AnalisadorLexo)


def main():
    print("Testador do AnalisadorLexo")
    print(f"Pasta testada: {ANALISADOR_DIR}")
    runner = TestRunner()

    add_paths()
    AnalisadorLexo = load_analisador(runner)
    if AnalisadorLexo is None:
        runner.summary()
        return

    analisador = build_analisador(runner, AnalisadorLexo)
    if analisador is not None:
        run_tests(runner, analisador, AnalisadorLexo)

    runner.summary()


if __name__ == "__main__":
    main()
