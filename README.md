# Gerador de Analisadores Lexicos e Sintaticos SLR

Projeto da disciplina de Linguagens Formais e Compiladores.

O sistema implementa um gerador de analisadores lexicos a partir de definicoes regulares
e um gerador de analisadores sintaticos do tipo SLR a partir de uma Gramatica Livre de
Contexto. As duas partes podem ser testadas separadamente ou em um fluxo completo pela
interface web.

## O que o projeto faz

- Le definicoes regulares no formato `nome: expressao_regular`.
- Converte cada expressao regular em automato finito pelo algoritmo direto do Aho.
- Une os automatos usando transicoes epsilon.
- Determiniza e minimiza automatos.
- Mostra automatos e tabela de analise lexica na interface web.
- Gera lista de tokens a partir de um arquivo de palavras.
- Trata palavras reservadas pela tabela de simbolos.
- Calcula FIRST e FOLLOW de uma GLC.
- Calcula closure, colecao canonica LR(0), tabela SLR e GOTO.
- Executa a analise sintatica e informa se a lista de tokens foi aceita pela gramatica.

## Estrutura do projeto

```text
.
|-- analisador_lexico/
|   `-- analisador_lexico.py
|-- analisador_sintatico/
|   |-- analisador_sintatico.py
|   |-- gramatica_livre.py
|   |-- producao.py
|   |-- prod_item_LR0.py
|   `-- simbolo_producao.py
|-- arvore_sintax/
|   |-- arvore_sintax.py
|   |-- no_arvore_sintax.py
|   `-- parte_regex.py
|-- automato/
|   |-- automato.py
|   |-- estado.py
|   |-- transicao.py
|   `-- unificador_de_automato.py
|-- docs/
|   |-- Trabalho-Parte1-GAL.pdf
|   `-- Tra_Sintatico.pdf
|-- exemplos/
|-- testes_unitarios/
|-- web/
|-- main.py
`-- README.md
```

## Como executar

### 1. Instalar dependencias

O projeto usa Python. Para a interface web e visualizacao dos automatos, instale:

```powershell
python -m pip install flask graphviz
```

Tambem e necessario ter o Graphviz instalado no sistema para renderizar os automatos.
No Windows, uma opcao e:

```powershell
choco install graphviz -y
```

Se o Graphviz ja estiver instalado, basta garantir que o comando `dot` esteja no `PATH`.

### 2. Iniciar a interface web

Na raiz do projeto, execute:

```powershell
python main.py
```

O navegador sera aberto automaticamente em:

```text
http://127.0.0.1:5000/
```

## Como usar a interface

A interface possui quatro abas principais:

- `Fluxo completo`
- `Analise lexica`
- `GLC FIRST/FOLLOW`
- `Analise sintatica`

### Fluxo completo

Use essa aba para demonstrar o trabalho integrado.

Arquivos recomendados:

```text
Definicoes regulares: exemplos/1/lexico_defs.txt
Palavras de entrada:  exemplos/1/lexico_valido.txt
GLC:                  exemplos/1/sintatico_glc.txt
Palavras reservadas:  exemplos/1/lexico_reservadas.txt
```

O programa ira:

1. gerar automatos para as definicoes regulares;
2. unir, determinizar e minimizar os automatos;
3. gerar a tabela de analise lexica;
4. gerar a tabela de simbolos;
5. gerar a lista de tokens;
6. usar esses tokens na analise sintatica;
7. informar se a entrada foi aceita ou rejeitada pela gramatica.

### Analise lexica

Use para testar somente o analisador lexico.

Arquivos recomendados:

```text
Definicoes regulares: exemplos/1/lexico_defs.txt
Palavras de entrada:  exemplos/1/lexico_valido.txt
Palavras reservadas:  exemplos/1/lexico_reservadas.txt
```

Para testar erro lexico:

```text
Palavras de entrada: exemplos/1/lexico_invalido.txt
```

Para uma massa maior:

```text
Palavras de entrada: exemplos/1/lexico_misto.txt
```

### GLC FIRST/FOLLOW

Use para testar somente os conjuntos FIRST e FOLLOW da gramatica.

Arquivo recomendado:

```text
GLC: exemplos/1/sintatico_glc.txt
```

### Analise sintatica

Use para testar somente a parte sintatica.

Caso valido:

```text
GLC:    exemplos/1/sintatico_glc.txt
Tokens: exemplos/1/sintatico_tokens_valido.txt
```

Caso invalido:

```text
GLC:    exemplos/1/sintatico_glc.txt
Tokens: exemplos/1/sintatico_tokens_invalido.txt
```

## Formato dos arquivos

### Definicoes regulares

Cada linha possui uma classe e uma expressao regular:

