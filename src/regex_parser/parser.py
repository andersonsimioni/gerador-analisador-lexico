from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RegexPart:
    kind: str
    value: str


@dataclass(frozen=True)
class RegexNode:
    kind: str
    value: str = ""
    left: "RegexNode | None" = None
    right: "RegexNode | None" = None
    position: int | None = None
    nullable: bool = False
    firstpos: frozenset[int] = frozenset()
    lastpos: frozenset[int] = frozenset()


@dataclass(frozen=True)
class RegexDefinition:
    name: str
    expression: str
    parts: list[RegexPart]
    root: RegexNode
    positions: dict[int, str]
    followpos: dict[int, set[int]]


OPERATORS = {
    "(": "LPAREN",
    ")": "RPAREN",
    "|": "UNION",
    "*": "STAR",
    "+": "PLUS",
    "?": "OPTIONAL",
    "&": "EPSILON",
}


def parse_definitions_file(path: str | Path) -> list[RegexDefinition]:
    return parse_definitions_text(Path(path).read_text(encoding="utf-8"))


def parse_definitions_text(text: str) -> list[RegexDefinition]:
    definitions: list[RegexDefinition] = []

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        name, expression = _split_definition(line, line_number)
        parts = _add_concat_parts(tokenize_expression(expression, line_number))
        root, positions, followpos = build_syntax_tree(parts, line_number)
        definitions.append(
            RegexDefinition(
                name=name,
                expression=expression,
                parts=parts,
                root=root,
                positions=positions,
                followpos=followpos,
            )
        )

    return definitions


def tokenize_expression(expression: str, line_number: int = 1) -> list[RegexPart]:
    parts: list[RegexPart] = []
    index = 0

    while index < len(expression):
        char = expression[index]

        if char.isspace():
            index += 1
            continue

        if char == "[":
            value, index = _read_char_class(expression, index, line_number)
            parts.append(RegexPart("CHAR_CLASS", value))
            continue

        if char == "\\":
            if index + 1 >= len(expression):
                raise ValueError(f"Line {line_number}: incomplete escape.")
            parts.append(RegexPart("LITERAL", expression[index + 1]))
            index += 2
            continue

        if char in OPERATORS:
            parts.append(RegexPart(OPERATORS[char], char))
            index += 1
            continue

        parts.append(RegexPart("LITERAL", char))
        index += 1

    return parts


def build_syntax_tree(
    parts: list[RegexPart],
    line_number: int = 1,
) -> tuple[RegexNode, dict[int, str], dict[int, set[int]]]:
    parser = _SyntaxTreeParser(parts, line_number)
    root = parser.parse()
    followpos = {position: set() for position in parser.positions}
    root = _annotate(root, followpos)
    return root, parser.positions, followpos


def with_end_marker(definition: RegexDefinition, marker: str = "#") -> RegexDefinition:
    positions = dict(definition.positions)
    marker_position = max(positions, default=0) + 1
    positions[marker_position] = marker

    root = RegexNode(
        "CONCAT",
        left=definition.root,
        right=RegexNode("LITERAL", marker, position=marker_position),
    )
    followpos = {position: set() for position in positions}
    root = _annotate(root, followpos)

    return RegexDefinition(
        name=definition.name,
        expression=f"({definition.expression}){marker}",
        parts=definition.parts + [RegexPart("CONCAT", ""), RegexPart("LITERAL", marker)],
        root=root,
        positions=positions,
        followpos=followpos,
    )


def _split_definition(line: str, line_number: int) -> tuple[str, str]:
    if ":" not in line:
        raise ValueError(f"Line {line_number}: definition missing ':'.")

    name, expression = line.split(":", 1)
    name = name.strip()
    expression = expression.strip()

    if not name:
        raise ValueError(f"Line {line_number}: empty definition name.")
    if not expression:
        raise ValueError(f"Line {line_number}: empty regular expression.")

    return name, expression


def _read_char_class(expression: str, start: int, line_number: int) -> tuple[str, int]:
    end = expression.find("]", start + 1)
    if end == -1:
        raise ValueError(f"Line {line_number}: '[' group missing closing ']'.")
    if end == start + 1:
        raise ValueError(f"Line {line_number}: empty character group.")

    return expression[start : end + 1], end + 1


def _add_concat_parts(parts: list[RegexPart]) -> list[RegexPart]:
    if not parts:
        return []

    result = [parts[0]]
    for previous, current in zip(parts, parts[1:]):
        if _needs_concat(previous, current):
            result.append(RegexPart("CONCAT", ""))
        result.append(current)

    return result


def _needs_concat(previous: RegexPart, current: RegexPart) -> bool:
    left = previous.kind in {"LITERAL", "CHAR_CLASS", "EPSILON", "RPAREN", "STAR", "PLUS", "OPTIONAL"}
    right = current.kind in {"LITERAL", "CHAR_CLASS", "EPSILON", "LPAREN"}
    return left and right


