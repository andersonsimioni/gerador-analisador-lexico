from flask import Flask, render_template, request
from src.automata import build_dfa_from_regex
from src.regex_parser import parse_definitions_text
from graphviz import Digraph

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result = []
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

        for definition in definitions:
            automaton = build_dfa_from_regex(definition)
            automata.append((definition.name, automaton))

        for name, automaton in automata:
            automata_svgs.append(
                automaton_to_svg(automaton, name=name)
            )

        main_automaton = automata[0][1] if automata else None

        for text in test_content.splitlines():
            text = text.strip()
            if not text:
                continue

            result.append(
                (text, "accepted" if main_automaton.accepts(text) else "rejected")
            )

    return render_template(
        "index.html",
        result=result,
        automata_svgs=automata_svgs
    )
 
def automaton_to_svg(automaton, name=""):
    dot = Digraph()

    dot.attr(rankdir="LR")
    dot.attr(label=name)
    dot.attr(fontsize="16")

    dot.node("start", shape="none")
    dot.edge("start", automaton.initial_state)

    for state_name, state in automaton.states.items():
        shape = "doublecircle" if state.is_final else "circle"
        dot.node(state_name, state_name, shape=shape)

    for t in automaton.transitions:
        dot.edge(t.source, t.target, label=t.symbol)

    return dot.pipe(format="svg").decode("utf-8")

if __name__ == "__main__":
    app.run(debug=True)