# Formais Trabalho 1

Projeto da disciplina de Linguagens Formais e Compiladores para implementacao de um gerador de analisadores lexicos.

O trabalho consiste em ler definicoes regulares, construir automatos finitos, gerar uma tabela de analise lexica e executar essa tabela sobre textos de entrada para produzir uma lista de tokens.

## Documentacao

- [Documentacao do trabalho](docs/trabalho.md)
- Enunciado original: `Trabalho-Parte1-GAL.pdf`

## Escopo

O framework deve contemplar:

- Conversao de expressoes regulares para automatos finitos.
- Minimizacao de automatos.
- Uniao de automatos com transicoes epsilon.
- Determinizacao de automatos.
- Visualizacao dos automatos e da tabela de analise lexica.
- Execucao do analisador lexico sobre arquivos de teste.
- Geracao de saida no formato `<lexema, padrao>` ou `<lexema, erro!>`.

## Formato das Definicoes Lexicas

```text
id: [a-zA-Z]([a-zA-Z] | [0-9])*
num: [1-9]([0-9])* | 0
```

Operadores esperados:

- `*`: fecho.
- `+`: fecho positivo.
- `?`: zero ou um.
- `|`: ou.
- `&`: epsilon.

## Estrutura Sugerida

```text
.
+-- docs/
|   +-- trabalho.md
+-- src/
|   +-- ...
+-- tests/
|   +-- ...
+-- examples/
|   +-- ...
+-- README.md
+-- Trabalho-Parte1-GAL.pdf
```

## Desenvolvimento

Este repositorio foi preparado para um projeto em Python e, se necessario, uma interface web.

Sugestao inicial para ambiente Python:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Quando houver dependencias, registre-as em `requirements.txt` ou `pyproject.toml`.

## Automatos Finitos

A base inicial do projeto esta em `src/automata`.

Ela contem:

- `State`: representa um estado do automato.
- `Transition`: representa uma transicao entre estados.
- `FiniteAutomaton`: representa um AFD ou AFND simples, com suporte a transicoes epsilon usando `&`.
- `build_dfa_from_regex`: gera um AFD direto a partir da arvore sintatica da expressao regular pelo algoritmo do Aho.

Exemplo de execucao:

```powershell
python -m examples.simple_automaton
python -m examples.build_dfa
```

## Parser de Expressoes Regulares

A parte de entrada e parser das definicoes lexicas esta em `src/regex_parser`.

Ela le arquivos no formato:

```text
id: [a-zA-Z]([a-zA-Z] | [0-9])*
num: [1-9]([0-9])* | 0
```

E transforma cada linha em uma `RegexDefinition`, contendo:

- `name`: nome do padrao.
- `expression`: expressao regular original.
- `tokens`: lista simples de tokens internos da expressao.
- `root`: arvore sintatica da expressao regular.
- `positions`: simbolos associados as posicoes da arvore.
- `followpos`: relacao calculada para a construcao do AFD pelo algoritmo do Aho.

A concatenacao e implicita no arquivo de entrada, mas o parser insere um token interno `CONCAT` para montar a arvore.

O gerador de AFD acrescenta internamente o marcador final `#`, usa `firstpos` como estado inicial e cria as transicoes a partir de `followpos`.

Exemplo de execucao:

```powershell
python -m examples.parse_definitions
```

## Testes

Os exemplos de teste devem cobrir diferentes definicoes lexicas e entradas validas e invalidas. A avaliacao considera tanto a corretude dos algoritmos quanto a organizacao e legibilidade do codigo.

Para rodar os testes atuais:

```powershell
python -m unittest discover -s tests
```

Para rodar com saida detalhada, mostrando cada teste e seu resultado:

```powershell
python scripts/run_tests.py
```
