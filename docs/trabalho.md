# Trabalho 1: Gerador de Analisadores Lexicos

Disciplina: Linguagens Formais e Compiladores  
Professora: Jerusa Marchi

## Objetivo

O objetivo deste trabalho e desenvolver um arcabouco (framework) para gerar analisadores lexicos.

O framework deve implementar os algoritmos necessarios para criar automatos finitos capazes de atender as definicoes regulares expressas em um arquivo de entrada. A saida esperada e uma lista de tokens, associando cada lexema ao seu padrao.

## Algoritmos Necessarios

Para a construcao do gerador de analisador lexico, devem ser implementados os seguintes algoritmos:

1. Conversao de Expressao Regular para Automato Finito Deterministico, conforme algoritmo apresentado no livro do Aho.
2. Minimizacao de automatos.
3. Uniao de automatos via transicao epsilon.
4. Determinizacao de automatos.

## Interface de Projeto

O framework deve prover uma interface para o projeto de um novo analisador lexico.

Essa interface deve permitir:

- Incluir expressoes regulares para todos os padroes de tokens, usando definicoes regulares.
- Gerar o AFD correspondente para cada expressao regular.
- Minimizar os AFDs gerados.
- Unir os AFDs por meio de transicoes epsilon.
- Determinizar o AFND resultante.
- Gerar a tabela de analise lexica, em representacao implicita.

## Interface de Execucao

O framework tambem deve prover uma interface de execucao para uso do analisador lexico gerado.

Essa interface deve permitir:

- Inserir um texto fonte, isto e, um conjunto de palavras simulando um programa fonte.
- Analisar o texto fonte usando a tabela de analise lexica gerada na etapa de projeto.
- Gerar um arquivo de saida com a lista de tokens encontrados.
- Reportar erro quando uma entrada nao for valida.

O formato da saida deve ser:

```text
<lexema, padrao>
```

Quando houver erro lexico:

```text
<lexema, erro!>
```

## Observacoes

- As notacoes devem seguir as utilizadas em sala.
- Para representar epsilon, deve ser usado o caractere `&`.
- A tabela de analise lexica deve poder ser visualizada.
- Os automatos finitos gerados pela conversao das expressoes regulares tambem devem poder ser visualizados, em arquivo ou tela, na forma de tabela.

## Realizacao

O trabalho deve ser realizado em grupos de no minimo 3 e no maximo 4 integrantes.

Ao final do semestre, os grupos devem apresentar o trabalho em dia e horario agendado, juntamente com o analisador sintatico, de forma integrada.

Durante a apresentacao, serao executados testes das partes em separado. Por isso, e importante que cada parte possa ser testada de forma independente.

O grupo deve entregar:

- Codigo-fonte.
- Executaveis, quando aplicavel.
- Um HowTo ou guia de uso.
- Exemplos variados de testes.
- Diferentes definicoes lexicas para avaliacao do trabalho.

## Avaliacao

O trabalho sera avaliado considerando:

- Robustez dos algoritmos.
- Corretude dos algoritmos.
- Legibilidade do codigo.
- Organizacao dos fontes.
- Qualidade dos exemplos de teste.

## Anexo I: Formato de Entrada de Expressoes Regulares

Os arquivos com expressoes regulares devem seguir o padrao:

```text
def-reg1: ER1
def-reg2: ER2
...
def-regn: ERn
```

As expressoes regulares devem aceitar grupos como:

```text
[a-zA-Z]
[0-9]
```

Tambem devem aceitar os operadores usuais:

- `*`: fecho.
- `+`: fecho positivo.
- `?`: zero ou um.
- `|`: ou.

### Exemplo 1

```text
id: [a-zA-Z]([a-zA-Z] | [0-9])*
num: [1-9]([0-9])* | 0
```

### Exemplo 2

```text
er1: a?(a | b)+
er2: b?(a | b)+
```

## Anexo II: Exemplos de Entrada e Saida

Os arquivos de teste dependem das definicoes regulares introduzidas.

### Exemplo com Identificadores e Numeros

Considerando as definicoes:

```text
id: [a-zA-Z]([a-zA-Z] | [0-9])*
num: [1-9]([0-9])* | 0
```

Entrada:

```text
a1
0
teste2
21
alpha123
3444
a43teste
```

Saida esperada:

```text
<a1, id>
<0, num>
<teste2, id>
<21, num>
<alpha123, id>
<3444, num>
<a43teste, id>
```

### Exemplo com Palavras Iniciadas por `a` ou `b`

Considerando as definicoes:

```text
er1: a?(a | b)+
er2: b?(a | b)+
```

Entrada:

```text
aa
bbbba
ababab
bbbbb
```

Saida esperada:

```text
<aa, er1>
<bbbba, er2>
<ababab, er1>
<bbbbb, er2>
```
