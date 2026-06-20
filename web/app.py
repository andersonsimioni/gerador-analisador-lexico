from flask import Flask, render_template, request
from src.automata import build_dfa_from_regex
from src.regex_parser import parse_definitions_text

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result = []

    if request.method == "POST":

        def_file = request.files.get("definitions")
        def_content = def_file.read().decode("utf-8")

        definitions = parse_definitions_text(def_content)

        definition = definitions[0]
        automaton = build_dfa_from_regex(definition)

        test_file = request.files.get("tests")
        test_content = test_file.read().decode("utf-8")

        tests = test_content.splitlines()

        for t in tests:
            t = t.strip()
            if not t:
                continue

            status = "accepted" if automaton.accepts(t) else "rejected"
            result.append((t, status))

    return render_template("index.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)