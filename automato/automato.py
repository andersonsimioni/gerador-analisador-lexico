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

    """ def debug_print(self) -> None:
        print("\n" + "=" * 60)
        print(f"AUTÔMATO: {self.name}")
        print("=" * 60)

        print(f"\nEstado Inicial: {self.initial_state}")

        print("\nEstados:")
        for state in self.states.values():
            flags = []

            if state.name == self.initial_state:
                flags.append("INITIAL")

            if state.is_final:
                flags.append("FINAL")

            marker = f" [{' | '.join(flags)}]" if flags else ""
            print(f"  • {state.name}{marker}")

        print("\nTransições:")
        for transition in self.transitions:
            symbol = "ε" if transition.is_epsilon else transition.symbol
            print(f"  {transition.source} -- {symbol} --> {transition.target}")

        print("\nAlfabeto:")
        print(f"  {sorted(self.alphabet())}")

        print("\nEstados Finais:")
        print(f"  {sorted(self.final_states())}")

        print("=" * 60 + "\n")
        
        print(f'initial state: {self.initial_state}')
        
    def estado_esta_no_grupo(self, state, groups):
        for i, grupo in enumerate(groups):
            if state in grupo:
                return i
        return 'm' # estado morto
            
    def minimization(self) -> None:
        # ESTADOS INALCANÇÁVEIS
        # partimos do estado inicial e vamos vendo até onde alcança
        current_states = [self.initial_state] # começa no estado inicial
        estados_alcancaveis = [self.initial_state]
        
        # para quando os current_states ficarem vazios
        while current_states:
            c = current_states[0]
            transitions = [x.target for x in self.transitions if x.source == c] # pega as transicoes desse estado
            current_states.extend([x for x in transitions 
                                   if not x in current_states 
                                   and not x in estados_alcancaveis
                                ]) # viram os novos current_states, pq eles sao alcançaveis
            current_states.remove(c) # esse state ja foi aberto, entao remove ele
            if not c in estados_alcancaveis: # se esse state nao foi ainda para os estados alcancaveis, add ele lá pq ele é alcançavel
                estados_alcancaveis.append(c)
            
            if len(estados_alcancaveis) == len(self.states): # se o tamanho da lista de estados alcancaveis e da lista de estados é igual, entao todos sao alcançaveis
                break
        
        self.transitions = [x for x in self.transitions if x.source in estados_alcancaveis] # remove as transições dos estados inalcançaveis
        for key in list(self.states.keys()):
            if key not in estados_alcancaveis: # remove o estado inalcançavel
                del self.states[key]
                
        # ESTADOS MORTOS
        # partiremos dos estados finais e vemos até onde alcança
        current_states = [x for x in self.final_states()] # agora o current_state sao os estados finais
        estados_nao_mortos = [x for x in self.final_states()]
        
        # para quando os current_states ficarem vazios tbm
        while current_states:
            c = current_states[0]
            
            # vamos pegando os estados de origem e nao os estados destino que nem na remoção dos estados alcançaveis
            transitions = [x.source for x in 
                           self.transitions if x.target == c] 
            current_states.extend([x for x in transitions if not x in current_states and not x in estados_nao_mortos]) 
            current_states.remove(c)
            if not c in estados_nao_mortos:
                estados_nao_mortos.append(c)
            
            if len(estados_nao_mortos) == len(self.states):
                break
            
        self.transitions = [x for x in self.transitions if x.source in estados_nao_mortos and x.target in estados_nao_mortos]
        for key in list(self.states.keys()):
            if key not in estados_nao_mortos:
                del self.states[key]
        
        # se nao tiver alfabeto ou tiver só um estado, ja eh minimo
        if not self.alphabet() or len(self.states) <= 1:
            return
        
        # CLASSES DE EQUIVALENCIA
        # partimos da 1° separação que é os finais dos não-finais
        grupos = [
            [x for x in self.final_states()], # finais
            [x for x in self.states.keys() if not x in self.final_states()] # nao finais
        ]
        
        # consideramos que o novo grupo é diferente do grupo antigo pra entrar no while
        mesmo_grupo = False
        
        while not mesmo_grupo:
            for symbol in sorted(self.alphabet()):
                novos_grupos = {}
                transitions = [x for x in self.transitions if x.symbol == symbol] # pegamos todas as transições por esse simbolo
                estados_que_tem_transicoes_por_este_simbolo = []
                for t in transitions:
                    grupo = self.estado_esta_no_grupo(t.target, grupos) # pegamos o índice do grupo do estado, que esse estado alcança
                    estados_que_tem_transicoes_por_este_simbolo.append(t.source)
                    if grupo not in novos_grupos: # se esse indice nao estiver ainda nos novos_grupos, criamos um vazio
                        novos_grupos[grupo] = []
                    novos_grupos[grupo].append(t.source) # adicionamos o estado-origem que alcança esse grupo
                
                if len(estados_que_tem_transicoes_por_este_simbolo) != len(self.states.keys()): # ha transicoes pro estado morto
                    estados_transicao_pro_morto = self.states.keys() - estados_que_tem_transicoes_por_este_simbolo
                    novos_grupos['m'] = [x for x in estados_transicao_pro_morto]

                # esse novos_grupos nao será o substituto de "grupos" ainda, pq precisamos separar os finais dos nao-finais
                novo_grupo_intersec = []
                for g in grupos:
                    for ng in novos_grupos.values():
                        intersec = set(g) & set(ng) # faz a intersecção, pra casos em que estados finais e nao-finais apontem pro mesmo grupo (mas nao podem ficar juntos)
                        if(list(intersec) != []):
                            novo_grupo_intersec.append(list(intersec))
                mesmo_grupo = novo_grupo_intersec == grupos # se for o mesmo grupo significa que chegamos no autômato mínimo
                grupos = novo_grupo_intersec # novo_grupo_intersec se torna o novo grupo e será usado na próxima iteração com o outro símbolo
        
        # atualizando o autômato com os novos estados
        new_states = {}
        new_states_dict = {} # estados antigos mapeados para os novos para facilitar a mudança das transições
        new_initial_state = None
        for g in grupos:
            estado_agrupado = "".join(g) # novo estado agrupado
            for x in g:
                new_states_dict[x] = estado_agrupado # mapeando estado antigo para o estado novo
            is_final = any(x for x in self.final_states() if x in g)
            
            if self.initial_state in g:
                new_initial_state = estado_agrupado
            
            new_states[estado_agrupado] = State(is_final=is_final, name=estado_agrupado)
            
        self.states = new_states
        self.initial_state = new_initial_state

        # substituindo as novas transições
        new_transitions = set() # pra nao ter transicoes repetidas
        
        for t in self.transitions:
            if t.source not in new_states_dict or t.target not in new_states_dict:
                continue # significa que essa transição nao existe mais
            new_source = new_states_dict[t.source]
            new_target = new_states_dict[t.target]
            new_transitions.add(Transition(new_source, t.symbol, new_target))
        
        self.transitions = list(new_transitions) """


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