```text
id: [a-zA-Z]([a-zA-Z] | [0-9])*
num: [1-9]([0-9])* | 0
op_plus: \+
```

Espacos internos nas expressoes sao aceitos.

Operadores suportados:

- `*`: fecho de Kleene.
- `+`: fecho positivo.
- `?`: opcional.
- `|`: uniao.
- `&`: epsilon.
- `[a-z]`, `[A-Z]`, `[0-9]`: grupos/faixas.
- `\`: escape para literais, como `\+`, `\*`, `\(`.

### Palavras de entrada

O arquivo de palavras simula um programa fonte separado por linhas:

```text
x
+
12
*
(
y
+
0xff
)
```

### Palavras reservadas

O arquivo pode ser uma lista simples:

```text
if
else
while
true
false
```

Nesse caso, cada palavra recebe a classe `PR`.

Tambem e possivel informar a classe explicitamente:

```text
true:bool
false:bool
```

### Saida lexica

Palavras reservadas:

```text
<if,PR>
```

Identificadores:

```text
<id,6>
```

Nesse caso, `6` e a linha da tabela de simbolos onde o lexema foi armazenado.

Outros tokens:

```text
<12,num>
<+,op_plus>
<0xff,hex>
```

Erro lexico:

```text
<lexema,erro!>
```

### Gramaticas livres de contexto

Cada producao deve ficar em uma linha:

```text
Programa ::= Expressao
Expressao ::= Expressao op_plus Termo
Expressao ::= Termo
Termo ::= Termo op_star Fator
Termo ::= Fator
Fator ::= lparen Expressao rparen
Fator ::= id
```

### Lista de tokens para analise sintatica

Pode vir no formato gerado pelo lexico:

```text
<id,6>
<+,op_plus>
<12,num>
```

O analisador sintatico interpreta `<id,6>` como token `id`.

## Exemplos disponiveis

Os exemplos ficam separados em suites numeradas de `1` a `10`.
Todas as pastas possuem os mesmos nomes de arquivos, mudando apenas os casos de teste.

Para a demonstracao principal, use a suite `1`:

```text
exemplos/1/lexico_defs.txt
exemplos/1/lexico_reservadas.txt
exemplos/1/lexico_valido.txt
exemplos/1/lexico_invalido.txt
exemplos/1/lexico_sintatico_invalido.txt
exemplos/1/lexico_misto.txt
exemplos/1/sintatico_glc.txt
exemplos/1/sintatico_tokens_valido.txt
exemplos/1/sintatico_tokens_invalido.txt
```

Para testar outros cenarios, troque apenas o numero da pasta:

```text
exemplos/2/...
exemplos/3/...
...
exemplos/10/...
```

## Testes

Os testes ficam em `testes_unitarios/`.

Para rodar um teste especifico:

```powershell
python -X utf8 testes_unitarios\test_analisador_lexo_IA.py
python -X utf8 testes_unitarios\test_analisador_sintatico_IA.py
```

Para rodar todos os testes manualmente no PowerShell:

```powershell
$tests = Get-ChildItem testes_unitarios -Filter *.py | Sort-Object Name
$failed = @()
foreach ($test in $tests) {
    Write-Host "== $($test.Name) =="
    $env:PYTHONDONTWRITEBYTECODE='1'
    python -X utf8 $test.FullName
    if ($LASTEXITCODE -ne 0) { $failed += $test.Name }
}
if ($failed.Count -eq 0) {
    Write-Host "TODOS PASSARAM"
} else {
    Write-Host "FALHARAM:"
    $failed | ForEach-Object { Write-Host $_ }
    exit 1
}
```

Observacao: o teste lexico possui uma bateria pesada para validar expressoes regulares
com espacos internos. Ele pode demorar mais que os demais.

## Roteiro sugerido para apresentacao

1. Abrir a interface com `python main.py`.
2. Mostrar a aba `Analise lexica` com `lexico_defs.txt`, `lexico_valido.txt` e `lexico_reservadas.txt`.
3. Mostrar a tabela de simbolos e explicar `PR` e `<id,N>`.
4. Mostrar os automatos e a tabela de analise lexica.
5. Mostrar a aba `GLC FIRST/FOLLOW` com `sintatico_glc.txt`.
6. Mostrar a aba `Analise sintatica` com tokens validos e invalidos.
7. Finalizar com a aba `Fluxo completo`, usando os arquivos recomendados.

## Observacoes importantes

- O simbolo de epsilon usado no projeto e `&`.
- Palavras reservadas sem classe explicita viram `PR`.
- Identificadores novos sao armazenados na tabela de simbolos.
- A interface foi feita para permitir testar as partes separadas, como pedido no enunciado.
- Os exemplos incluem casos validos, invalidos e um fluxo completo integrado.

