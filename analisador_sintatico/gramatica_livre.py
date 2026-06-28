import producao,definicoes,prod_item_LR0


class GramaticaLivreDeContexto:
    
    def __init__(self, GLC_em_string, extender=False):
        self.GLC_em_string = GLC_em_string
        self.cabeca_inicial = None
        self.producoes = self.monta_GLC_obj(extender)
        
        #self.firsts = self.calcular_first()
        #self.follows = self.calcular_follow()
        self.firsts ={}
        self.follows ={}
        self.set_firsts()
        self.set_follows()
        
        if(not extender): self.GLC_exntedida = GramaticaLivreDeContexto(GLC_em_string, True)
        else: 
            #CHAMAR APENAS DENTRO DA GLC EXTENDIDA
            #gotos_LR0 formato eh (I_from, (simbolo, is_terminal), I_to) em dicionario {I_from: {simbolo..: I_to}}
            self.itens_LR0, self.gotos_LR0 = self.calcula_colecao_items_LR0()
            
            #tabela_SLR = action_table, goto_table
            self.tabela_SLR = self.calcula_tabela_SLR()
            pass

    def monta_GLC_obj(self, extender = False):
        cabecas = set()
        producoes = set()
        
        for l in self.GLC_em_string.split('\n'): 
            p = producao.Producao(l)
            if(self.cabeca_inicial == None): self.cabeca_inicial = p.cabeca
            cabecas.add(p.cabeca)
        
        if(extender):
            novo_inicial = self.cabeca_inicial
            while(novo_inicial in cabecas): novo_inicial += '\''
            cabecas = {novo_inicial} | cabecas
            producoes.add(producao.Producao(f"{novo_inicial} ::= {self.cabeca_inicial}", cabecas))
            self.cabeca_inicial = novo_inicial
        
        for l in self.GLC_em_string.split('\n'): 
            producoes.add(producao.Producao(l, cabecas))
        
        return producoes

    def get_gotos(self): return self.GLC_exntedida.gotos_LR0
    
    def get_itens_LR0(self): return self.GLC_exntedida.itens_LR0
            
    def get_cabecas(self): return [p.cabeca for p in self.producoes]
    
    def __str__(self): return '\n'.join([str(x) for x in self.producoes])
    
    """ def calcular_first(self):
        firsts = {k:set() for k in self.get_cabecas()}
        
        mudou = True
        while mudou == True:
            mudou = False
            for p in self.producoes:
                for s in p.corpo:
                    _break = False
                    if(not s.is_terminal):
                        firsts_aux = firsts[s.simbolo]
                        for faux in [x for x in firsts_aux if x != definicoes.EPISLON]:
                            if(faux not in firsts[p.cabeca]):
                                firsts[p.cabeca].add(faux)
                                mudou = True
                        if(definicoes.EPISLON not in firsts_aux): _break = True
                                
                    elif(s.is_terminal):
                        if(s.simbolo not in firsts[p.cabeca]):
                            firsts[p.cabeca].add(s.simbolo)
                            mudou = True
                        _break = True
                    
                    if _break: break
            
            for p in self.producoes:
                if(all([not s.is_terminal for s in p.corpo])):
                    if(all([definicoes.EPISLON in firsts[s.simbolo] for s in p.corpo])):
                        if(definicoes.EPISLON not in firsts[p.cabeca]):
                            firsts[p.cabeca].add(definicoes.EPISLON)
                            mudou = True
        
        return firsts
    
    def calcular_follow(self):
        follows = {k:set() for k in self.get_cabecas()}
        follows[self.cabeca_inicial].add('$')
        
        mudou = True
        while mudou == True:
            mudou = False
            for p in self.producoes:
                
                #caso 1
                #S -> ABCa joga first de B em A, tambem first de C em A se B.nullable
                for i,s in enumerate(p.corpo):
                    simbolo = s.simbolo
                    if(s.is_terminal): continue
                    for i2,s2 in enumerate(p.corpo[i:]):
                        simbolo2 = s2.simbolo
                        if(s2.is_terminal): break
                        if(simbolo == simbolo2): continue
                        first_aux = self.firsts[simbolo2]
                        for fa in [x for x in first_aux if x != definicoes.EPISLON]:
                            if(fa not in follows[simbolo]):
                                follows[simbolo].add(fa)
                                mudou=True
                        if(definicoes.EPISLON not in first_aux): break
                    
                #caso 2
                #S -> ABa joga a em follow B, tambem em follow A se B.nullable
                for i,s in enumerate(list(reversed(p.corpo))):
                    simbolo = s.simbolo
                    if(not s.is_terminal): continue
                    for i2,s2 in enumerate(list(reversed(p.corpo))[i:]):
                        simbolo2 = s2.simbolo
                        if(simbolo == simbolo2): continue
                        if(s2.is_terminal): continue
                        if(simbolo not in follows[simbolo2]):
                            follows[simbolo2].add(simbolo)
                            mudou=True
                        if(definicoes.EPISLON not in self.firsts[simbolo2]): break

                #caso 3
                # S -> ABC joga follow de S em C, em B se C.nullable...
                for i,s in enumerate(reversed(p.corpo)):
                    simbolo = s.simbolo
                    terminal = s.is_terminal
                    if(terminal): break
                    
                    follow_aux = follows[p.cabeca]
                    for fa in [x for x in follow_aux if definicoes.EPISLON != x]:
                        if(fa not in follows[simbolo]):
                            follows[simbolo].add(fa)
                            mudou=True
                    
                    if(definicoes.EPISLON not in self.firsts[simbolo]): break
        
        return follows """
    
    def get_firsts_by_head(self, head:str):
        productions = self.grammar.get_productions_by_head(head)
        firsts = []
        for p in productions:
            i = 0
            while True:
                first_symbol = p.body[i]
                if not first_symbol.isupper():
                    firsts.append(first_symbol)
                    break
                else:
                    firsts.extend(self.get_firsts_by_head(first_symbol))
                    if self.grammar.has_epsolon_productions_by_head(first_symbol) and i < (len(p.body) - 1):
                        firsts.remove(definicoes.EPISLON)
                        i += 1
                    else:
                        break
        firsts = list(set(firsts))
        return firsts
    
    def set_firsts(self):
        dict_prd: dict[str, list[Production]] = {}
        
        for p in self.grammar.productions:
            if not p.head in dict_prd:
                dict_prd[p.head] = []
                
            dict_prd[p.head].append(p)
            
        for head in dict_prd.keys():
            firsts = self.get_firsts_by_head(head)
            if not head in self.firsts:
                self.firsts[head] = set()
            self.firsts[head].update(firsts)
    
    def get_follows_by_head(self, symbol:str):
        all_productions = self.grammar.get_productions_with_symbol_on_body(symbol)
        productions = [x for x in all_productions if x.head != symbol]
        
        follows = []
        if symbol == self.grammar.start_symbol:
            follows.append('$')

        for p in productions:
            index_list = [i for i,x in enumerate(p.body) if x == symbol]
            for i in index_list:
                if i < (len(p.body) - 1): # αBβ
                    next_symbol = p.body[i+1]
                    if not next_symbol.isupper():
                        follows.append(next_symbol)
                    elif definicoes.EPISLON in self.firsts[next_symbol]:
                        #  Se A ::= αB (ou A ::= αBβ, onde ε ∈ FIRST(β)) ∈ P, 
                        #  então adicione FOLLOW(A) em FOLLOW(B)
                        follows.extend([x for x in self.firsts[next_symbol] if x != definicoes.EPISLON])
                        i2 = i+2 # simbolo depois do proximo
                        while True:
                            # ex de caso: B ::= ACd , d seria o next do next
                            if i2 > len(p.body) - 1:
                                follows_head = []
                                if not p.head in self.follows: 
                                    follows_head = self.get_follows_by_head(p.head)
                                else:
                                    follows_head = list(self.follows[p.head])
                                follows.extend(follows_head)
                                break
                            else:
                                next_symbol2 = p.body[i2]
                                if not next_symbol2.isupper():
                                    follows.append(next_symbol2)
                                    break;
                                elif definicoes.EPISLON in self.firsts[next_symbol2]:
                                    i2 += 1
                                    
                    # Se A ::= αBβ ∈ P e β != ε, 
                    # então adicione FIRST(β) em  FOLLOW(B)
                    else:
                        follows.extend(self.firsts[next_symbol])
                else: # αB
                    follows_head = []
                    if not p.head in self.follows: 
                        follows_head = self.get_follows_by_head(p.head)
                    else:
                        follows_head = list(self.follows[p.head])
                    follows.extend(follows_head)
            
        return follows
    
    def set_follows(self):
        symbols = set()
        for p in self.grammar.productions:
            symbols.add(p.head)
        
        for s in symbols:
            follows = self.get_follows_by_head(s)
            self.follows[s] = set(follows)
    
    def calcula_closure(self, lr0_item_prods):
        closure = [] + lr0_item_prods
        stack = [] + lr0_item_prods
        
        prods_novas = []
        while(len(stack) > 0):
            prod = stack.pop()
            if(prod.finalizo()): continue
            simbolo_atual = prod.get_simbolo_atual()
            if(simbolo_atual.is_terminal): continue
            
            prods = [p for p in self.producoes if p.cabeca == simbolo_atual.simbolo and p not in prods_novas]
            for p in prods:
                prods_novas.append(p)
                lr0 = prod_item_LR0.ProdItemLR0(p, 0)
                closure.append(lr0)
                stack.append(lr0)
        
        return closure
    
    def lr0_item_to_str(self, lr0_item): return "\n".join([str(x) for x in lr0_item])
    
    #CHAMAR APENAS DENTRO DA GLC EXTENDIDA
    def calcula_colecao_items_LR0(self):
        prod_inicial = [p for p in self.producoes if p.cabeca == self.cabeca_inicial][0]
        prod_inicial_closure = self.calcula_closure([prod_item_LR0.ProdItemLR0(prod_inicial, 0)])
        
        itens = [ prod_inicial_closure ]
        gotos = {}
        
        #['S->ABC \n A->zxc..'] = I0, itens/chaves apontam pra indice
        map_lr0_items = { self.lr0_item_to_str(k):0 for k in itens }
        
        mudou = True
        while mudou:
            mudou = False
            
            for i,item in enumerate(itens):
                prods_aux = [x for x in item if not x.finalizo()]
                simbolos = set([(x.get_simbolo_atual().simbolo, x.get_simbolo_atual().is_terminal) for x in prods_aux])
                
                for s in simbolos:
                    novo_item = []
                    for p in [x for x in prods_aux if x.get_simbolo_atual().simbolo == s[0]]:    
                        novo_item.append(p.avanca_simbolo_atual())
                    
                    novo_item = self.calcula_closure(novo_item)
                    if(self.lr0_item_to_str(novo_item) not in map_lr0_items):
                        id_novo_item = len(itens)
                        map_lr0_items[self.lr0_item_to_str(novo_item)] = id_novo_item
                        itens.append(novo_item)
                        mudou = True
                    else:
                        id_novo_item = map_lr0_items[self.lr0_item_to_str(novo_item)]
                        
                    #goto(I_from, Simbolo) = I_to
                    #i, s, id_novo_item = GOT(i, s) = id_novo_item
                    # s = (simbolo, is_terminal), ex (A, false), (a, true)...
                    id_item_antigo = i
                    simbolo = s
                    if(id_item_antigo not in gotos.keys()): gotos[id_item_antigo] = {}
                    gotos[id_item_antigo][simbolo] = id_novo_item
        
        return itens, gotos
    
    #CHAMAR APENAS DENTRO DA GLC EXTENDIDA
    def calcula_tabela_SLR(self):
        action_table = {}
        goto_table = {}
        
        gotos_com_terminais = [(k1, k2, self.gotos_LR0[k1][k2]) for k1 in self.gotos_LR0.keys() for k2 in self.gotos_LR0[k1] if k2[1]]
        gotos_com_nao_terminais = [(k1, k2, self.gotos_LR0[k1][k2]) for k1 in self.gotos_LR0.keys() for k2 in self.gotos_LR0[k1] if not k2[1]]
        
        
        """ 
            caso 1 SHIFT

            pra cada GOTO com terminal:

            GOTO(Ix, a) = Iy

            onde a eh terminal:

            ACTION[IX][a] = shift Iy 
        """
        
        for g in gotos_com_terminais: 
            if(g[0] not in action_table.keys()): action_table[g[0]] = {}
            action_table[g[0]][g[1][0]] = ('shift', g[2]) #f'shift I{g[2]}'
    
        """ 
            caso 2 GOTO de nao terminal

            pra cada GOTO com nao terminal:

            GOTO(Ix, A) = Iy

            onde A eh nao terminal:

            GOTO_TABLE[Ix][A] = Iy 
        """
        
        for g in gotos_com_nao_terminais: 
            if(g[0] not in goto_table.keys()): goto_table[g[0]] = {}
            goto_table[g[0]][g[1][0]] = g[2] #f'I{g[2]}'
            

        """ 
            case 3 REDUCE

            pra cada item finalizado:

            A ::= α ·

            se A nao eh o inicial estendido:

            pra cada x em FOLLOW(A):
                ACTION[Ix][x] = reduce A ::= α 
        """
        
        for item_id, i in enumerate(self.itens_LR0):
            prods_finalizadas = [p for p in i if p.finalizo() and p.get_cabeca() != self.cabeca_inicial]
            for pf in prods_finalizadas:
                cabeca = pf.get_cabeca()
                follows = self.follows[cabeca]
                for f in follows:
                    if(item_id not in action_table): action_table[item_id] = {}
                    action_table[item_id][f] = ('reduce', pf) #f"reduce {pf.__str__(False)}"

        """ 
            caso 4 ACCEPT
            Se: S' ::= S . então:
            ACTION[I]["$"] = accept 
        """
            
        prod_inicial= [p for i in self.itens_LR0 for p in i if p.get_cabeca() == self.cabeca_inicial][0]
        prod_inicial_finalizada = prod_inicial.get_prod_finalizada()
        itens_com_prod_inicial_finalizada = [i for i in self.itens_LR0 for p in i if str(prod_inicial_finalizada) == str(p)]

        for i in itens_com_prod_inicial_finalizada:
            if(i in self.itens_LR0):
                id_item = self.itens_LR0.index(i)
                if(id_item not in action_table): action_table[id_item] = {}
                action_table[id_item]['$'] = ('accept', None)
        
        return action_table, goto_table