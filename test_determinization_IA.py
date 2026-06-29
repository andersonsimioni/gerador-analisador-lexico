# ==========================================
# 1. MOCKS ATUALIZADOS (Com Inicial e Final)
# ==========================================
class MockTransicao:
    def __init__(self, origem, destino, simbolo):
        self.estado_origem = origem
        self.estado_destino = destino
        self.simbolo = simbolo

class MockEstado:
    def __init__(self, nome, inicial=False, final=False):
        self.nome = nome
        self.inicial = inicial
        self.final = final
        self.transicoes = {} 
        
    def add_transicao(self, destino, simbolo):
        t = MockTransicao(self, destino, simbolo)
        if simbolo not in self.transicoes:
            self.transicoes[simbolo] = []
        self.transicoes[simbolo].append(t)

class MockAutomato:
    def __init__(self, nome):
        self.nome = nome
        self.estados = {} 
        
    def add_estado(self, estado):
        self.estados[estado.nome] = estado

    def get_inicial(self):
        for e in self.estados.values():
            if e.inicial:
                return e
        return None

    # O epsilon_fecho silencioso (sem prints para não poluir a determinização)
    def epsilon_fecho(self, AFN):
        epsilon_fecho_dict = {}
        grafo_epsilon = {}
        for estado in AFN.estados.values():
            grafo_epsilon[estado] = []
        for estado in AFN.estados.values():
            for t in estado.transicoes.get("&", []):
                grafo_epsilon[t.estado_origem].append(t.estado_destino)

        for estado_origem in AFN.estados.values():
            visitados = [] 
            fila = [estado_origem]
            visitados.append(estado_origem)
            
            while len(fila) > 0:
                fonte = fila.pop(0)
                for vizinho in grafo_epsilon[fonte]:
                    if vizinho not in visitados:
                        visitados.append(vizinho)
                        fila.append(vizinho)            
            epsilon_fecho_dict[estado_origem] = visitados
            
        return epsilon_fecho_dict


