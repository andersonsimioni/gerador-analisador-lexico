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
from automato.unificador_de_automato import Unificador_de_automato
from analisador_lexico import AnalisadorLexo
from gramatica_livre import GramaticaLivreDeContexto
from analisador_sintatico import AnalisadorSintatico


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

DEFAULT_SYNTACTIC_GRAMMAR = """E ::= E op_plus T
E ::= T
T ::= T op_times F
T ::= F
F ::= lparen E rparen
F ::= id"""

DEFAULT_SYNTACTIC_TOKENS = """<x,id>
<+,op_plus>
<y,id>
<*,op_times>
<z,id>"""


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
            # Tabela léxica implícita do AFD
            "tabela_lexica": None,  # {"alfabeto": [...], "linhas": [...]}
        },
        "first_follow": {
            "grammar": DEFAULT_GRAMMAR,
            "firsts": {},
            "follows": {},
        },
        "sintatico": {
            "grammar": DEFAULT_SYNTACTIC_GRAMMAR,
            "tokens_text": DEFAULT_SYNTACTIC_TOKENS,
            "tokens": [],
            "accepted": None,
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
        data["sintatico"]["tokens_text"] = request.form.get("sintatico_tokens", "")


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
    lista_de_automatos = []

    for name, regex in parsed_definitions:
        automaton = Automato.parse_regex(regex)
        lista_de_automatos.append(automaton)
        automata_svgs.append(automaton_to_svg(automaton, name=name))

    tabela_lexica = None

    if len(lista_de_automatos) > 0:
        # União dos autômatos (AFND)
        automato_unificado = Unificador_de_automato.uniao_de_automato(lista_de_automatos)
        svg_uniao = automaton_to_svg(automato_unificado, name="União dos automatos")
        automata_svgs.append(svg_uniao)

        # Determinização → AFD
        automato_determinizado = automato_unificado.determinization(automato_unificado)
        svg_afd = automaton_to_svg(automato_determinizado, name="Autômato Determinizado (AFD)")
        automata_svgs.append(svg_afd)

        # ── NOVO: Tabela de análise léxica (representação implícita do AFD) ──
        tabela_lexica = gerar_tabela_lexica(automato_determinizado)

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
        "tabela_lexica": tabela_lexica,
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
    tokens_text = require_content(
        get_required_file("sintatico_tokens_file", "Escolha o arquivo com a lista de tokens antes de executar a analise sintatica."),
        "O arquivo de tokens esta vazio.",
    )
    tokens = parse_tokens_text(tokens_text)
    grammar = GramaticaLivreDeContexto(grammar_text)
    sintatico = AnalisadorSintatico(grammar)
    action_table, goto_table = grammar.GLC_exntedida.tabela_SLR

    return {
        "grammar": grammar_text,
        "tokens_text": tokens_text,
        "tokens": tokens,
        "accepted": sintatico.aceita(tokens),
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


def parse_tokens_text(content):
    tokens = []

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("<") and line.endswith(">"):
            tokens.append(parse_token(line))
            continue

        for token in line.split():
            tokens.append(parse_token(token))

    if not tokens:
        raise ValueError("A lista de tokens esta vazia.")

    if "erro!" in tokens:
        raise ValueError("A lista de tokens contem erro lexico. Corrija a analise lexica antes de executar a analise sintatica.")

    return tokens


def parse_token(token):
    if token.startswith("<") and token.endswith(">") and "," in token:
        token = token[1:-1]
        return token.split(",")[-1].strip()

    return token.strip()


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


def gerar_tabela_lexica(afd):
    """
    Gera a tabela de análise léxica (representação implícita do AFD).

    Retorna um dicionário com:
      - "alfabeto": lista ordenada de todos os símbolos de entrada (colunas)
      - "linhas": lista de dicts com "estado" (rótulo) e "transicoes" (dict símbolo→destino ou "-")
    """
    # 1. Coleta o alfabeto completo (todas as transições, exceto épsilon)
    alfabeto = set()
    for estado in afd.estados.values():
        for simbolo in estado.transicoes.keys():
            if simbolo not in ("&", "ε", definicoes_EPISLON()):
                alfabeto.add(simbolo)
    alfabeto = sorted(list(alfabeto))

    linhas = []

    # 2. Monta uma linha por estado
    for nome_estado in sorted(afd.estados.keys()):
        estado = afd.estados[nome_estado]

        # Prefixos clássicos: -> para inicial, * para final
        prefixo = ""
        if estado.inicial:
            prefixo += "-> "
        if estado.final:
            prefixo += "* "

        linha = {
            "estado": f"{prefixo}{nome_estado}",
            "final": estado.final,
            "inicial": estado.inicial,
            "transicoes": {},
        }

        # 3. Preenche cada célula com o estado destino ou "-" (erro)
        for simb in alfabeto:
            destinos = estado.transicoes.get(simb, [])
            if destinos:
                # AFD: sempre um único destino; join como salvaguarda
                linha["transicoes"][simb] = ", ".join(
                    t.estado_destino.nome for t in destinos
                )
            else:
                linha["transicoes"][simb] = "-"

        linhas.append(linha)

    return {
        "alfabeto": alfabeto,
        "linhas": linhas,
    }


def definicoes_EPISLON():
    """Retorna o símbolo de épsilon definido em definicoes.py sem importar o módulo aqui."""
    try:
        import definicoes
        return definicoes.EPISLON
    except Exception:
        return "&"


if __name__ == "__main__":
    app.run(debug=True)
