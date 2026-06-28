from flask import Flask, render_template, request
from graphviz import Digraph
from pathlib import Path
import sys
import tempfile

BASE_DIR = Path(__file__).resolve().parent.parent
AUTOMATO_DIR = BASE_DIR / "automato"
ANALISADOR_DIR = BASE_DIR / "analisador_lexo"
sys.path.insert(0, str(AUTOMATO_DIR))
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(ANALISADOR_DIR))

from automato.automato import Automato
from analisador_lexo import AnalisadorLexo

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    tabela_tokens = ""
    automata_svgs = []

    if request.method == "POST":

        def_file = request.files.get("definitions")
        test_file = request.files.get("tests")

        if not def_file or def_file.filename == "":
            return "Erro: arquivo de definições não enviado"

        if not test_file or test_file.filename == "":
            return "Erro: arquivo de testes não enviado"

        def_content = def_file.read().decode("utf-8")
        test_content = test_file.read().decode("utf-8")

        definitions = parse_definitions_text(def_content)

        automata = []

        for name, regex in definitions:
            automaton = Automato.parse_regex(regex)
            automata.append((name, automaton))

        for name, automaton in automata:
            automata_svgs.append(
                automaton_to_svg(automaton, name=name)
            )

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as defs_tmp:
            defs_tmp.write(def_content)
            path_defs = defs_tmp.name
            
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as testes_tmp:
            testes_tmp.write(test_content)
            path_testes = testes_tmp.name
            
        analisador = AnalisadorLexo(path_defs)
        tabela_tokens = analisador.get_tabela_tokens(path_testes)

    return render_template(
        "index.html",
        tabela_tokens=tabela_tokens,
        automata_svgs=automata_svgs
    )

def parse_definitions_text(content):
    definitions = []
    
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        
        partes = line.split(":", 1)
        name = partes[0].strip()
        regex = partes[1].strip()
        definitions.append((name, regex))
        
    return definitions
 
def automaton_to_svg(automaton, name=""):
    dot = Digraph()

    dot.attr(rankdir="LR")
    dot.attr(label=name)
    dot.attr(fontsize="16")

    dot.node("start", shape="none")
    estado_inicial = [x for x in automaton.estados.keys() if automaton.estados[x].inicial][0]
    dot.edge("start", estado_inicial)

    for state_name, state in automaton.estados.items():
        shape = "doublecircle" if state.final else "circle"
        dot.node(state_name, state_name, shape=shape)

    for t in automaton.get_TODAS_transicoes():
        dot.edge(t.estado_origem.nome, t.estado_destino.nome, label=t.simbolo)

    return dot.pipe(format="svg").decode("utf-8")

if __name__ == "__main__":
    app.run(debug=True)