# ==========================================
# 2. O SEU MÉTODO DE DETERMINIZAÇÃO (Com Prints Visuais)
# ==========================================
def determinization_com_prints(AFN):
    print("\n" + "="*70)
    print(f" INICIANDO DETERMINIZAÇÃO: AFN -> AFD ({AFN.nome})")
    print("="*70)
    
    # Instanciamos o Mock do AFD para o teste
    AFD = MockAutomato(f"AFD_de_{AFN.nome}")
    
    # 1. Epsilon Fecho
    print("\n[ETAPA 1] Calculando Epsilon-Fecho de todos os estados do AFN...")
    epsilon_fecho_local = AFD.epsilon_fecho(AFN)
    for k, v in epsilon_fecho_local.items():
        print(f"  -> Fecho({k.nome}) = {[e.nome for e in v]}")

    # 2. Alfabeto
    alfabeto = []
    for est in AFN.estados.values():
        for simbolo in est.transicoes.keys():
            if simbolo != "&" and simbolo not in alfabeto:
                alfabeto.append(simbolo)
    alfabeto.sort()
    print(f"\n[ETAPA 2] Alfabeto identificado: {alfabeto}")

    def gerar_nome(lista_estados):
        nomes = [e.nome for e in lista_estados]
        nomes.sort()
        return "-".join(nomes)

    # 3. Estado Inicial do AFD
    estado_inicial_afn = AFN.get_inicial()
    estados_do_novo_inicial = epsilon_fecho_local[estado_inicial_afn]
    
    nome_inicial = gerar_nome(estados_do_novo_inicial)
    is_final = any([e.final for e in estados_do_novo_inicial])
    
    novo_inicial = MockEstado(nome_inicial, inicial=True, final=is_final)
    AFD.add_estado(novo_inicial)
    composicao_estados = {nome_inicial: estados_do_novo_inicial}
    
    print(f"\n[ETAPA 3] Estado Inicial do AFD gerado: [{nome_inicial}] (Final? {is_final})")

    # 4. Busca em Largura (Subconjuntos)
    print("\n[ETAPA 4] Executando Busca em Largura (Construção de Subconjuntos):")
    fila = [nome_inicial]
    visitados = [nome_inicial]
    
    passo = 1
    while len(fila) > 0:
        print(f"\n  --- Passo {passo} | Fila Atual: {fila} ---")
        atual_nome = fila.pop(0)
        
        estados_afn_atuais = composicao_estados[atual_nome]
        estado_afd_atual = AFD.estados[atual_nome]
        
        print(f"  Analisando estado do AFD: [{atual_nome}]")
        
        for simbolo in alfabeto:
            alcançados_direto = []
            
            # Move(T, a)
            for nfa_state in estados_afn_atuais:
                transicoes_pelo_simbolo = nfa_state.transicoes.get(simbolo, [])
                for t in transicoes_pelo_simbolo:
                    if t.estado_destino not in alcançados_direto:
                        alcançados_direto.append(t.estado_destino)
            
            if len(alcançados_direto) == 0:
                print(f"    -> Lendo '{simbolo}': Beco sem saída (Vai para o vazio).")
                continue
                
            # Fecho-Epsilon do Move
            novo_conjunto_nfa = []
            for dest in alcançados_direto:
                for e in epsilon_fecho_local[dest]:
                    if e not in novo_conjunto_nfa:
                        novo_conjunto_nfa.append(e)
            
            novo_nome = gerar_nome(novo_conjunto_nfa)
            print(f"    -> Lendo '{simbolo}': Alcança {novo_nome}")
            
            if novo_nome not in AFD.estados:
                is_f = any([e.final for e in novo_conjunto_nfa])
                novo_estado_afd = MockEstado(novo_nome, inicial=False, final=is_f)
                AFD.add_estado(novo_estado_afd)
                composicao_estados[novo_nome] = novo_conjunto_nfa
                
                if novo_nome not in visitados:
                    print(f"       + [{novo_nome}] é um estado INÉDITO! Adicionado à fila.")
                    visitados.append(novo_nome)
                    fila.append(novo_nome)
            else:
                print(f"       x [{novo_nome}] já existe no AFD.")
            
            t_nova = MockTransicao(estado_afd_atual, AFD.estados[novo_nome], simbolo)
            estado_afd_atual.add_transicao(AFD.estados[novo_nome], simbolo)
            
        passo += 1

    print("\n" + "="*70)
    print(" RESUMO DO AFD GERADO")
    print("="*70)
    for estado in AFD.estados.values():
        tipo = "(Inicial)" if estado.inicial else "(Final)" if estado.final else ""
        if estado.inicial and estado.final: tipo = "(Inicial/Final)"
        
        print(f"Estado: [{estado.nome}] {tipo}")
        for simb, transicoes in estado.transicoes.items():
            for t in transicoes:
                print(f"  -- {simb} --> [{t.estado_destino.nome}]")

    return AFD


# ==========================================
# 3. EXECUÇÃO DO TESTE
# ==========================================
def executar_teste():
    afn = MockAutomato("Meu_AFN_Teste")
    
    # Criando os estados do cenário
    q0 = MockEstado("q0", inicial=True)
    q1 = MockEstado("q1")
    q2 = MockEstado("q2", final=True)
    
    # Transições do cenário
    q0.add_transicao(q0, "a")  # Loop no q0 com 'a'
    q0.add_transicao(q1, "&")  # Epsilon pro q1
    q1.add_transicao(q2, "b")  # q1 com 'b' vai pro q2 (Final)
    
    afn.add_estado(q0)
    afn.add_estado(q1)
    afn.add_estado(q2)
    
    # Executa a determinização e pega o AFD
    afd_resultante = determinization_com_prints(afn)
    
    # Asserts para garantir matematicamente que está certo
    assert "q0-q1" in afd_resultante.estados, "Erro: Estado inicial deveria ser q0-q1"
    assert "q2" in afd_resultante.estados, "Erro: Estado final q2 não foi criado"
    
    print("\n🚀 ASSERTIONS PASSARAM: O AFD foi gerado perfeitamente!\n")

if __name__ == "__main__":
    executar_teste()