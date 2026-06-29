# ==========================================
# 1. MOCKS (Simulando suas classes reais)
# ==========================================
class MockTransicao:
    def __init__(self, origem, destino, simbolo):
        self.estado_origem = origem
        self.estado_destino = destino
        self.simbolo = simbolo

class MockEstado:
    def __init__(self, nome):
        self.nome = nome
        self.transicoes = {} 
        
    def add_transicao(self, destino, simbolo):
        t = MockTransicao(self, destino, simbolo)
        if simbolo not in self.transicoes:
            self.transicoes[simbolo] = []
        self.transicoes[simbolo].append(t)

class MockAutomato:
    def __init__(self):
        self.estados = {} 
        
    def add_estado(self, estado):
        self.estados[estado.nome] = estado

    def epsilon_fecho_com_prints(self):
        print("\n" + "="*60)
        print(" INICIANDO ALGORITMO DE FECHO-EPSILON (CENÁRIO COMPLEXO)")
        print("="*60)
        
        epsilon_fecho_dict = {}
        grafo_epsilon = {}
        
        for estado in self.estados.values():
            grafo_epsilon[estado] = []
            
        print("\n[ETAPA 1] Mapeando grafo de transicoes epsilon (&):")
        for estado in self.estados.values():
            transicoes_vazias = estado.transicoes.get("&", []) 
            if not transicoes_vazias:
                print(f"  -> {estado.nome} possui 0 transicoes epsilon.")
            for t in transicoes_vazias:
                grafo_epsilon[t.estado_origem].append(t.estado_destino)
                print(f"  -> {t.estado_origem.nome} possui transicao epsilon para {t.estado_destino.nome}")

        print("\n[ETAPA 2] Executando Busca em Largura (BFS):")
        for estado_origem in self.estados.values():
            print(f"\n  >>> Analisando Fecho-Epsilon do estado: [{estado_origem.nome}]")
            
            visitados = [] 
            fila = []      
            
            fila.append(estado_origem)
            visitados.append(estado_origem)
            
            passo = 1
            while (len(fila) > 0):
                nomes_fila = [e.nome for e in fila]
                nomes_visitados = [e.nome for e in visitados]
                
                # Usando str(nomes_fila) para evitar o erro de formatação
                print(f"      Passo {passo} | Fila: {str(nomes_fila): <25} | Visitados: {nomes_visitados}")
                
                fonte = fila[0]
                fila.pop(0)
                
                nomes_vizinhos = [e.nome for e in grafo_epsilon[fonte]]
                if nomes_vizinhos:
                    print(f"      - Retirou '{fonte.nome}'. Checando vizinhos epsilon: {nomes_vizinhos}")
                else:
                    print(f"      - Retirou '{fonte.nome}'. Nenhum vizinho epsilon encontrado.")
                
                for vizinho in grafo_epsilon[fonte]:
                    if vizinho not in visitados:
                        print(f"        + Vizinho '{vizinho.nome}' INÉDITO! Adicionando à fila.")
                        visitados.append(vizinho)
                        fila.append(vizinho)
                    else:
                        print(f"        x Vizinho '{vizinho.nome}' JÁ VISITADO. Ignorando.")
                        
                passo += 1
            
            nomes_finais = [e.nome for e in visitados]
            print(f"  <<< RESULTADO: FECHO({estado_origem.nome}) = {nomes_finais}")
            
            epsilon_fecho_dict[estado_origem] = visitados
            
        print("\n" + "="*60)
        return epsilon_fecho_dict


# ==========================================
# 2. TESTE COM A ESTRUTURA SOLICITADA
# ==========================================
def executar_teste_visual():
    afn = MockAutomato()
    
    q1 = MockEstado("q1")
    q2 = MockEstado("q2")
    q3 = MockEstado("q3")
    q4 = MockEstado("q4")
    q5 = MockEstado("q5")
    
    # q2: Nenhum vizinho (Beco sem saída)
    # Não adicionamos transições
    
    # q5: 1 vizinho
    q5.add_transicao(q2, "&")
    
    # q3: 2 vizinhos
    q3.add_transicao(q2, "&")
    q3.add_transicao(q5, "&")
    
    # q1: 4 vizinhos
    q1.add_transicao(q2, "&")
    q1.add_transicao(q3, "&")
    q1.add_transicao(q4, "&")
    q1.add_transicao(q5, "&")
    
    # q4: 5 vizinhos (incluindo ele mesmo)
    q4.add_transicao(q1, "&")
    q4.add_transicao(q2, "&")
    q4.add_transicao(q3, "&")
    q4.add_transicao(q4, "&")
    q4.add_transicao(q5, "&")
    
    # Adicionando na ordem para a saída ficar organizada
    afn.add_estado(q1)
    afn.add_estado(q2)
    afn.add_estado(q3)
    afn.add_estado(q4)
    afn.add_estado(q5)
    
    afn.epsilon_fecho_com_prints()

if __name__ == "__main__":
    executar_teste_visual()