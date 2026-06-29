from pathlib import Path
import os
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parent
TESTES_DIR = BASE_DIR / "testes_unitarios"


def main():
    testes = sorted(TESTES_DIR.glob("*.py"))
    falharam = []

    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

    for teste in testes:
        print(f"\n== {teste.name} ==")
        resultado = subprocess.run([sys.executable, "-X", "utf8", str(teste)])

        if(resultado.returncode != 0):
            falharam.append(teste.name)

    print("\n== RESULTADO FINAL ==")

    if(len(falharam) == 0):
        print("TODOS PASSARAM")
        return 0

    print("FALHARAM:")
    for teste in falharam:
        print(teste)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
