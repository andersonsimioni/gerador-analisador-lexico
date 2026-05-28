# Divisao de Atividades

## Pessoa 1

Parte: Entrada, parser de Expressoes Regulares e base de automatos

Responsabilidade principal:

- Ler o arquivo de definicoes lexicas.
- Transformar cada expressao regular em uma estrutura interna.
- Construir a base comum de automatos finitos.
- Definir as estruturas de estado, transicao e automato.
- Garantir suporte inicial a AFD, AFND e transicao epsilon `&`.

## Pessoa 2

Parte: Geracao dos automatos

Responsabilidade principal:

- Converter cada expressao regular em automato.
- Seguir o algoritmo pedido no enunciado do trabalho.

## Pessoa 3

Parte: Operacoes sobre automatos

Responsabilidade principal:

- Fazer minimizacao.
- Fazer uniao com transicao `&`.
- Fazer determinizacao.

## Pessoa 4

Parte: Analisador lexico, saida e testes

Responsabilidade principal:

- Usar a tabela final para analisar textos de entrada.
- Gerar os tokens encontrados.
- Gerar erros lexicos quando a entrada nao for valida.
