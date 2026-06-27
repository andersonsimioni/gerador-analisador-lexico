import definicoes
import copy
import arvore_sintax.arvore_sintax, arvore_sintax.no_arvore_sintax, arvore_sintax.parte_regex
import estado, transicao

class Automato:
    
    def __init__(self, nome): 
        self.nome = nome
        self.estados = {}
        
    def add_estado(self, estado):
        self.estados[estado.nome] = estado
    
    def get_inicial(self):
        return [self.estados[x] for x in self.estados.keys() if self.estados[x].inicial][0]
    
    def get_TODAS_transicoes(self):
        return [t for e in self.estados.values() for k in e.transicoes.keys() for t in e.transicoes[k]]
    
    def reconhece(self, palavra):
        len_busca_largura = 0
        proximos = [(self.get_inicial(), palavra)]
        
        while(proximos is not None and len_busca_largura < definicoes.MAX_BUSCA_LARGURA_AFND):
            len_busca_largura += 1
            if any([True for x in proximos if x[0].final and x[1] == '']): return True
            proximos = [(estado, t[1]) for t in 
                              [(x[0].get_proximos_estados(x[1][0]), x[1][1:]) for x in proximos if len(x[1]) > 0] +
                              [(x[0].get_proximos_estados(definicoes.EPISLON), x[1]) for x in proximos]
                              for estado in t[0]]
        
        return any([True for x in proximos if x[0].final and x[1] == ''])

    def debug_print(self) -> None:
        print("\n" + "=" * 60)
        print(f"AUTOMATO: {self.nome}")
        print("=" * 60)
        
        estado_inicial = [x for x in self.estados.keys() if self.estados[x].inicial][0]

        print(f"\nEstado Inicial: {estado_inicial}")

        print("\nEstados:")
        for state in self.estados.values():
            flags = []

            if state.inicial:
                flags.append("INITIAL")

            if state.final:
                flags.append("FINAL")

            marker = f" [{' | '.join(flags)}]" if flags else ""
            print(f"  - {state.nome}{marker}")

        print("\nTransicoes:")
        transicoes = self.get_TODAS_transicoes()
        for transition in transicoes:
            symbol = "e" if transition.simbolo == definicoes.EPISLON else transition.simbolo
            print(f"  {transition.estado_origem.nome} -- {symbol} --> {transition.estado_destino.nome}")

        print("\nAlfabeto:")
        print(f"  {sorted(set([t.simbolo for t in transicoes if t.simbolo != definicoes.EPISLON]))}")

        print("\nEstados Finais:")
        print(f"  {sorted([x for x in self.estados.keys() if self.estados[x].final])}")

        print("=" * 60 + "\n")
        
        print(f'initial state: {estado_inicial}')
        
    def estado_esta_no_grupo(self, state, groups):
        for i, grupo in enumerate(groups):
            if state in grupo:
                return i
        return 'm' # estado morto
            
    def minimization(self) -> None:
        # ESTADOS INALCANCAVEIS
        # partimos do estado inicial e vamos vendo ate onde alcanca
        estado_inicial = [x for x in self.estados.keys() if self.estados[x].inicial][0]
        current_states = [estado_inicial] # comeca no estado inicial
        estados_alcancaveis = [estado_inicial]
        
        # para quando os current_states ficarem vazios
        while current_states:
            c = current_states[0]
            transicoes = self.get_TODAS_transicoes()
            transitions = [t.estado_destino.nome for t in transicoes if t.estado_origem.nome == c] # pega as transicoes desse estado
            current_states.extend([x for x in transitions 
                                   if not x in current_states 
                                   and not x in estados_alcancaveis
                                ]) # viram os novos current_states, pq eles sao alcancaveis
            current_states.remove(c) # esse state ja foi aberto, entao remove ele
            if not c in estados_alcancaveis: # se esse state nao foi ainda para os estados alcancaveis, add ele la pq ele eh alcancavel
                estados_alcancaveis.append(c)
            
            if len(estados_alcancaveis) == len(self.estados): # se o tamanho da lista de estados alcancaveis e da lista de estados eh igual, entao todos sao alcancaveis
                break
        
        for key in self.estados.keys():
            for simbolo in list(self.estados[key].transicoes.keys()):
                transicoes_estado = self.estados[key].transicoes[simbolo]
                transicoes_validas = [x for x in transicoes_estado if x.estado_destino.nome in estados_alcancaveis]
                self.estados[key].transicoes[simbolo] = transicoes_validas # remove as transicoes dos estados inalcancaveis
                
                if transicoes_validas == []:
                    del self.estados[key].transicoes[simbolo]
                    
        for key in list(self.estados.keys()):
            if key not in estados_alcancaveis: # remove o estado inalcancavel
                del self.estados[key]
                
        # ESTADOS MORTOS
        # partiremos dos estados finais e vemos ate onde alcanca
        current_states = [x for x in self.estados.keys() if self.estados[x].final] # agora o current_state sao os estados finais
        estados_nao_mortos = [x for x in self.estados.keys() if self.estados[x].final]
        
        # para quando os current_states ficarem vazios tbm
        while current_states:
            c = current_states[0]
            
            transicoes = self.get_TODAS_transicoes()
            # vamos pegando os estados de origem e nao os estados destino que nem na remocao dos estados alcancaveis
            transitions = [x.estado_origem.nome for x in 
                           transicoes if x.estado_destino.nome == c] 
            current_states.extend([x for x in transitions if not x in current_states and not x in estados_nao_mortos]) 
            current_states.remove(c)
            if not c in estados_nao_mortos:
                estados_nao_mortos.append(c)
            
            if len(estados_nao_mortos) == len(self.estados):
                break
            
        for key in self.estados.keys():
            for simbolo in list(self.estados[key].transicoes.keys()):
                transicoes_estado = self.estados[key].transicoes[simbolo]
                transicoes_validas = [
                    x for x in transicoes_estado 
                    if x.estado_origem.nome in estados_nao_mortos and x.estado_destino.nome in estados_nao_mortos
                ]
                self.estados[key].transicoes[simbolo] = transicoes_validas
                
                if transicoes_validas == []:
                    del self.estados[key].transicoes[simbolo]
                    
        for key in list(self.estados.keys()):
            if key not in estados_nao_mortos:
                del self.estados[key]
        
        alfabeto = set([t.simbolo for t in self.get_TODAS_transicoes() if t.simbolo != definicoes.EPISLON])
        # se nao tiver alfabeto ou tiver so um estado, ja eh minimo
        if not alfabeto or len(self.estados) <= 1:
            return
        
        # CLASSES DE EQUIVALENCIA
        # partimos da 1 separacao que eh os finais dos nao-finais
        grupos = [
            [x for x in self.estados.keys() if self.estados[x].final], # finais
            [x for x in self.estados.keys() if not self.estados[x].final] # nao finais
        ]
        
        # consideramos que o novo grupo eh diferente do grupo antigo pra entrar no while
        mesmo_grupo = False
        
        while not mesmo_grupo:
            for symbol in sorted(alfabeto):
                novos_grupos = {}
                transicoes = self.get_TODAS_transicoes()
                transitions = [x for x in transicoes if x.simbolo == symbol] # pegamos todas as transicoes por esse simbolo
                estados_que_tem_transicoes_por_este_simbolo = []
                for t in transitions:
                    grupo = self.estado_esta_no_grupo(t.estado_destino.nome, grupos) # pegamos o indice do grupo do estado, que esse estado alcanca
                    estados_que_tem_transicoes_por_este_simbolo.append(t.estado_origem.nome)
                    if grupo not in novos_grupos: # se esse indice nao estiver ainda nos novos_grupos, criamos um vazio
                        novos_grupos[grupo] = []
                    novos_grupos[grupo].append(t.estado_origem.nome) # adicionamos o estado-origem que alcanca esse grupo
                
                if len(estados_que_tem_transicoes_por_este_simbolo) != len(self.estados.keys()): # ha transicoes pro estado morto
                    estados_transicao_pro_morto = set(self.estados.keys()) - set(estados_que_tem_transicoes_por_este_simbolo)
                    novos_grupos['m'] = [x for x in estados_transicao_pro_morto]

                # esse novos_grupos nao sera o substituto de "grupos" ainda, pq precisamos separar os finais dos nao-finais
                novo_grupo_intersec = []
                for g in grupos:
                    for ng in novos_grupos.values():
                        intersec = set(g) & set(ng) # faz a interseccao, pra casos em que estados finais e nao-finais apontem pro mesmo grupo (mas nao podem ficar juntos)
                        if(list(intersec) != []):
                            novo_grupo_intersec.append(list(intersec))
                mesmo_grupo = novo_grupo_intersec == grupos # se for o mesmo grupo significa que chegamos no automato minimo
                grupos = novo_grupo_intersec # novo_grupo_intersec se torna o novo grupo e sera usado na proxima iteracao com o outro simbolo
        
        # atualizando o automato com os novos estados
        transicoes_antigas = self.get_TODAS_transicoes()
        new_states = {}
        new_states_dict = {} # estados antigos mapeados para os novos para facilitar a mudanca das transicoes
        new_initial_state = None
        for g in grupos:
            estado_agrupado = "".join(g) # novo estado agrupado
            for x in g:
                new_states_dict[x] = estado_agrupado # mapeando estado antigo para o estado novo
            is_final = any(x for x in [y for y in self.estados.keys() if self.estados[y].final] if x in g)
            
            if estado_inicial in g:
                new_initial_state = estado_agrupado
            
            new_states[estado_agrupado] = estado.Estado(estado_agrupado, estado_agrupado == new_initial_state, is_final)
            
        self.estados = new_states

        # substituindo as novas transicoes
        new_transitions = set() # pra nao ter transicoes repetidas
        
        for t in transicoes_antigas:
            if t.estado_origem.nome not in new_states_dict or t.estado_destino.nome not in new_states_dict:
                continue # significa que essa transicao nao existe mais
            new_source = new_states_dict[t.estado_origem.nome]
            new_target = new_states_dict[t.estado_destino.nome]
            new_transitions.add((new_source, t.simbolo, new_target))
        
        for t in new_transitions:
            self.estados[t[0]].add_transicao(transicao.Transicao(self.estados[t[0]], self.estados[t[2]], t[1]))


    def parse_regex(regex):    
        arvore = arvore_sintax.arvore_sintax.ArvoreSintax(f"({regex})#")
        raiz_first = arvore_sintax.no_arvore_sintax.NoArvoreSintax.get_ids_partes(arvore.raiz.first)
        id_hastag = arvore.get_id_hastag()
        estados = { raiz_first }
        estados_finais = set()
        estado_inicial = "-".join([str(x) for x in sorted(raiz_first)])
        transicoes = set() # (estado_from, simbolo, estado_to)
        
        stack = [raiz_first]
        while(len(stack)  > 0):
            _estado = stack.pop()
            nome_estado_from = "-".join([str(x) for x in sorted(_estado)])
            if (id_hastag in _estado): estados_finais.add(nome_estado_from)
            nos = arvore.get_nos(_estado)
            
            simbolos = {x[1].get_parte_regex_valor(): set() for x in nos}
            for n in nos:
                simbolos[n[1].get_parte_regex_valor()].add(n[1]) 
            
            for k in simbolos:
                if k == "#": continue
                follows = frozenset([f.get_parte_regex_id() for n in simbolos[k] for f in n.follow])
                if(follows not in stack and follows not in estados):
                    estados.add(follows)
                    stack.append(follows)
                nome_estado_to = "-".join([str(x) for x in sorted(follows)])
                transicoes.add((nome_estado_from, k, nome_estado_to))
                if (id_hastag in follows): estados_finais.add(nome_estado_to)
                
        AF = Automato('Aho')
    
        _estados = {s: estado.Estado(s, s == estado_inicial, s in estados_finais) for s in ["-".join([str(y) for y in sorted(x)]) for x in estados]}
        for t in transicoes:_estados[t[0]].add_transicao(transicao.Transicao(_estados[t[0]], _estados[t[2]], t[1]))
        for k in _estados.keys(): AF.add_estado(_estados[k])
        
        return AF
