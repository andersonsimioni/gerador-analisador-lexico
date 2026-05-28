from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RegexToken:
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
    tokens: list[RegexToken]
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
        tokens = _add_concat_tokens(tokenize_expression(expression, line_number))
        root, positions, followpos = build_syntax_tree(tokens, line_number)
        definitions.append(
            RegexDefinition(
                name=name,
                expression=expression,
                tokens=tokens,
                root=root,
                positions=positions,
                followpos=followpos,
            )
        )

    return definitions


def tokenize_expression(expression: str, line_number: int = 1) -> list[RegexToken]:
    tokens: list[RegexToken] = []
    index = 0

    while index < len(expression):
        char = expression[index]

        if char.isspace():
            index += 1
            continue

        if char == "[":
            value, index = _read_char_class(expression, index, line_number)
            tokens.append(RegexToken("CHAR_CLASS", value))
            continue

        if char == "\\":
            if index + 1 >= len(expression):
                raise ValueError(f"Line {line_number}: incomplete escape.")
            tokens.append(RegexToken("LITERAL", expression[index + 1]))
            index += 2
            continue

        if char in OPERATORS:
            tokens.append(RegexToken(OPERATORS[char], char))
            index += 1
            continue

        tokens.append(RegexToken("LITERAL", char))
        index += 1

    return tokens


def build_syntax_tree(
    tokens: list[RegexToken],
    line_number: int = 1,
) -> tuple[RegexNode, dict[int, str], dict[int, set[int]]]:
    parser = _SyntaxTreeParser(tokens, line_number)
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
        tokens=definition.tokens + [RegexToken("CONCAT", ""), RegexToken("LITERAL", marker)],
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


def _add_concat_tokens(tokens: list[RegexToken]) -> list[RegexToken]:
    if not tokens:
        return []

    result = [tokens[0]]
    for previous, current in zip(tokens, tokens[1:]):
        if _needs_concat(previous, current):
            result.append(RegexToken("CONCAT", ""))
        result.append(current)

    return result


def _needs_concat(previous: RegexToken, current: RegexToken) -> bool:
    left = previous.kind in {"LITERAL", "CHAR_CLASS", "EPSILON", "RPAREN", "STAR", "PLUS", "OPTIONAL"}
    right = current.kind in {"LITERAL", "CHAR_CLASS", "EPSILON", "LPAREN"}
    return left and right


class _SyntaxTreeParser:
    def __init__(self, tokens: list[RegexToken], line_number: int) -> None:
        self.tokens = tokens
        self.line_number = line_number
        self.index = 0
        self.next_position = 1
        self.positions: dict[int, str] = {}

    def parse(self) -> RegexNode:
        if not self.tokens:
            raise ValueError(f"Line {self.line_number}: empty regular expression.")

        root = self._parse_union()
        if self._current() is not None:
            token = self._current()
            raise ValueError(f"Line {self.line_number}: unexpected token '{token.value}'.")
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
        token = self._current()
        if token is None:
            raise ValueError(f"Line {self.line_number}: incomplete expression.")

        if self._accept("LPAREN"):
            node = self._parse_union()
            if not self._accept("RPAREN"):
                raise ValueError(f"Line {self.line_number}: missing closing parenthesis.")
            return node

        if token.kind in {"LITERAL", "CHAR_CLASS"}:
            self.index += 1
            position = self.next_position
            self.next_position += 1
            self.positions[position] = token.value
            return RegexNode(token.kind, token.value, position=position)

        if token.kind == "EPSILON":
            self.index += 1
            return RegexNode("EPSILON", token.value)

        raise ValueError(f"Line {self.line_number}: unexpected token '{token.value}'.")

    def _accept(self, kind: str) -> bool:
        token = self._current()
        if token is not None and token.kind == kind:
            self.index += 1
            return True
        return False

    def _current(self) -> RegexToken | None:
        if self.index >= len(self.tokens):
            return None
        return self.tokens[self.index]


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
