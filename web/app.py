from flask import Flask, render_template, request
from graphviz import Digraph
from pathlib import Path
import sys
import tempfile


BASE_DIR = Path(__file__).resolve().parent.parent
AUTOMATO_DIR = BASE_DIR / "automato"
ANALISADOR_LEXICO_DIR = BASE_DIR / "analisador_lexico"
ANALISADOR_SINTATICO_DIR = BASE_DIR / "analisador_sintatico"

sys.path.insert(0, str(BASE_DIR))
sys.path.append(str(AUTOMATO_DIR))
sys.path.append(str(ANALISADOR_LEXICO_DIR))
sys.path.append(str(ANALISADOR_SINTATICO_DIR))

from automato.automato import Automato
from analisador_lexico import AnalisadorLexo
from gramatica_livre import GramaticaLivreDeContexto


app = Flask(__name__)


DEFAULT_DEFINITIONS = """id: [a-zA-Z][a-zA-Z0-9]*
num: [0-9][0-9]*
op_plus: \\+
op_times: \\*
lparen: \\(
rparen: \\)"""

DEFAULT_WORDS = """id
abc123
42
+
*
("""

DEFAULT_GRAMMAR = """E ::= E + T
E ::= T
T ::= T * F
T ::= F
F ::= ( E )
F ::= id"""


@app.route("/", methods=["GET", "POST"])
def index():
    active_tab = request.form.get("tab", "lexico")
    data = build_empty_data(active_tab)

    if request.method == "POST":
        try:
            if active_tab == "lexico":
                data["lexico"] = run_lexical_analysis(request)
            elif active_tab == "first_follow":
                data["first_follow"] = run_first_follow(request)
            elif active_tab == "sintatico":
                data["sintatico"] = run_syntactic_analysis(request)
        except Exception as exc:
            data["error"] = str(exc)
            keep_submitted_values(data, active_tab)

    return render_template("index.html", **data)


def build_empty_data(active_tab):
    return {
        "active_tab": active_tab,
        "error": "",
        "defaults": {
            "definitions": DEFAULT_DEFINITIONS,
            "words": DEFAULT_WORDS,
            "grammar": DEFAULT_GRAMMAR,
        },
        "lexico": {
            "definitions": DEFAULT_DEFINITIONS,
            "words": DEFAULT_WORDS,
            "tokens": "",
            "automata_svgs": [],
        },
        "first_follow": {
            "grammar": DEFAULT_GRAMMAR,
            "firsts": {},
            "follows": {},
        },
        "sintatico": {
            "grammar": DEFAULT_GRAMMAR,
            "items": [],
            "gotos": [],
            "action_table": {},
            "goto_table": {},
        },
    }


def keep_submitted_values(data, active_tab):
    if active_tab == "lexico":
        data["lexico"]["definitions"] = request.form.get("definitions_text", "")
        data["lexico"]["words"] = request.form.get("words_text", "")
    elif active_tab == "first_follow":
        data["first_follow"]["grammar"] = request.form.get("first_follow_grammar", "")
    elif active_tab == "sintatico":
        data["sintatico"]["grammar"] = request.form.get("sintatico_grammar", "")


def get_text_or_file(field_name, file_name, default=""):
    uploaded_file = request.files.get(file_name)
    if uploaded_file and uploaded_file.filename:
        return uploaded_file.read().decode("utf-8")
    return request.form.get(field_name, default)


def get_required_file(file_name, message):
    uploaded_file = request.files.get(file_name)
    if not uploaded_file or not uploaded_file.filename:
        raise ValueError(message)
    return uploaded_file.read().decode("utf-8")


def require_content(value, message):
    if not value or not value.strip():
        raise ValueError(message)
    return value


