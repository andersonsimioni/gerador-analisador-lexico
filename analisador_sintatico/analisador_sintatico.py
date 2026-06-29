import definicoes

class AnalisadorSintatico:
    
    def __init__(self, GLC):
        self.GLC = GLC
        
    def aceita(self, lista_de_tokens):
        indice_token = 0
        action_table, goto_table = self.GLC.GLC_exntedida.tabela_SLR
        stack = [0] # estados do automato LR por id, 0 = I0
        entrada = list(lista_de_tokens)

        #adiciona fundo de pilha
        if(len(entrada) == 0 or entrada[-1] != "$"): entrada.append("$")
        while(True):
            consome_token = True
            estado_atual = stack[-1]
            token_atual = entrada[indice_token]

            # busca na action table oque acao tomar
            acao = action_table.get(estado_atual, {}).get(token_atual)

            #caso EPISLON, pode ser que seja por epislon
            # pois ele nao aparece como entrada!
            if(acao is None):
                acao = action_table.get(estado_atual, {}).get(definicoes.EPISLON)
                consome_token = False

            #caso 1: acao nao encontrada.. erro
            if(acao is None): return False

            tipo_acao, valor_acao = acao

            #caso 2-> SHIFT empilha proximo Ix e consome uma entrada
            if(tipo_acao == "shift"):
                stack.append(valor_acao)
                #EPSILON eh uma transicao interna, entao nao anda na entrada.
                if(consome_token): indice_token += 1
                continue

            """
                caso 3
                se E ::= E + T então:
                    cabeca = "E"
                    corpo = ["E", "+", "T"]
                    remove 3 estados porque o corpo tem 3 simbolos
            """
            if(tipo_acao == "reduce"):
                producao = valor_acao
                cabeca = producao.get_cabeca()
                corpo = producao.get_corpo()

                #remove da pilha os x estados do corpo da prod
                for i in corpo: stack.pop()
                estado_de_retorno = stack[-1]

                #pela cabeca da prod descobre o goto
                proximo_estado = goto_table.get(estado_de_retorno, {}).get(cabeca)

                #sem goto tem erro, nao reconhece a palavra
                if(proximo_estado is None): return False

                #empilha I encontrado no goto table
                stack.append(proximo_estado)
                continue

            #caso 4: encontrou accept/palavra foi reconhecida!
            if(tipo_acao == "accept"): return True

            return False