"""_summary_
SYNTAX TREE PARSER RULES:
The parser uses recursive descent.
Each method handles one precedence level.

PRECEDENCE, FROM LOWEST TO HIGHEST:
1. UNION:       A | B
2. CONCAT:      AB, inserted internally as CONCAT
3. POSTFIX:     A*, A+, A?
4. ATOM:        a, [a-z], &, (A)

METHODS:
parse:          starts parsing and checks if no part is left
_parse_union:   handles |
_parse_concat:  handles internal CONCAT
_parse_postfix: handles *, + and ?
_parse_atom:    handles literals, char classes, epsilon and parentheses

PARENTHESES:
Parentheses do not become tree nodes.
They only force a subexpression to be parsed first.
"""
class _SyntaxTreeParser:
    def __init__(self, parts: list[RegexPart], line_number: int) -> None:
        self.parts = parts
        self.line_number = line_number
        self.index = 0
        self.next_position = 1
        self.positions: dict[int, str] = {}

    def parse(self) -> RegexNode:
        if not self.parts:
            raise ValueError(f"Line {self.line_number}: empty regular expression.")

        root = self._parse_union()
        if self._current() is not None:
            part = self._current()
            raise ValueError(f"Line {self.line_number}: unexpected regex part '{part.value}'.")
        return root

    def _parse_union(self) -> RegexNode:
        node = self._parse_concat()
        while self._accept("UNION"):
            node = RegexNode("UNION", "|", left=node, right=self._parse_concat())
        return node

    def _parse_concat(self) -> RegexNode:
        node = self._parse_postfix()
        while self._accept("CONCAT"):
            node = RegexNode("CONCAT", left=node, right=self._parse_postfix())
        return node

    def _parse_postfix(self) -> RegexNode:
        node = self._parse_atom()

        while True:
            if self._accept("STAR"):
                node = RegexNode("STAR", "*", left=node)
            elif self._accept("PLUS"):
                node = RegexNode("PLUS", "+", left=node)
            elif self._accept("OPTIONAL"):
                node = RegexNode("OPTIONAL", "?", left=node)
            else:
                return node

    def _parse_atom(self) -> RegexNode:
        part = self._current()
        if part is None:
            raise ValueError(f"Line {self.line_number}: incomplete expression.")

        if self._accept("LPAREN"):
            node = self._parse_union()
            if not self._accept("RPAREN"):
                raise ValueError(f"Line {self.line_number}: missing closing parenthesis.")
            return node

        if part.kind in {"LITERAL", "CHAR_CLASS"}:
            self.index += 1
            position = self.next_position
            self.next_position += 1
            self.positions[position] = part.value
            return RegexNode(part.kind, part.value, position=position)

        if part.kind == "EPSILON":
            self.index += 1
            return RegexNode("EPSILON", part.value)

        raise ValueError(f"Line {self.line_number}: unexpected regex part '{part.value}'.")

    def _accept(self, kind: str) -> bool:
        part = self._current()
        if part is not None and part.kind == kind:
            self.index += 1
            return True
        return False

    def _current(self) -> RegexPart | None:
        if self.index >= len(self.parts):
            return None
        return self.parts[self.index]


"""_summary_
FIRST/LAST/NULLABLE RULES:
LEAF:
    nullable = False
    firstpos = {position}
    lastpos = {position}

EPSILON:
    nullable = True
    firstpos = {}
    lastpos = {}

UNION:
    nullable = nullable(left) or nullable(right)
    firstpos = firstpos(left) union firstpos(right)
    lastpos = lastpos(left) union lastpos(right)

CONCAT:
    nullable = nullable(left) and nullable(right)
    firstpos = firstpos(left) union firstpos(right), if nullable(left)
    firstpos = firstpos(left), otherwise
    lastpos = lastpos(left) union lastpos(right), if nullable(right)
    lastpos = lastpos(right), otherwise

STAR:
    nullable = True
    firstpos = firstpos(child)
    lastpos = lastpos(child)

PLUS:
    nullable = nullable(child)
    firstpos = firstpos(child)
    lastpos = lastpos(child)

OPTIONAL:
    nullable = True
    firstpos = firstpos(child)
    lastpos = lastpos(child)


--------------
FOLLOW RULES: 
    CONCAT: followpos[lastpos(left)] += firstpos(right)
    STAR:   followpos[lastpos(child)] += firstpos(child)
    PLUS:   followpos[lastpos(child)] += firstpos(child)
"""
def _annotate(node: RegexNode, followpos: dict[int, set[int]]) -> RegexNode:
    if node.kind in {"LITERAL", "CHAR_CLASS"}:
        assert node.position is not None
        position_set = frozenset({node.position})
        return RegexNode(
            kind=node.kind,
            value=node.value,
            position=node.position,
            nullable=False,
            firstpos=position_set,
            lastpos=position_set,
        )

    if node.kind == "EPSILON":
        return RegexNode(kind=node.kind, value=node.value, nullable=True)

    if node.kind in {"STAR", "PLUS", "OPTIONAL"}:
        child = _annotate(_required(node.left), followpos)
        if node.kind in {"STAR", "PLUS"}:
            for position in child.lastpos:
                followpos[position].update(child.firstpos)
        return RegexNode(
            kind=node.kind,
            value=node.value,
            left=child,
            nullable=node.kind != "PLUS" or child.nullable,
            firstpos=child.firstpos,
            lastpos=child.lastpos,
        )

    left = _annotate(_required(node.left), followpos)
    right = _annotate(_required(node.right), followpos)

    if node.kind == "UNION":
        return RegexNode(
            kind=node.kind,
            value=node.value,
            left=left,
            right=right,
            nullable=left.nullable or right.nullable,
            firstpos=left.firstpos | right.firstpos,
            lastpos=left.lastpos | right.lastpos,
        )

    if node.kind == "CONCAT":
        for position in left.lastpos:
            followpos[position].update(right.firstpos)
        return RegexNode(
            kind=node.kind,
            value=node.value,
            left=left,
            right=right,
            nullable=left.nullable and right.nullable,
            firstpos=left.firstpos | right.firstpos if left.nullable else left.firstpos,
            lastpos=left.lastpos | right.lastpos if right.nullable else right.lastpos,
        )

    raise ValueError(f"Unknown node type: {node.kind}")


def _required(node: RegexNode | None) -> RegexNode:
    if node is None:
        raise ValueError("Invalid syntax tree.")
    return node