def run_lexical_analysis(req):
    definitions = require_content(
        get_required_file("definitions_file", "Escolha o arquivo de definicoes regulares antes de executar a analise lexica."),
        "O arquivo de definicoes regulares esta vazio.",
    )
    words = require_content(
        get_required_file("words_file", "Escolha o arquivo de palavras de teste antes de executar a analise lexica."),
        "O arquivo de palavras de teste esta vazio.",
    )

    parsed_definitions = parse_definitions_text(definitions)
    automata_svgs = []

    for name, regex in parsed_definitions:
        automaton = Automato.parse_regex(regex)
        automata_svgs.append(automaton_to_svg(automaton, name=name))

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as defs_tmp:
        defs_tmp.write(definitions)
        defs_path = defs_tmp.name

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as words_tmp:
        words_tmp.write(words)
        words_path = words_tmp.name

    analyzer = AnalisadorLexo(defs_path)

    return {
        "definitions": definitions,
        "words": words,
        "tokens": analyzer.get_tabela_tokens(words_path),
        "automata_svgs": automata_svgs,
    }


def run_first_follow(req):
    grammar_text = require_content(
        get_required_file("first_follow_file", "Escolha o arquivo da GLC antes de calcular FIRST/FOLLOW."),
        "O arquivo da GLC esta vazio.",
    )
    grammar = GramaticaLivreDeContexto(grammar_text)

    return {
        "grammar": grammar_text,
        "firsts": sort_sets(grammar.firsts),
        "follows": sort_sets(grammar.follows),
    }


def run_syntactic_analysis(req):
    grammar_text = require_content(
        get_required_file("sintatico_file", "Escolha o arquivo da GLC antes de gerar a analise sintatica."),
        "O arquivo da GLC esta vazio.",
    )
    grammar = GramaticaLivreDeContexto(grammar_text)
    action_table, goto_table = grammar.GLC_exntedida.tabela_SLR

    return {
        "grammar": grammar_text,
        "items": format_lr0_items(grammar.get_itens_LR0()),
        "gotos": format_gotos(grammar.get_gotos()),
        "action_table": format_action_table(action_table),
        "goto_table": format_plain_table(goto_table),
    }


def parse_definitions_text(content):
    definitions = []

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        name, regex = line.split(":", 1)
        definitions.append((name.strip(), regex.strip()))

    return definitions


def automaton_to_svg(automaton, name=""):
    dot = Digraph()
    dot.attr(rankdir="LR", label=name, fontsize="16")
    dot.node("start", shape="none")

    initial_state = [x for x in automaton.estados.keys() if automaton.estados[x].inicial][0]
    dot.edge("start", initial_state)

    for state_name, state in automaton.estados.items():
        shape = "doublecircle" if state.final else "circle"
        dot.node(state_name, state_name, shape=shape)

    for transition in automaton.get_TODAS_transicoes():
        dot.edge(
            transition.estado_origem.nome,
            transition.estado_destino.nome,
            label=transition.simbolo,
        )

    return dot.pipe(format="svg").decode("utf-8")


def sort_sets(data):
    return {key: sorted(values) for key, values in sorted(data.items())}


def format_lr0_items(items):
    return [
        {
            "name": f"I{index}",
            "productions": [format_lr0_production(production) for production in item],
        }
        for index, item in enumerate(items)
    ]


def format_lr0_production(production):
    text = str(production)
    text = text.replace("Â·", ".")
    text = text.replace("·", ".")
    return text


def format_gotos(gotos):
    rows = []
    for origin in sorted(gotos.keys()):
        for symbol, target in sorted(gotos[origin].items(), key=lambda item: item[0][0]):
            rows.append({
                "origin": f"I{origin}",
                "symbol": symbol[0],
                "kind": "Terminal" if symbol[1] else "Nao terminal",
                "target": f"I{target}",
            })
    return rows


def format_action_table(action_table):
    formatted = {}
    for state, columns in sorted(action_table.items()):
        formatted[f"I{state}"] = {}
        for symbol, action in sorted(columns.items()):
            action_type, value = action
            formatted[f"I{state}"][symbol] = action_type if value is None else f"{action_type} {value}"
    return formatted


def format_plain_table(table):
    return {
        f"I{state}": {symbol: f"I{target}" for symbol, target in sorted(columns.items())}
        for state, columns in sorted(table.items())
    }


if __name__ == "__main__":
    app.run(debug=True)
