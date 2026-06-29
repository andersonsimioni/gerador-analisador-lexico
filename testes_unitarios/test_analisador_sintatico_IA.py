from pathlib import Path
import sys


BASE_DIR = Path(__file__).resolve().parent.parent
SINTATICO_DIR = BASE_DIR / "analisador_sintatico"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if str(SINTATICO_DIR) not in sys.path:
    sys.path.insert(0, str(SINTATICO_DIR))

from gramatica_livre import GramaticaLivreDeContexto
from analisador_sintatico import AnalisadorSintatico


class TestRunner:
    def __init__(self):
        self.total = 0
        self.passed = 0

    def check(self, name, condition):
        self.total += 1

        if condition:
            self.passed += 1
            print(f"[OK] {name}")
            return

        print(f"[FALHOU] {name}")

    def summary(self):
        failed = self.total - self.passed
        print("\n== Resumo ==")
        print(f"Passou: {self.passed}/{self.total}")
        print(f"Falhou: {failed}/{self.total}")


def criar_analisador(texto_gramatica):
    glc = GramaticaLivreDeContexto(texto_gramatica.strip())
    return AnalisadorSintatico(glc)


def main():
    runner = TestRunner()

    gramatica_expressao = """
E ::= E + T
E ::= T
T ::= T * F
T ::= F
F ::= ( E )
F ::= id
"""

    analisador_expressao = criar_analisador(gramatica_expressao)

    runner.check(
        "expressao aceita id + id * id",
        analisador_expressao.aceita(["id", "+", "id", "*", "id"])
    )

    runner.check(
        "expressao rejeita operador sem operando",
        not analisador_expressao.aceita(["id", "+", "*", "id"])
    )

    gramatica_epsilon = """
S ::= A b
A ::= &
A ::= a
"""

    analisador_epsilon = criar_analisador(gramatica_epsilon)

    runner.check(
        "epsilon aceita quando A some",
        analisador_epsilon.aceita(["b"])
    )

    runner.check(
        "epsilon aceita quando A vira terminal",
        analisador_epsilon.aceita(["a", "b"])
    )

    runner.check(
        "epsilon rejeita token sobrando",
        not analisador_epsilon.aceita(["a", "a", "b"])
    )

    runner.summary()

    if runner.passed != runner.total:
        sys.exit(1)


if __name__ == "__main__":
    main()
